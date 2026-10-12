"""统一预测接口（B 负责）。

对外约定（A 的板端程序和 C 的联调脚本都按此调用）：

    predictor = RealtimeSignPredictor(
        static_model_path="models/static_model.joblib",
        dynamic_model_path="models/dynamic_model.joblib",
    )
    result = predictor.predict(frame_or_sequence)
    # result = {"label": "hello", "text": "你好",
    #           "confidence": 0.91, "kind": "dynamic",
    #           "timestamp": 1234567890.0}

实时模式（逐帧输入，动作起止检测 + 投票 + 冷却 + 防重复播报）：

    result = predictor.feed(frame_bgr)   # 无动作结束时返回 None

模型文件缺失时自动退化为假预测器（恒返回 unknown），供板端联调先行。
"""

import json
import os
import time
from collections import Counter

import joblib
import numpy as np

from feature_utils import hog_feature
from labels import DYNAMIC_KIND, STATIC_KIND, make_result
from preprocess import preprocess_frame
from sequence_features import DEFAULT_SEQ_LEN, extract_sequence_features, sample_frames

DEFAULT_CONFIG = {
    "seq_len": 16,
    "static_min_confidence": 0.50,
    "dynamic_min_confidence": 0.50,
    "start_motion_threshold": 0.03,   # 归一化中心位移/帧，超过视为动作开始
    "end_motion_threshold": 0.01,     # 低于视为动作结束
    "end_patience_frames": 6,         # 连续静止帧数达到后结束动作
    "no_hand_patience_frames": 8,     # 连续无手帧数达到后结束动作
    "max_action_frames": 96,          # 动作最长帧数，防止缓存无限增长
    "cooldown_s": 1.5,                # 预测后的冷却时间
    "repeat_window_s": 3.0,           # 同一标签的防重复播报窗口
}


def load_config(path=None):
    """加载配置：默认值 + JSON 文件覆盖。"""
    config = dict(DEFAULT_CONFIG)
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            config.update(json.load(f))
    return config


def _soft_confidence(model, x, label):
    """兼容 predict_proba / decision_function 的置信度提取。"""
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(x)[0]
        return float(proba[list(model.classes_).index(label)])
    if hasattr(model, "decision_function"):
        scores = np.asarray(model.decision_function(x))[0].astype(float)
        proba = np.exp(scores - scores.max())
        proba = proba / proba.sum()
        return float(proba[list(model.classes_).index(label)])
    return 1.0


class StaticPredictor:
    """静态手语预测器；模型缺失时自动退化为假预测器（恒返回 unknown）。"""

    def __init__(self, model_path=None, min_confidence=0.5):
        if model_path and os.path.exists(model_path):
            self.model = joblib.load(model_path)
        else:
            if model_path:
                print(f"[predictor] 静态模型不存在，使用假预测器: {model_path}")
            self.model = None
        self.min_confidence = float(min_confidence)

    def predict(self, frame_bgr):
        """输入单帧 BGR 图像，返回 (label, confidence)。"""
        if self.model is None:
            return "unknown", 1.0
        binary, _ = preprocess_frame(frame_bgr)
        if binary is None:
            return "unknown", 1.0
        x = hog_feature(binary).reshape(1, -1)
        label = self.model.predict(x)[0]
        confidence = _soft_confidence(self.model, x, label)
        if confidence < self.min_confidence:
            return "unknown", confidence
        return str(label), confidence


class DynamicPredictor:
    """动态手语预测器；模型缺失时自动退化为假预测器。"""

    def __init__(self, model_path=None, seq_len=DEFAULT_SEQ_LEN, min_confidence=0.5):
        if model_path and os.path.exists(model_path):
            self.model = joblib.load(model_path)
        else:
            if model_path:
                print(f"[predictor] 动态模型不存在，使用假预测器: {model_path}")
            self.model = None
        self.seq_len = int(seq_len)
        self.min_confidence = float(min_confidence)

    def predict(self, frames):
        """输入帧序列（至少 2 帧），返回 (label, confidence)。"""
        if self.model is None:
            return "unknown", 0.0
        frames = list(frames)
        if len(frames) < 2:
            raise ValueError("动态序列帧数不足：至少需要 2 帧")
        x = extract_sequence_features(frames, self.seq_len).reshape(1, -1)
        label = self.model.predict(x)[0]
        confidence = _soft_confidence(self.model, x, label)
        if confidence < self.min_confidence:
            return "unknown", confidence
        return str(label), confidence


