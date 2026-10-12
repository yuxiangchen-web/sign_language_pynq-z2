"""AXI Simple DMA 字节缓冲事务；不定义 A 尚未交付的图像流协议。

寄存器偏移来自 AMD PG021；通道接口依据 PYNQ 2.7 官方驱动。
只支持同时启用 MM2S/S2MM 的普通 Simple DMA，不支持 SG/Micro。
"""

import math
import threading
import time

import numpy as np

from board.load_overlay import _integer

# AXI DMA 标准寄存器，不是项目 HLS 寄存器或实际 IP 基地址。
MM2S_CONTROL = 0x00
MM2S_STATUS = 0x04
S2MM_STATUS = 0x34
RESET = 0x04
HALTED = 0x01
IDLE = 0x02
ERROR_MASK = 0x70

# 复位无法确认时保留强引用，避免仍在运行的 DMA 访问已释放的物理内存。
_QUARANTINED = []


def dma_contract(description):
    if not description.get("type", "").startswith("xilinx.com:ip:axi_dma:"):
        raise ValueError("要求实际 AXI DMA 的 PYNQ ip_dict 描述")
    params = {k.lower(): v for k, v in description.get("parameters", {}).items()}
    required = ("c_include_sg", "c_include_mm2s", "c_include_s2mm", "c_sg_length_width",
                "c_m_axi_mm2s_data_width", "c_m_axi_s2mm_data_width", "c_addr_width")
    if any(key not in params for key in required):
        raise ValueError(f"HWH 缺少 DMA 配置，必须由 A 补齐: {required}")
    if _integer(params["c_include_sg"]) or _integer(params.get("c_micro_dma", 0)):
        raise ValueError("仅支持普通 Simple DMA，SG/Micro 需独立适配")
    if not all(_integer(params[k]) == 1 for k in ("c_include_mm2s", "c_include_s2mm")):
        raise ValueError("要求 MM2S 和 S2MM 两个通道")
    length_bits = _integer(params["c_sg_length_width"])
    address_bits = _integer(params["c_addr_width"])
    if not 8 <= length_bits <= 26 or not 32 <= address_bits <= 64:
        raise ValueError("DMA 长度或地址位宽超出支持范围")
    result = {"max_bytes": (1 << length_bits) - 1, "address_bits": address_bits}
    for direction in ("mm2s", "s2mm"):
        width = _integer(params[f"c_m_axi_{direction}_data_width"])
        if width < 8 or width % 8:
            raise ValueError("DMA memory-map 位宽必须为正整字节")
        result[f"{direction}_alignment"] = (
            1 if _integer(params.get(f"c_include_{direction}_dre", 0)) else width // 8)
    return result


class DmaTransfer:
    """READY -> ACTIVE -> READY；故障 -> FAULTED，必须重新构造驱动。

    input/output shape 和 dtype 由 A 的接口适配层或黄金测试向量提供。
    在事务中使用同一把锁，禁止两个线程复用同一对缓冲。
    start_ip 回调由 A 根据真实 register_map 提供，C 不猜 AP_CTRL 偏移。
    """

    def __init__(self, dma, input_shape, output_shape, input_dtype, output_dtype,
                 allocate_fn=None, clock=time.monotonic, sleep=time.sleep):
        self.dma = dma
        self.contract = dma_contract(dma.description)
        if dma.sendchannel is None or dma.recvchannel is None:
            raise ValueError("DMA 驱动缺少发送或接收通道")
        self._clock, self._sleep = clock, sleep
        self._lock = threading.Lock()
        self.state = "READY"
        self._safe_to_free = True
        self.last_record = None
        self.input_buffer = None
        self.output_buffer = None
        specs = []
        for shape, dtype in ((input_shape, input_dtype), (output_shape, output_dtype)):
            shape = tuple(shape)
            dtype = np.dtype(dtype)
            if (not shape or any(isinstance(n, bool) or not isinstance(n, int) or n <= 0 for n in shape)
                    or dtype.kind not in "ui" or not dtype.isnative):
                raise ValueError("DMA shape 必须全为正整数，dtype 必须是本机字节序整数")
            count = math.prod(shape) * dtype.itemsize
            if not 0 < count <= self.contract["max_bytes"]:
                raise ValueError(f"DMA 缓冲长度 {count} 超过硬件限制")
            specs.append((shape, dtype))
        if allocate_fn is None:
            from pynq import allocate
            allocate_fn = allocate
        try:
            self.input_buffer = allocate_fn(shape=specs[0][0], dtype=specs[0][1])
            self.output_buffer = allocate_fn(shape=specs[1][0], dtype=specs[1][1])
            self._validate_buffer(self.input_buffer, "mm2s")
            self._validate_buffer(self.output_buffer, "s2mm")
            lo1, lo2 = self._address(self.input_buffer), self._address(self.output_buffer)
            if max(lo1, lo2) < min(lo1 + self.input_buffer.nbytes, lo2 + self.output_buffer.nbytes):
                raise ValueError("发送与接收物理地址重叠")
        except Exception:
            self._free_buffers()
            raise

    @staticmethod
    def _address(buffer):
        return int(buffer.physical_address)

    def _validate_buffer(self, buffer, direction):
        for name in ("physical_address", "flush", "invalidate", "freebuffer"):
            if not hasattr(buffer, name):
                raise ValueError("必须使用 pynq.allocate 分配的物理连续缓冲")
        address = self._address(buffer)
        if address < 0 or address + buffer.nbytes > (1 << self.contract["address_bits"]):
            raise ValueError("缓冲物理地址超出 DMA 地址位宽")
        if address % self.contract[f"{direction}_alignment"]:
            raise ValueError(f"{direction} 地址不满足无 DRE 对齐要求")
        if not buffer.flags.c_contiguous:
            raise ValueError("DMA 缓冲不是 C-contiguous")

    def status(self):
        return {"mm2s": int(self.dma.mmio.read(MM2S_STATUS)),
                "s2mm": int(self.dma.mmio.read(S2MM_STATUS))}

    def _wait_complete(self, deadline, poll_s):
        while True:
            status = self.status()
            if any(value & ERROR_MASK for value in status.values()):
                raise RuntimeError(f"DMA error，状态={status}")
            if any(value & HALTED for value in status.values()):
                raise RuntimeError(f"DMA 意外停止，状态={status}")
            if all(value & IDLE for value in status.values()):
                return status
            if self._clock() >= deadline:
                raise TimeoutError(f"DMA 超时（检查 TLAST、IP 启动、字节数、时钟复位）：{status}")
            self._sleep(min(poll_s, max(0.0, deadline - self._clock())))

    def _reset_hardware(self, timeout_s=0.25, poll_s=0.001):
        self.dma.mmio.write(MM2S_CONTROL, RESET)
        deadline = self._clock() + timeout_s
        while True:
            control = int(self.dma.mmio.read(MM2S_CONTROL))
            status = self.status()
            if not control & RESET and all(value & HALTED for value in status.values()):
                self._safe_to_free = True
                return status
            if self._clock() >= deadline:
                raise TimeoutError(f"DMA 复位未确认，保留缓冲，不再复用: {status}")
            self._sleep(poll_s)

    def transfer(self, input_array, timeout_s=1.0, start_ip=None, poll_s=0.001):
        if not math.isfinite(timeout_s) or timeout_s <= 0 or not math.isfinite(poll_s) or poll_s <= 0:
            raise ValueError("DMA 超时和轮询间隔必须为有限正数")
        array = np.asarray(input_array)
        with self._lock:
            if self.state != "READY":
                raise RuntimeError(f"DMA 不可继续传输: {self.state}；请重载 Overlay 并重建驱动")
            if array.shape != self.input_buffer.shape or array.dtype != self.input_buffer.dtype:
                raise ValueError("输入 shape/dtype 与调用方提供的接口不符，不做隐式截断或类型转换")
            begin = self._clock()
            record = {"mode": "hardware_dma", "input_bytes": self.input_buffer.nbytes,
                      "output_bytes": self.output_buffer.nbytes, "passed": False}
            self.last_record = record
            # 接收缓冲先 flush，避免 CPU 的脏 cache line 随后覆盖 PL 写入。
            np.copyto(self.input_buffer, array)
            self.input_buffer.flush()
            self.output_buffer.fill(0)
            self.output_buffer.flush()
            initial = self.status()
            if any(value & (HALTED | ERROR_MASK) for value in initial.values()):
                self.state = "FAULTED"
                record["error"] = f"DMA 未启动或存在错误: {initial}"
                raise RuntimeError(f"DMA 未启动或存在错误: {initial}")
            for name, offset in (("sendchannel", "mm2s"), ("recvchannel", "s2mm")):
                channel = getattr(self.dma, name)
                # PYNQ 2.7 首次启动可处于 idle=0；仅其 first_transfer 标记允许。
                if not initial[offset] & IDLE and not getattr(channel, "_first_transfer", False):
                    record["error"] = f"已有其他事务占用 {name}"
                    raise RuntimeError(record["error"])
            self.state = "ACTIVE"
            self._safe_to_free = False
            try:
                # 先接收，再启动 IP，再发送；避免流水线因输出背压而挂死。
                self.dma.recvchannel.transfer(self.output_buffer)
                if start_ip:
                    start_ip()
                self.dma.sendchannel.transfer(self.input_buffer)
                record["status"] = self._wait_complete(begin + timeout_s, poll_s)
                # 两通道已确认 idle，调用原驱动完成其统计与缓存收尾。
                self.dma.sendchannel.wait()
                self.dma.recvchannel.wait()
                if (int(self.dma.sendchannel.transferred) != self.input_buffer.nbytes
                        or int(self.dma.recvchannel.transferred) != self.output_buffer.nbytes):
                    raise RuntimeError("DMA 实际字节数不符，检查提前 TLAST/TKEEP 和输出尺寸")
                self.output_buffer.invalidate()
                output = np.array(self.output_buffer, copy=True)
                self.state = "READY"
                self._safe_to_free = True
                record.update(passed=True, elapsed_s=self._clock() - begin)
                return output
            except Exception as exc:
                record.update(error=f"{type(exc).__name__}: {exc}", elapsed_s=self._clock() - begin)
                self.state = "FAULTED"
                try:
                    record["reset_status"] = self._reset_hardware()
                    record["reset_confirmed"] = True
                except Exception as reset_exc:
                    record.update(reset_confirmed=False, reset_error=str(reset_exc))
                    if not any(item is self for item in _QUARANTINED):
                        _QUARANTINED.append(self)
                raise

    def retry_reset(self, timeout_s=0.25):
        """复位成功只允许安全释放；仍须重建驱动和复位上游 HLS。"""
        if not math.isfinite(timeout_s) or timeout_s <= 0:
            raise ValueError("复位超时必须为有限正数")
        with self._lock:
            if self.state != "FAULTED":
                raise RuntimeError("仅故障状态可重试复位")
            result = self._reset_hardware(timeout_s)
            _QUARANTINED[:] = [item for item in _QUARANTINED if item is not self]
            return result

    def _free_buffers(self):
        for name in ("output_buffer", "input_buffer"):
            buffer = getattr(self, name)
            if buffer is not None:
                buffer.freebuffer()
                setattr(self, name, None)

    def close(self):
        with self._lock:
            if self.state == "CLOSED":
                return
            if not self._safe_to_free:
                raise RuntimeError("DMA 仍可能运行，禁止释放物理缓冲；先确认复位")
            self._free_buffers()
            self.state = "CLOSED"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None or self._safe_to_free:
            self.close()
