"""DMA 软件模型：独立 CPU/设备缓存、延迟完成、缺 TLAST、错误和复位。

这里未调用真实 DMA/IP；1000 次模型事务不等于 1000 帧上板验收。
"""

import copy

import numpy as np
import pytest

from board.dma_board_test import run_dma_test
from board.dma_transfer import (DmaTransfer, ERROR_MASK, HALTED, IDLE, MM2S_CONTROL,
                                MM2S_STATUS, RESET, S2MM_STATUS, _QUARANTINED,
                                dma_contract)


def fake_description():
    return {"type": "xilinx.com:ip:axi_dma:7.1", "parameters": {
        "c_include_sg": "0", "c_micro_dma": "0", "c_include_mm2s": "1",
        "c_include_s2mm": "1", "c_sg_length_width": "14", "c_addr_width": "32",
        "c_m_axi_mm2s_data_width": "32", "c_m_axi_s2mm_data_width": "32",
        "c_include_mm2s_dre": "0", "c_include_s2mm_dre": "0"}}


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


class FakeBuffer(np.ndarray):
    def __new__(cls, shape, dtype, address, events):
        obj = np.zeros(shape, dtype).view(cls)
        obj.physical_address = address
        obj.device_data = np.zeros(shape, dtype)
        obj.events = events
        obj.freed = False
        return obj

    def flush(self):
        self.events.append(("flush", self.physical_address))
        np.copyto(self.device_data, np.asarray(self))

    def invalidate(self):
        self.events.append(("invalidate", self.physical_address))
        np.copyto(self, self.device_data)

    def freebuffer(self):
        assert not self.freed
        self.freed = True
        self.events.append(("free", self.physical_address))


class FakeChannel:
    def __init__(self, dma, name):
        self.dma, self.name = dma, name
        self.buffer = None
        self.transferred = 0
        self._first_transfer = True

    def transfer(self, buffer):
        self.dma.events.append(("transfer", self.name))
        self.buffer = buffer
        self.transferred = 0
        self._first_transfer = False
        offset = MM2S_STATUS if self.name == "send" else S2MM_STATUS
        self.dma.mmio.registers[offset] = 0
        if self.name == "send":
            assert self.dma.recvchannel.buffer is not None
            self.dma.started = True
            self.dma.reads = 0

    def wait(self):
        self.dma.events.append(("wait", self.name))
        assert not self.dma.error
        assert all(self.dma.mmio.registers[o] & IDLE for o in (MM2S_STATUS, S2MM_STATUS))
        self.transferred = self.buffer.nbytes - (self.dma.short_bytes if self.name == "recv" else 0)


class FakeMMIO:
    def __init__(self, dma):
        self.dma = dma
        self.registers = {MM2S_CONTROL: 1, MM2S_STATUS: IDLE, S2MM_STATUS: IDLE}

    def read(self, offset):
        dma = self.dma
        if dma.started and offset in (MM2S_STATUS, S2MM_STATUS):
            dma.reads += 1
            if dma.error:
                self.registers[MM2S_STATUS] = dma.error
                self.registers[S2MM_STATUS] = dma.error
            elif dma.complete and dma.reads >= 6:
                source = dma.sendchannel.buffer.device_data
                # 真正按发送内容计算结果，避免返回固定测试答案。
                dma.recvchannel.buffer.device_data[:] = 255 - source
                self.registers[MM2S_STATUS] = IDLE
                self.registers[S2MM_STATUS] = IDLE
                dma.started = False
        return self.registers[offset]

    def write(self, offset, value):
        self.dma.events.append(("write", offset, value))
        self.registers[offset] = value
        if offset == MM2S_CONTROL and value & RESET and not self.dma.reset_stuck:
            self.dma.started = False
            self.registers[MM2S_CONTROL] = 0
            self.registers[MM2S_STATUS] = HALTED
            self.registers[S2MM_STATUS] = HALTED


class FakeDMA:
    def __init__(self):
        self.description = fake_description()
        self.events = []
        self.started = False
        self.complete = True
        self.error = 0
        self.reset_stuck = False
        self.short_bytes = 0
        self.reads = 0
        self.mmio = FakeMMIO(self)
        self.sendchannel = FakeChannel(self, "send")
        self.recvchannel = FakeChannel(self, "recv")
        self.buffers = []

    def allocate(self, shape, dtype):
        buffer = FakeBuffer(shape, dtype, 0x1000 * (len(self.buffers) + 1), self.events)
        self.buffers.append(buffer)
        return buffer


def make_transfer(dma=None, shape=(8,)):
    dma = dma or FakeDMA()
    clock = FakeClock()
    transfer = DmaTransfer(dma, shape, shape, "uint8", "uint8", dma.allocate, clock, clock.sleep)
    return dma, transfer, clock