class RealtimeSignPredictor:
    """统一实时接口：静态 / 动态 / 逐帧状态机。

    状态机：
      idle -> (手部中心位移超过 start_motion_threshold) -> recording
      recording -> (静止 end_patience_frames 帧 / 无手 no_hand_patience_frames 帧
                    / 达到 max_action_frames) -> 滑动窗口投票预测 -> 冷却
    """

    def __init__(self, config=None, static_model_path=None, dynamic_model_path=None,
                 static_predictor=None, dynamic_predictor=None):
        self.config = dict(DEFAULT_CONFIG)
        if isinstance(config, str):
            self.config.update(load_config(config))
        elif isinstance(config, dict):
            self.config.update(config)
        if static_predictor is None:
            static_predictor = StaticPredictor(
                static_model_path, self.config["static_min_confidence"])
        if dynamic_predictor is None:
            dynamic_predictor = DynamicPredictor(
                dynamic_model_path, self.config["seq_len"],
                self.config["dynamic_min_confidence"])
        self.static_predictor = static_predictor
        self.dynamic_predictor = dynamic_predictor
        self._reset()

    def _reset(self):
        self._state = "idle"
        self._buffer = []
        self._prev_centroid = None
        self._end_counter = 0
        self._no_hand_counter = 0
        self._cooldown_until = 0.0
        self._last_label = None
        self._last_time = 0.0

    # ---------- 统一入口 ----------

    def predict(self, frame_or_sequence):
        """静态输入单帧，动态输入帧序列，返回统一 result dict。"""
        if isinstance(frame_or_sequence, (list, tuple)):
            return self.predict_sequence(frame_or_sequence)
        if isinstance(frame_or_sequence, np.ndarray) and frame_or_sequence.ndim == 4:
            return self.predict_sequence(list(frame_or_sequence))
        return self.predict_static(frame_or_sequence)

    def predict_static(self, frame_bgr):
        label, confidence = self.static_predictor.predict(frame_bgr)
        if confidence < self.config["static_min_confidence"]:
            label = "unknown"
        return make_result(label, confidence, STATIC_KIND)

    def predict_sequence(self, frames):
        frames = list(frames)
        if len(frames) < 2:
            raise ValueError("动态序列帧数不足：至少需要 2 帧")
        sampled = sample_frames(frames, self.config["seq_len"])
        label, confidence = self.dynamic_predictor.predict(sampled)
        if confidence < self.config["dynamic_min_confidence"]:
            label = "unknown"
        return make_result(label, confidence, DYNAMIC_KIND)

    # ---------- 实时状态机 ----------

    def feed(self, frame_bgr):
        """逐帧输入；动作结束并成功播报时返回 result dict，否则返回 None。"""
        _, info = preprocess_frame(frame_bgr)
        now = time.time()
        if info["hand_found"]:
            centroid = info["centroid"]
            diag = float(np.hypot(info["frame_w"], info["frame_h"]))
            if self._prev_centroid is None:
                speed = 0.0
            else:
                dx = centroid[0] - self._prev_centroid[0]
                dy = centroid[1] - self._prev_centroid[1]
                speed = float(np.hypot(dx, dy)) / diag
            self._prev_centroid = centroid
            if self._state == "idle":
                if (now >= self._cooldown_until
                        and speed >= self.config["start_motion_threshold"]):
                    self._state = "recording"
                    self._buffer = [frame_bgr]
                    self._end_counter = 0
                    self._no_hand_counter = 0
            elif self._state == "recording":
                self._buffer.append(frame_bgr)
                self._end_counter = (self._end_counter + 1
                                     if speed <= self.config["end_motion_threshold"]
                                     else 0)
                if (self._end_counter >= self.config["end_patience_frames"]
                        or len(self._buffer) >= self.config["max_action_frames"]):
                    return self._finish_action()
        else:
            self._prev_centroid = None
            if self._state == "recording":
                self._no_hand_counter += 1
                if self._no_hand_counter >= self.config["no_hand_patience_frames"]:
                    return self._finish_action()
        return None

    def _finish_action(self):
        """结束当前动作：滑动窗口多帧投票 -> 冷却/防重复判断。"""
        frames = self._buffer
        self._state = "idle"
        self._buffer = []
        self._end_counter = 0
        self._no_hand_counter = 0
        self._prev_centroid = None
        if len(frames) < 2:
            return None

        seq_len = self.config["seq_len"]
        stride = max(1, seq_len // 4)
        if len(frames) <= seq_len:
            windows = [frames]
        else:
            windows = [frames[i:i + seq_len]
                       for i in range(0, len(frames) - seq_len + 1, stride)]
            if windows[-1][-1] is not frames[-1]:
                windows.append(frames[-seq_len:])

        votes = [self.dynamic_predictor.predict(window) for window in windows]
        if not votes:
            return None
        counter = Counter(label for label, _ in votes)
        label, _ = counter.most_common(1)[0]
        confidence = float(np.mean([c for l, c in votes if l == label]))
        if confidence < self.config["dynamic_min_confidence"]:
            label = "unknown"
        return self._announce(make_result(label, confidence, DYNAMIC_KIND))

    def _announce(self, result, now=None):
        """冷却与防重复播报；被抑制时返回 None。"""
        now = time.time() if now is None else float(now)
        label = result["label"]
        if now < self._cooldown_until:
            return None
        if (label != "unknown" and label == self._last_label
                and now - self._last_time < self.config["repeat_window_s"]):
            return None
        self._last_label = label
        self._last_time = now
        self._cooldown_until = now + self.config["cooldown_s"]
        return result
