"""真实 HWH 检查 + 明确注入的寄存器/Overlay 替身，不算上板测试。"""

from pathlib import Path

import pytest

from board.load_overlay import DEFAULT_BITSTREAM, OverlaySession, inspect_overlay
from board.overlay_register_test import gpio_contract, test_gpio_registers


class FakeGpio:
    def __init__(self):
        self.registers = {0: 5, 4: 15}
        self.writes = []
        self.fail_on_pattern = None

    def read(self, offset):
        value = self.registers[offset]
        return value ^ 1 if offset == 0 and value == self.fail_on_pattern else value

    def write(self, offset, value):
        self.writes.append((offset, value))
        self.registers[offset] = value


class FakeOverlay:
    def __init__(self, bitstream, download):
        self.loaded = download
        self.downloads = 1
        self.ip_dict = {"axi_gpio_0": {"phys_addr": 0x41200000, "addr_range": 0x10000}}
        self.axi_gpio_0 = FakeGpio()

    def is_loaded(self):
        return self.loaded

    def download(self):
        self.downloads += 1
        self.loaded = True


@pytest.mark.parametrize("folder,name", [("led_test", "led_test"),
                                         ("led_test_2026_1", "led_test_2026_1")])
def test_real_hwh_contract(folder, name):
    bit = DEFAULT_BITSTREAM.parents[1] / folder / (name + ".bit")
    metadata = inspect_overlay(bit)
    assert metadata["mode"] == "offline_metadata"
    assert metadata["dma_ips"] == []
    contract = gpio_contract(metadata)
    assert contract == {"ip": "axi_gpio_0", "base_address": 0x41200000,
                        "width": 4, "data_offset": 0, "tri_offset": 4}
    gpio = metadata["ips"]["axi_gpio_0"]
    assert gpio["clocks"][0]["frequency_hz"] == 100000000
    assert {r["polarity"] for r in gpio["resets"]} == {"ACTIVE_LOW"}


def test_fake_overlay_load_reload_and_missing_dma():
    session = OverlaySession(overlay_factory=FakeOverlay)
    before = session.overlay
    session.reload()
    assert session.overlay is not before and session.overlay.loaded
    assert session.overlay.axi_gpio_0 is not before.axi_gpio_0
    with pytest.raises(ValueError):
        session.get_ip("unknown")
    with pytest.raises(ValueError, match="未提供 AXI DMA"):
        session.get_dma("axi_dma_0")


@pytest.mark.parametrize("loaded,address", [(False, 0x41200000), (True, 0x40000000)])
def test_loader_rejects_mismatch(loaded, address):
    def factory(bit, download):
        overlay = FakeOverlay(bit, download)
        overlay.loaded = loaded
        overlay.ip_dict["axi_gpio_0"]["phys_addr"] = address
        return overlay
    with pytest.raises(RuntimeError):
        OverlaySession(overlay_factory=factory)


def test_gpio_patterns_and_restore():
    session = OverlaySession(overlay_factory=FakeOverlay)
    result = test_gpio_registers(session)
    assert result["passed"]
    assert [r["written"] for r in result["patterns"]] == [0, 1, 2, 4, 8, 15, 0]
    assert session.overlay.axi_gpio_0.registers == {0: 5, 4: 15}


def test_gpio_restore_even_on_readback_failure():
    session = OverlaySession(overlay_factory=FakeOverlay)
    session.overlay.axi_gpio_0.fail_on_pattern = 2
    with pytest.raises(AssertionError, match="读回不一致"):
        test_gpio_registers(session)
    assert session.overlay.axi_gpio_0.registers == {0: 5, 4: 15}


def test_missing_and_invalid_metadata(tmp_path):
    bit = tmp_path / "bad.bit"
    with pytest.raises(FileNotFoundError):
        inspect_overlay(bit)
    bit.write_bytes(b"test fixture, not a bitstream")
    with pytest.raises(FileNotFoundError):
        inspect_overlay(bit)
    bit.with_suffix(".hwh").write_text("<SYSTEM/>", encoding="utf-8")
    with pytest.raises(ValueError, match="不包含 IP"):
        inspect_overlay(bit)


def test_working_directory_independent(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert gpio_contract(inspect_overlay(DEFAULT_BITSTREAM))["width"] == 4