def test_transaction_cache_order_and_independent_result():
    dma, transfer, _ = make_transfer()
    data = np.array([0, 1, 127, 128, 254, 255, 42, 99], np.uint8)
    output = transfer.transfer(data, start_ip=lambda: dma.events.append(("start_ip",)))
    np.testing.assert_array_equal(output, 255 - data)
    assert type(output) is np.ndarray and not np.shares_memory(output, transfer.output_buffer)
    assert dma.events[:5] == [("flush", 0x1000), ("flush", 0x2000),
                              ("transfer", "recv"), ("start_ip",), ("transfer", "send")]
    assert dma.events.index(("wait", "recv")) < dma.events.index(("invalidate", 0x2000))
    assert transfer.state == "READY" and transfer.last_record["passed"]
    transfer.close()
    assert all(buffer.freed for buffer in dma.buffers)
    transfer.close()


def test_1000_continuous_transactions():
    dma, transfer, _ = make_transfer()
    inputs = [np.arange(8, dtype=np.uint8), np.arange(255, 247, -1, dtype=np.uint8)]
    result = run_dma_test(transfer, inputs, [255 - array for array in inputs], frames=1000)
    assert result["completed_frames"] == 1000 and result["passed"]
    assert len([e for e in dma.events if e == ("transfer", "send")]) == 1000
    transfer.close()


@pytest.mark.parametrize("timeout,poll", [(0, .001), (-1, .001), (float("nan"), .001),
                                          (float("inf"), .001), (1, 0), (1, float("inf"))])
def test_bad_deadline(timeout, poll):
    _, transfer, _ = make_transfer()
    with pytest.raises(ValueError):
        transfer.transfer(np.zeros(8, np.uint8), timeout, poll_s=poll)
    assert transfer.state == "READY"
    transfer.close()


@pytest.mark.parametrize("data", [np.zeros(7, np.uint8), np.zeros(8, np.uint16),
                                  np.zeros((2, 4), np.uint8)])
def test_shape_dtype_rejected_before_dma(data):
    dma, transfer, _ = make_transfer()
    with pytest.raises(ValueError):
        transfer.transfer(data)
    assert dma.events == []
    transfer.close()


def test_noncontiguous_input_copied_without_changing_format():
    _, transfer, _ = make_transfer()
    data = np.arange(16, dtype=np.uint8)[::2]
    assert not data.flags.c_contiguous
    np.testing.assert_array_equal(transfer.transfer(data), 255 - data)
    transfer.close()


def test_missing_tlast_timeout_reset_and_no_faulted_reuse():
    dma, transfer, clock = make_transfer()
    dma.complete = False
    with pytest.raises(TimeoutError, match="TLAST"):
        transfer.transfer(np.arange(8, dtype=np.uint8), timeout_s=.01)
    assert .01 <= clock.now < .012
    assert transfer.state == "FAULTED" and transfer.last_record["reset_confirmed"]
    assert dma.mmio.registers[MM2S_STATUS] == dma.mmio.registers[S2MM_STATUS] == HALTED
    assert not any(buffer.freed for buffer in dma.buffers)
    with pytest.raises(RuntimeError, match="FAULTED"):
        transfer.transfer(np.arange(8, dtype=np.uint8))
    transfer.close()
    assert all(buffer.freed for buffer in dma.buffers)


@pytest.mark.parametrize("error", [0x10, 0x20, 0x40])
def test_dma_error_reset(error):
    dma, transfer, _ = make_transfer()
    dma.error = error
    with pytest.raises(RuntimeError, match="DMA error"):
        transfer.transfer(np.arange(8, dtype=np.uint8))
    assert transfer.last_record["reset_confirmed"]
    assert not transfer.last_record["passed"]
    transfer.close()


def test_failed_reset_quarantines_and_retry_allows_release():
    dma, transfer, clock = make_transfer()
    dma.complete = False
    dma.reset_stuck = True
    with pytest.raises(TimeoutError):
        transfer.transfer(np.arange(8, dtype=np.uint8), timeout_s=.01)
    assert transfer.last_record["reset_confirmed"] is False and transfer in _QUARANTINED
    assert .26 <= clock.now < .263
    with pytest.raises(RuntimeError, match="禁止释放"):
        transfer.close()
    assert not any(buffer.freed for buffer in dma.buffers)
    dma.reset_stuck = False
    transfer.retry_reset()
    assert transfer not in _QUARANTINED
    transfer.close()


def test_short_tlast_rejected_even_if_both_channels_idle():
    dma, transfer, _ = make_transfer()
    dma.short_bytes = 1
    with pytest.raises(RuntimeError, match="实际字节数"):
        transfer.transfer(np.arange(8, dtype=np.uint8))
    assert transfer.state == "FAULTED"
    transfer.close()


