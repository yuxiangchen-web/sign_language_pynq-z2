"""对实际 HWH 中的 AXI GPIO 执行 LED 模式读写，结束后恢复原值。"""

import argparse
import json
import math
import time

from board.load_overlay import DEFAULT_BITSTREAM, OverlaySession, _integer, inspect_overlay
from board.run_log import write_json


def gpio_contract(metadata, name=None):
    names = [n for n, ip in metadata["ips"].items()
             if ip["vlnv"].startswith("xilinx.com:ip:axi_gpio:")]
    if name is None:
        if len(names) != 1:
            raise ValueError(f"必须明确指定 GPIO IP: {names}")
        name = names[0]
    if name not in names:
        raise ValueError(f"不是实际 GPIO IP: {name}")
    ip = metadata["ips"][name]
    width = _integer(ip["parameters"]["C_GPIO_WIDTH"])
    if not 1 <= width <= 32:
        raise ValueError("GPIO 宽度不在 1..32")
    data, tri = (ip["registers"][r] for r in ("GPIO_DATA", "GPIO_TRI"))
    for register in (data, tri):
        if register["offset"] % 4 or register["offset"] + 4 > ip["address_range"]:
            raise ValueError("HWH 寄存器偏移越界或不对齐")
        if register["access"] != "read-write":
            raise ValueError("GPIO 寄存器不可读写")
    return {"ip": name, "base_address": ip["base_address"], "width": width,
            "data_offset": data["offset"], "tri_offset": tri["offset"]}


def test_gpio_registers(session, name=None, hold_s=0.0):
    if not math.isfinite(hold_s) or hold_s < 0:
        raise ValueError("hold_s 必须是有限非负数")
    contract = gpio_contract(session.metadata, name)
    ip = session.get_ip(contract["ip"])
    data_offset, tri_offset = contract["data_offset"], contract["tri_offset"]
    mask = (1 << contract["width"]) - 1
    original_data, original_tri = int(ip.read(data_offset)), int(ip.read(tri_offset))
    records = []
    try:
        ip.write(tri_offset, original_tri & ~mask)
        if int(ip.read(tri_offset)) & mask:
            raise AssertionError("GPIO 未成功切换输出方向")
        for pattern in [0] + [1 << i for i in range(contract["width"])] + [mask, 0]:
            ip.write(data_offset, pattern)
            readback = int(ip.read(data_offset)) & mask
            records.append({"written": pattern, "readback": readback})
            if readback != pattern:
                raise AssertionError(f"GPIO 读回不一致: 写 {pattern}, 读 {readback}")
            if hold_s:
                time.sleep(hold_s)
    finally:
        try:
            ip.write(data_offset, original_data)
        finally:
            ip.write(tri_offset, original_tri)
    return {"mode": "hardware_register", "passed": True, "contract": contract,
            "patterns": records, "restored": True}


# 避免 pytest 将需要真实板卡的工具函数当作 fixture 测试。
test_gpio_registers.__test__ = False


def main():
    ap = argparse.ArgumentParser(description="AXI GPIO 寄存器与 LED 联调")
    ap.add_argument("--bit", default=str(DEFAULT_BITSTREAM))
    ap.add_argument("--ip")
    ap.add_argument("--inspect", action="store_true")
    ap.add_argument("--hold-s", type=float, default=0.0)
    ap.add_argument("--log", default="board/logs/registers.json")
    args = ap.parse_args()
    mode = "offline_metadata" if args.inspect else "hardware_register"
    try:
        if args.inspect:
            result = {"mode": mode, "contract": gpio_contract(inspect_overlay(args.bit), args.ip),
                      "passed": True, "register_io_executed": False}
        else:
            result = test_gpio_registers(OverlaySession(args.bit), args.ip, args.hold_s)
    except Exception as exc:
        result = {"mode": mode, "passed": False, "error": f"{type(exc).__name__}: {exc}"}
    write_json(args.log, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
