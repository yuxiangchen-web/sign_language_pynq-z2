"""测量当前 PC 的 CPU 参考处理耗时；不冒充 ARM/FPGA 或分类性能。"""

import argparse
import json
import platform
import time
from pathlib import Path

import cv2
import numpy as np

from board.run_log import write_json
from feature_utils import hog_feature
from preprocess import preprocess_frame


def benchmark_cpu(paths, frames=100):
    if frames < 1 or not paths:
        raise ValueError("需要非空图像列表和正帧数")
    images = []
    for path in paths:
        # 由 Python 读取字节，避免 Windows OpenCV 文件 API 的长路径限制。
        try:
            image = cv2.imdecode(np.frombuffer(Path(path).read_bytes(), dtype=np.uint8), cv2.IMREAD_COLOR)
        except (OSError, cv2.error) as exc:
            raise ValueError(f"无法读取图像: {path}") from exc
        if image is None:
            raise ValueError(f"无法读取图像: {path}")
        images.append(image)
    # 预热不计入统计；磁盘读取也不计入计算时间。
    for image in images:
        mask, _ = preprocess_frame(image)
        if mask is not None:
            hog_feature(mask)
    preprocess_times, combined_times = [], []
    found = 0
    for index in range(frames):
        image = images[index % len(images)]
        begin = time.perf_counter()
        binary, info = preprocess_frame(image)
        after_preprocess = time.perf_counter()
        if binary is not None:
            hog_feature(binary)
            found += 1
        finish = time.perf_counter()
        preprocess_times.append(after_preprocess - begin)
        combined_times.append(finish - begin)
    return {"mode": "pc_cpu_reference", "passed": True, "frames": frames,
            "source_images": [str(Path(p).resolve()) for p in paths],
            "image_shapes": [list(image.shape) for image in images], "hand_found_frames": found,
            "preprocess_mean_ms": float(np.mean(preprocess_times) * 1000),
            "preprocess_p95_ms": float(np.percentile(preprocess_times, 95) * 1000),
            "preprocess_fps": frames / sum(preprocess_times),
            "preprocess_hog_mean_ms": float(np.mean(combined_times) * 1000),
            "preprocess_hog_fps": frames / sum(combined_times),
            "includes_capture": False, "includes_classifier": False,
            "board_measurement": False, "fpga_measurement": False,
            "processor": platform.processor(), "numpy_version": np.__version__,
            "opencv_version": cv2.__version__}


def main():
    ap = argparse.ArgumentParser(description="PC CPU 预处理及 HOG 计算测量")
    ap.add_argument("--input", nargs="+", required=True)
    ap.add_argument("--frames", type=int, default=100)
    ap.add_argument("--log", default="report/role_c_logs/cpu_reference.json")
    args = ap.parse_args()
    try:
        result = benchmark_cpu(args.input, args.frames)
    except Exception as exc:
        result = {"mode": "pc_cpu_reference", "passed": False, "error": str(exc)}
    write_json(args.log, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
