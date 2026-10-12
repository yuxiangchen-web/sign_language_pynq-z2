"""CPU 测量脚本的有效输入与错误传播检查。"""

import cv2
import numpy as np
import pytest

from board.role_c_benchmark import benchmark_cpu


def test_cpu_measurement_is_explicitly_pc_only(tmp_path):
    image = np.full((240, 320, 3), 50, np.uint8)
    cv2.rectangle(image, (100, 70), (180, 190), (100, 120, 200), -1)
    path = tmp_path / "synthetic_test_input.png"
    ok, encoded = cv2.imencode(".png", image)
    assert ok
    path.write_bytes(encoded.tobytes())
    result = benchmark_cpu([path], frames=3)
    assert result["frames"] == result["hand_found_frames"] == 3
    assert result["preprocess_fps"] > 0 and result["preprocess_hog_fps"] > 0
    assert result["mode"] == "pc_cpu_reference" and result["board_measurement"] is False
    assert result["includes_classifier"] is False


def test_invalid_cpu_inputs(tmp_path):
    with pytest.raises(ValueError):
        benchmark_cpu([])
    with pytest.raises(ValueError):
        benchmark_cpu([tmp_path / "missing.png"])
