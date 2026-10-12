"""真实 DMA 黄金向量连续测试；输入格式由 A 提供，禁止默认假设 loopback。"""

import argparse
import importlib
import json
import time

import numpy as np

from board.dma_transfer import DmaTransfer
from board.load_overlay import OverlaySession, inspect_overlay
from board.run_log import write_json


def run_dma_test(transfer, inputs, expected, frames=100, duration_s=0.0, timeout_s=1.0,
                 start_ip=None):
    """frames 与 duration 同时设置时，两项目标都达到后才结束。"""
    if frames < 1 or duration_s < 0 or not np.isfinite(duration_s):
        raise ValueError("frames 必须 >= 1，duration_s 必须是有限非负数")
    if len(inputs) != len(expected) or len(inputs) == 0:
        raise ValueError("输入与黄金输出数量必须相等且非零")
    latencies = []
    begin = time.monotonic()
    records = []
    count = 0
    while count < frames or time.monotonic() - begin < duration_s:
        index = count % len(inputs)
        frame_start = time.monotonic()
        try:
            output = transfer.transfer(inputs[index], timeout_s=timeout_s, start_ip=start_ip)
            golden = np.asarray(expected[index])
            passed = (output.shape == golden.shape and output.dtype == golden.dtype
                      and np.array_equal(output, golden))
            elapsed = time.monotonic() - frame_start
            record = {"frame": count, "passed": passed, "latency_s": elapsed}
            if not passed:
                record["error"] = "输出与黄金向量不一致"
                if output.shape == golden.shape:
                    record["different_elements"] = int(np.count_nonzero(output != golden))
            records.append(record)
            latencies.append(elapsed)
            count += 1
            if not passed:
                break
        except Exception as exc:
            records.append({"frame": count, "passed": False,
                            "error": f"{type(exc).__name__}: {exc}",
                            "dma_record": transfer.last_record})
            break
    total = time.monotonic() - begin
    return {"mode": "hardware_dma_golden", "passed": all(r["passed"] for r in records),
            "requested_frames": frames, "requested_duration_s": duration_s,
            "completed_frames": count, "elapsed_s": total, "frames": records,
            "fps": count / total if total else 0.0,
            "latency_mean_s": float(np.mean(latencies)) if latencies else None,
            "latency_p95_s": float(np.percentile(latencies, 95)) if latencies else None}


def main():
    ap = argparse.ArgumentParser(description="真实 AXI DMA 连续黄金向量测试")
    ap.add_argument("--bit", required=True)
    ap.add_argument("--dma", help="必须使用 A 交付的真实 HWH IP 名称")
    ap.add_argument("--vectors", help="NPZ 包含 inputs/expected；首轴为向量编号")
    ap.add_argument("--adapter", help="A 提供的模块，含 start_ip(session) 和 reset_ip(session)")
    ap.add_argument("--free-running", action="store_true", help="调用方确认 IP 无需软件启动")
    ap.add_argument("--frames", type=int, default=100)
    ap.add_argument("--duration-s", type=float, default=0.0)
    ap.add_argument("--timeout-s", type=float, default=1.0)
    ap.add_argument("--inspect", action="store_true")
    ap.add_argument("--log", default="board/logs/dma.json")
    args = ap.parse_args()
    mode = "offline_metadata" if args.inspect else "hardware_dma_golden"
    transfer = None
    try:
        metadata = inspect_overlay(args.bit)
        if args.inspect:
            result = {"mode": mode, "passed": True, "dma_ips": metadata["dma_ips"],
                      "dma_available": bool(metadata["dma_ips"]), "dma_executed": False}
        else:
            if not args.dma or not args.vectors:
                raise ValueError("真实测试需要 --dma 和 --vectors，C 不猜像素格式")
            if args.dma not in metadata["dma_ips"]:
                raise ValueError("当前 Overlay 没有指定 DMA，不能执行图像传输")
            if bool(args.adapter) == args.free_running:
                raise ValueError("明确指定 --adapter 或 --free-running，不能猜测 HLS 启动方式")
            with np.load(args.vectors, allow_pickle=False) as vectors:
                inputs, expected = vectors["inputs"].copy(), vectors["expected"].copy()
            if inputs.ndim < 2 or expected.ndim < 2 or len(inputs) != len(expected) or not len(inputs):
                raise ValueError("黄金向量首轴必须为非空且数量相同的帧编号")
            session = OverlaySession(args.bit)
            adapter = importlib.import_module(args.adapter) if args.adapter else None
            if adapter:
                adapter.reset_ip(session)
            transfer = DmaTransfer(session.get_dma(args.dma), inputs.shape[1:], expected.shape[1:],
                                   inputs.dtype, expected.dtype)
            result = run_dma_test(transfer, inputs, expected, args.frames,
                                  args.duration_s, args.timeout_s,
                                  start_ip=(lambda: adapter.start_ip(session)) if adapter else None)
    except Exception as exc:
        result = {"mode": mode, "passed": False, "error": f"{type(exc).__name__}: {exc}"}
    finally:
        if transfer:
            try:
                transfer.close()
            except Exception as exc:
                result.update(passed=False, cleanup_error=str(exc))
    write_json(args.log, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
