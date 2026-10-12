"""预处理与标签模块测试（B 负责）。"""

import cv2
import numpy as np
import pytest

from labels import (ALL_LABELS, DYNAMIC_LABELS, LABEL_TEXT_ZH, RESULT_KEYS,
                    STATIC_LABELS, make_result, validate_confidence)
from preprocess import (IMG_SIZE, largest_component, normalize_binary,
                        preprocess_frame, segment_hand_ycrcb)

# BGR(100,120,200) 的 YCrCb 约 (142,169,104)，落在默认肤色范围内
SKIN_BGR = (100, 120, 200)
BG_BGR = (50, 50, 50)  # YCrCb 约 (50,128,128)，在肤色范围外


def make_frame(hand=True, touch_edge=False, center=(120, 160)):
    img = np.full((240, 320, 3), BG_BGR, np.uint8)
    if hand:
        if touch_edge:
            center = (10, 10)
        cv2.ellipse(img, center, (40, 55), 30, 0, 360, SKIN_BGR, -1)
    return img


# ---------- 预处理 ----------

def test_segment_hand_ycrcb_binary_values():
    mask = segment_hand_ycrcb(make_frame())
    assert set(np.unique(mask)) <= {0, 255}
    assert (mask > 0).sum() > 500  # 手部区域被分割出来


def test_preprocess_output_size():
    binary, info = preprocess_frame(make_frame())
    assert binary is not None
    assert binary.shape == (IMG_SIZE, IMG_SIZE)
    assert binary.dtype == np.uint8
    assert info["hand_found"] is True
    assert info["area"] > 0
    assert 0 <= info["centroid"][0] <= 320
    assert 0 <= info["centroid"][1] <= 240


def test_empty_input_raises():
    with pytest.raises(ValueError):
        segment_hand_ycrcb(None)
    with pytest.raises(ValueError):
        segment_hand_ycrcb(np.zeros((0, 0, 3), np.uint8))
    with pytest.raises(ValueError):
        segment_hand_ycrcb(np.zeros((240, 320), np.uint8))  # 灰度图


def test_no_hand_returns_none():
    binary, info = preprocess_frame(make_frame(hand=False))
    assert binary is None
    assert info["hand_found"] is False


def test_hand_touches_edge_flagged():
    binary, info = preprocess_frame(make_frame(touch_edge=True))
    assert binary is not None  # 出框仍可处理，但要有标记
    assert info["touches_edge"] is True
    # 正常图不应误报出框
    _, info2 = preprocess_frame(make_frame())
    assert info2["touches_edge"] is False


def test_normalize_binary_shape():
    mask = segment_hand_ycrcb(make_frame())
    comp = largest_component(mask)
    assert comp is not None
    binary = normalize_binary(comp, size=64)
    assert binary.shape == (64, 64)
    assert (binary > 0).any()


# ---------- 标签与统一结果结构 ----------

def test_make_result_valid():
    result = make_result("number_1", 0.9, "static")
    assert set(result) == set(RESULT_KEYS)
    assert result["label"] == "number_1"
    assert result["text"] == LABEL_TEXT_ZH["number_1"]
    assert result["kind"] == "static"
    assert 0.0 <= result["confidence"] <= 1.0
    assert isinstance(result["timestamp"], float)

    result = make_result("hello", 0.91, "dynamic", timestamp=1234567890.0)
    assert result["text"] == "你好"
    assert result["timestamp"] == 1234567890.0


def test_make_result_invalid():
    with pytest.raises(ValueError):
        make_result("number_9", 0.9, "static")   # 非法标签
    with pytest.raises(ValueError):
        make_result("hello", 0.9, "static")      # 动态标签用于静态
    with pytest.raises(ValueError):
        make_result("number_1", 0.9, "dynamic")  # 静态标签用于动态
    with pytest.raises(ValueError):
        make_result("number_1", 1.5, "static")   # 置信度越界
    with pytest.raises(ValueError):
        make_result("number_1", 0.9, "video")    # 非法 kind
    with pytest.raises(ValueError):
        validate_confidence(-0.1)


def test_label_sets():
    assert "unknown" in STATIC_LABELS and "unknown" in DYNAMIC_LABELS
    assert set(STATIC_LABELS) & set(DYNAMIC_LABELS) == {"unknown"}
    assert all(label in LABEL_TEXT_ZH for label in ALL_LABELS)
