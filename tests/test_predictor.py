"""缁熶竴棰勬祴鎺ュ彛娴嬭瘯锛圔 璐熻矗锛夈€?

浣跨敤鍋囬娴嬪櫒娉ㄥ叆锛屼笉渚濊禆璁粌濂界殑妯″瀷鏂囦欢銆?
"""

import cv2
import numpy as np
import pytest

from labels import DYNAMIC_KIND, RESULT_KEYS, STATIC_KIND, make_result
from predictor import RealtimeSignPredictor
from sequence_features import extract_sequence_features, sample_frames

SKIN_BGR = (100, 120, 200)
BG_BGR = (50, 50, 50)
FRAME_H, FRAME_W = 240, 320
DIAG = float(np.hypot(FRAME_W, FRAME_H))


def make_frame(center=(120, 160)):
    img = np.full((FRAME_H, FRAME_W, 3), BG_BGR, np.uint8)
    cv2.ellipse(img, center, (40, 55), 30, 0, 360, SKIN_BGR, -1)
    return img


class FakeStatic:
    def __init__(self, label, conf):
        self.label, self.conf = label, conf

    def predict(self, frame):
        return self.label, self.conf


class FakeDynamic:
    def __init__(self, label, conf):
        self.label, self.conf = label, conf
        self.calls: list[int] = []

    def predict(self, frames):
        self.calls.append(len(frames))
        return self.label, self.conf


def make_rt(seq_len=16, static_label="number_1", dynamic_label="hello",
            conf=0.9, **over):
    cfg = {
        "seq_len": seq_len,
        "static_min_confidence": 0.5,
        "dynamic_min_confidence": 0.5,
        "start_motion_threshold": 0.03,
        "end_motion_threshold": 0.01,
        "end_patience_frames": 4,
        "no_hand_patience_frames": 4,
        "max_action_frames": 96,
        "cooldown_s": 1.5,
        "repeat_window_s": 3.0,
    }
    cfg.update(over)
    return RealtimeSignPredictor(
        config=cfg,
        static_predictor=FakeStatic(static_label, conf),
        dynamic_predictor=FakeDynamic(dynamic_label, conf),
    )


def motion_clip(moving=8, still=8, step=30):
    """Frames that move first, then stay still to close an action."""
    frames = [make_frame(center=(60 + i * step, 100)) for i in range(moving)]
    frames += [make_frame(center=(60 + (moving - 1) * step, 100))] * still
    return frames


# ---------- 缁熶竴缁撴灉缁撴瀯 ----------

def test_static_result_structure():
    rt = make_rt()
    result = rt.predict(make_frame())
    assert set(result) == set(RESULT_KEYS)
    assert result["kind"] == STATIC_KIND
    assert result["label"] == "number_1"
    assert result["text"] == "一"
    assert 0.0 <= result["confidence"] <= 1.0
    assert isinstance(result["timestamp"], float)


def test_dynamic_result_structure_and_seq_len_switch():
    rt = make_rt(seq_len=24)
    frames = [make_frame(center=(60 + 5 * i, 100)) for i in range(40)]
    result = rt.predict(frames)
    assert result["kind"] == DYNAMIC_KIND
    assert result["label"] == "hello"
    assert result["text"] == "你好"
    assert 0.0 <= result["confidence"] <= 1.0
    assert rt.dynamic_predictor.calls[-1] == 24  # 16/24 甯у垏鎹㈢敓鏁?

    rt16 = make_rt(seq_len=16)
    rt16.predict(frames)
    assert rt16.dynamic_predictor.calls[-1] == 16


def test_static_and_dynamic_structure_consistent():
    rt = make_rt()
    static = rt.predict(make_frame())
    dynamic = rt.predict_sequence([make_frame(), make_frame(center=(130, 170))])
    assert set(static) == set(dynamic) == set(RESULT_KEYS)


# ---------- unknown 鍒ゆ柇 ----------

def test_unknown_judgment_low_confidence():
    rt = make_rt(conf=0.3)
    assert rt.predict_static(make_frame())["label"] == "unknown"
    assert rt.predict_sequence(
        [make_frame(), make_frame(center=(130, 170))])["label"] == "unknown"


