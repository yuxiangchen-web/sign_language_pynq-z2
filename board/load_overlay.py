"""依据实际 HWH 发现 IP 和寄存器；离线检查无需安装 PYNQ。"""

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

from board.run_log import write_json

DEFAULT_BITSTREAM = (Path(__file__).resolve().parent / "overlays" /
                     "led_test_2026_1" / "led_test_2026_1.bit")


def _integer(value):
    value = str(value)
    return int(value, 16 if value.lower().startswith("0x") else 10)


def inspect_overlay(bitstream):
    """读取随 bitstream 交付的同名 HWH；不根据目录名伪造硬件能力。"""
    bit = Path(bitstream).resolve()
    hwh = bit.with_suffix(".hwh")
    for path in (bit, hwh):
        if not path.is_file() or path.stat().st_size == 0:
            raise FileNotFoundError(f"Overlay 文件不存在或为空: {path}")
    root = ET.parse(hwh).getroot()
    ranges = {}
    for node in root.findall(".//MEMRANGE"):
        instance = node.get("INSTANCE")
        base, high = _integer(node.get("BASEVALUE")), _integer(node.get("HIGHVALUE"))
        if high < base:
            raise ValueError(f"地址范围倒置: {instance}")
        if instance in ranges and ranges[instance] != (base, high):
            raise ValueError(f"多地址范围需由 A 明确选择: {instance}")
        ranges[instance] = (base, high)
    ips = {}
    for module in root.findall(".//MODULES/MODULE"):
        name = module.get("FULLNAME", "").strip("/") or module.get("INSTANCE")
        instance = module.get("INSTANCE")
        params = {p.get("NAME"): p.get("VALUE")
                  for p in module.findall("./PARAMETERS/PARAMETER")}
        registers = {}
        for register in module.findall("./ADDRESSBLOCKS/ADDRESSBLOCK/REGISTERS/REGISTER"):
            props = {p.get("NAME"): p.get("VALUE") for p in register.findall("./PROPERTY")}
            if props.get("IS_ENABLED", "true").lower() != "true":
                continue
            fields = {}
            for field in register.findall("./FIELDS/FIELD"):
                fp = {p.get("NAME"): p.get("VALUE") for p in field.findall("./PROPERTY")}
                fields[field.get("NAME")] = {
                    "bit_offset": _integer(fp.get("BIT_OFFSET", 0)),
                    "bit_width": _integer(fp.get("BIT_WIDTH", 0)),
                }
            if "ADDRESS_OFFSET" in props:
                registers[register.get("NAME")] = {
                    "offset": _integer(props["ADDRESS_OFFSET"]),
                    "access": props.get("ACCESS"), "fields": fields}
        clocks = [{"port": p.get("NAME"), "frequency_hz": _integer(p.get("CLKFREQUENCY"))}
                  for p in module.findall("./PORTS/PORT") if p.get("CLKFREQUENCY")]
        resets = [{"port": p.get("NAME"), "polarity": p.get("POLARITY")}
                  for p in module.findall("./PORTS/PORT") if p.get("SIGIS") == "rst"]
        item = {"vlnv": module.get("VLNV", ""), "parameters": params,
                "registers": registers, "clocks": clocks, "resets": resets}
        if instance in ranges:
            item["base_address"], high = ranges[instance]
            item["address_range"] = high - item["base_address"] + 1
        ips[name] = item
    if not ips:
        raise ValueError("HWH 不包含 IP 元数据")
    return {"mode": "offline_metadata", "bitstream": str(bit), "hwh": str(hwh),
            "bitstream_sha256": hashlib.sha256(bit.read_bytes()).hexdigest(),
            "hwh_sha256": hashlib.sha256(hwh.read_bytes()).hexdigest(), "ips": ips,
            "dma_ips": [name for name, ip in ips.items()
                        if ip["vlnv"].startswith("xilinx.com:ip:axi_dma:")]}


class OverlaySession:
    """加载成功后核对 PYNQ 解析的 IP 地址；测试可显式注入软件替身。"""

    def __init__(self, bitstream=DEFAULT_BITSTREAM, overlay_factory=None):
        self.metadata = inspect_overlay(bitstream)
        if overlay_factory is None:
            try:
                from pynq import Overlay
            except ImportError as exc:
                raise RuntimeError("硬件加载需要在 PYNQ 板卡上运行；离线使用 --inspect") from exc
            overlay_factory = Overlay
        self._overlay_factory = overlay_factory
        self.overlay = overlay_factory(self.metadata["bitstream"], download=True)
        if not self.overlay.is_loaded():
            raise RuntimeError("PYNQ 未确认 Overlay 已加载")
        for name, ip in self.metadata["ips"].items():
            if "base_address" not in ip:
                continue
            actual = self.overlay.ip_dict.get(name)
            if actual is None:
                raise RuntimeError(f"PYNQ 缺少 HWH 中的 IP: {name}")
            if (int(actual["phys_addr"]) != ip["base_address"]
                    or int(actual["addr_range"]) != ip["address_range"]):
                raise RuntimeError(f"PYNQ 与 HWH 地址不一致: {name}")

    def get_ip(self, name):
        if name not in self.metadata["ips"] or name not in self.overlay.ip_dict:
            raise ValueError(f"Overlay 未提供 IP: {name}")
        node = self.overlay
        for part in name.split("/"):
            node = getattr(node, part)
        return node

    def get_dma(self, name):
        if name not in self.metadata["dma_ips"]:
            raise ValueError(f"HWH 未提供 AXI DMA: {name}；当前 DMA: {self.metadata['dma_ips']}")
        return self.get_ip(name)

    def reload(self):
        """重载整个 PL 并重建 IP 驱动；调用方须先结束/复位旧 DMA 事务。"""
        refreshed = OverlaySession(self.metadata["bitstream"], self._overlay_factory)
        self.metadata = refreshed.metadata
        self.overlay = refreshed.overlay


def main():
    ap = argparse.ArgumentParser(description="检查或加载真实 PYNQ Overlay")
    ap.add_argument("--bit", default=str(DEFAULT_BITSTREAM))
    ap.add_argument("--inspect", action="store_true", help="只读 bit/hwh，不访问硬件")
    ap.add_argument("--reload", action="store_true")
    ap.add_argument("--log", default="board/logs/overlay.json")
    args = ap.parse_args()
    mode = "offline_metadata" if args.inspect else "hardware_overlay"
    try:
        if args.inspect:
            if args.reload:
                raise ValueError("--reload 需要硬件模式")
            result = inspect_overlay(args.bit)
        else:
            session = OverlaySession(args.bit)
            if args.reload:
                session.reload()
            result = {**session.metadata, "mode": mode, "loaded": True}
        result["passed"] = True
    except Exception as exc:
        result = {"mode": mode, "passed": False, "error": f"{type(exc).__name__}: {exc}"}
    write_json(args.log, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