def test_start_callback_failure_resets_armed_receiver():
    dma, transfer, _ = make_transfer()

    def fail():
        raise RuntimeError("HLS not ready")
    with pytest.raises(RuntimeError, match="HLS not ready"):
        transfer.transfer(np.arange(8, dtype=np.uint8), start_ip=fail)
    assert ("transfer", "recv") in dma.events and ("transfer", "send") not in dma.events
    assert transfer.last_record["reset_confirmed"]
    transfer.close()


@pytest.mark.parametrize("key,value", [("c_include_sg", "1"), ("c_micro_dma", "1"),
                                       ("c_include_mm2s", "0"), ("c_include_s2mm", "0"),
                                       ("c_sg_length_width", "0"), ("c_addr_width", "8"),
                                       ("c_m_axi_mm2s_data_width", "7")])
def test_unsupported_configuration(key, value):
    description = fake_description()
    description["parameters"][key] = value
    with pytest.raises(ValueError):
        dma_contract(description)


def test_missing_config_and_uppercase_parameter_names():
    description = fake_description()
    del description["parameters"]["c_sg_length_width"]
    with pytest.raises(ValueError, match="缺少"):
        dma_contract(description)
    description = fake_description()
    description["parameters"] = {k.upper(): v for k, v in description["parameters"].items()}
    assert dma_contract(description)["max_bytes"] == 16383


@pytest.mark.parametrize("shape", [(), (0,), (-1,), (True,), (1.5,), (16384,)])
def test_invalid_shapes_or_length(shape):
    dma = FakeDMA()
    with pytest.raises(ValueError):
        DmaTransfer(dma, shape, (8,), "uint8", "uint8", dma.allocate)
    assert not dma.buffers


def test_allocation_failure_frees_first_buffer():
    dma = FakeDMA()

    def allocate(shape, dtype):
        if dma.buffers:
            raise MemoryError("CMA exhausted")
        return dma.allocate(shape, dtype)
    with pytest.raises(MemoryError):
        DmaTransfer(dma, (8,), (8,), "uint8", "uint8", allocate)
    assert dma.buffers[0].freed


def test_misaligned_address_frees_both_buffers():
    dma = FakeDMA()

    def allocate(shape, dtype):
        buffer = dma.allocate(shape, dtype)
        buffer.physical_address += 1
        return buffer
    with pytest.raises(ValueError, match="对齐"):
        DmaTransfer(dma, (8,), (8,), "uint8", "uint8", allocate)
    assert len(dma.buffers) == 2 and all(b.freed for b in dma.buffers)


def test_wrong_golden_output_is_failure_not_silently_accepted():
    _, transfer, _ = make_transfer()
    inputs = [np.arange(8, dtype=np.uint8)]
    result = run_dma_test(transfer, inputs, [inputs[0]], frames=100)
    assert result["passed"] is False and result["completed_frames"] == 1
    assert result["frames"][0]["different_elements"] == 8
    transfer.close()


def test_initial_halted_or_busy_channel_rejected():
    dma, transfer, _ = make_transfer()
    dma.mmio.registers[MM2S_STATUS] = HALTED
    with pytest.raises(RuntimeError, match="未启动"):
        transfer.transfer(np.zeros(8, np.uint8))
    assert transfer.state == "FAULTED"
    transfer.close()
    dma, transfer, _ = make_transfer()
    dma.mmio.registers[MM2S_STATUS] = 0
    dma.sendchannel._first_transfer = False
    with pytest.raises(RuntimeError, match="占用"):
        transfer.transfer(np.zeros(8, np.uint8))
    assert not any(e[0] == "transfer" for e in dma.events)
    transfer.close()


def test_ready_driver_initial_idle_zero_allowed_on_first_transaction():
    dma, transfer, _ = make_transfer()
    dma.mmio.registers[MM2S_STATUS] = dma.mmio.registers[S2MM_STATUS] = 0
    data = np.arange(8, dtype=np.uint8)
    np.testing.assert_array_equal(transfer.transfer(data), 255 - data)
    transfer.close()


def test_physical_overlap_and_address_overflow_rejected():
    for bad_address in (0x1000, (1 << 32) - 4):
        dma = FakeDMA()

        def allocate(shape, dtype):
            buffer = dma.allocate(shape, dtype)
            if len(dma.buffers) == 2:
                buffer.physical_address = bad_address
            return buffer
        with pytest.raises(ValueError):
            DmaTransfer(dma, (8,), (8,), "uint8", "uint8", allocate)
        assert all(buffer.freed for buffer in dma.buffers)