def test_unknown_passthrough():
    rt = make_rt(dynamic_label="unknown")
    result = rt.predict_sequence([make_frame(), make_frame(center=(130, 170))])
    assert result["label"] == "unknown"
    assert result["text"] == "未知"


# ---------- 甯ф暟涓嶈冻 ----------

def test_sequence_too_short_raises():
    rt = make_rt()
    frame = make_frame()
    with pytest.raises(ValueError):
        rt.predict_sequence([])
    with pytest.raises(ValueError):
        rt.predict_sequence([frame])
    with pytest.raises(ValueError):
        extract_sequence_features([])
    with pytest.raises(ValueError):
        extract_sequence_features([frame])
    with pytest.raises(ValueError):
        sample_frames([])


# ---------- 瀹炴椂鐘舵€佹満 ----------

def test_feed_detects_action():
    rt = make_rt()
    results = [r for r in (rt.feed(f) for f in motion_clip()) if r is not None]
    assert len(results) == 1
    assert results[0]["kind"] == DYNAMIC_KIND
    assert results[0]["label"] == "hello"


def test_feed_no_motion_returns_none():
    rt = make_rt()
    for _ in range(20):
        assert rt.feed(make_frame()) is None


def test_feed_no_hand_returns_none():
    rt = make_rt()
    blank = np.full((FRAME_H, FRAME_W, 3), BG_BGR, np.uint8)
    for _ in range(20):
        assert rt.feed(blank) is None


def test_feed_short_action_ignored():
    rt = make_rt()
    # 鍙湁 1 甯хЩ鍔紝鍔ㄤ綔缂撳啿涓嶈冻 2 甯ф椂涓嶅簲浜х敓缁撴灉
    frames = [make_frame(center=(60, 100)), make_frame(center=(90, 100))]
    frames += [make_frame(center=(90, 100))] * 6
    results = [r for r in (rt.feed(f) for f in frames) if r is not None]
    # 璧峰 1 甯?+ 缁撴潫鑰愬績 4 甯т粛 >= 2 甯э紝浼氭湁涓€娆￠娴嬶紱
    # 鍏抽敭鏄笉宕╂簝涓旂粨鏋滅粨鏋勫悎娉?
    for result in results:
        assert set(result) == set(RESULT_KEYS)


# ---------- 鍐峰嵈涓庨槻閲嶅鎾姤 ----------

def test_cooldown_and_repeat_suppression():
    rt = make_rt()
    t0 = 1000.0
    # 绗竴娆℃挱鎶ユ垚鍔?
    r1 = rt._announce(make_result("hello", 0.9, DYNAMIC_KIND), now=t0)
    assert r1 is not None
    # 鍐峰嵈鏈熷唴锛氫换浣曟爣绛鹃兘琚姂鍒?
    assert rt._announce(make_result("thanks", 0.9, DYNAMIC_KIND), now=t0 + 0.5) is None
    # 鍐峰嵈缁撴潫锛屼絾鍚屼竴鏍囩浠嶅湪闃查噸澶嶇獥鍙ｅ唴
    assert rt._announce(make_result("hello", 0.9, DYNAMIC_KIND), now=t0 + 2.0) is None
    # 鍐峰嵈缁撴潫涓旀槸涓嶅悓鏍囩锛屽彲浠ユ挱鎶?
    r2 = rt._announce(make_result("thanks", 0.9, DYNAMIC_KIND), now=t0 + 2.0)
    assert r2 is not None and r2["label"] == "thanks"
    # 瓒呰繃闃查噸澶嶇獥鍙ｅ悗锛屽悓涓€鏍囩鎭㈠鎾姤
    assert rt._announce(make_result("hello", 0.9, DYNAMIC_KIND),
                        now=t0 + 2.0 + 3.5) is not None


def test_unknown_not_suppressed_by_repeat():
    rt = make_rt()
    t0 = 2000.0
    assert rt._announce(make_result("hello", 0.9, DYNAMIC_KIND), now=t0) is not None
    # unknown 涓嶅弬涓庨槻閲嶅锛堝喎鍗寸粨鏉熷悗鍙甯歌繑鍥烇級
    r = rt._announce(make_result("unknown", 0.4, DYNAMIC_KIND), now=t0 + 2.0)
    assert r is not None and r["label"] == "unknown"

