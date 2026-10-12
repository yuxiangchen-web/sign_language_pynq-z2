"""从 B 的标签定义派生音频映射，不另建类别或中文词汇表。"""

import math
import wave
from pathlib import Path

from labels import ALL_LABELS, LABEL_TEXT_ZH, RESULT_KEYS, make_result

DEFAULT_AUDIO_DIR = Path(__file__).resolve().parent / "wav"
SPEECH_MAP = {label: f"{label}.wav" for label in ALL_LABELS if label != "unknown"}


def wav_path_for_label(label, audio_dir=None):
    """unknown 不播报；非法标签抛异常；路径不依赖当前工作目录。"""
    if label not in ALL_LABELS:
        raise ValueError(f"非法音频标签: {label!r}")
    if label == "unknown":
        return None
    return Path(audio_dir or DEFAULT_AUDIO_DIR).resolve() / SPEECH_MAP[label]


def inspect_wav(path):
    """验证完整的非空 PCM WAV；不将静音或截断文件当作有效语音。"""
    path = Path(path)
    with wave.open(str(path), "rb") as wav:
        channels = wav.getnchannels()
        width = wav.getsampwidth()
        rate = wav.getframerate()
        frames = wav.getnframes()
        if wav.getcomptype() != "NONE" or channels not in (1, 2) or width != 2:
            raise ValueError(f"需要单/双声道 16-bit PCM WAV: {path}")
        if rate <= 0 or frames <= 0:
            raise ValueError(f"空 WAV 或无效采样率: {path}")
        samples = wav.readframes(frames)
        if len(samples) != frames * channels * width:
            raise ValueError(f"WAV 数据截断: {path}")
        if not any(samples):
            raise ValueError(f"WAV 为全零静音: {path}")
    return {"path": str(path.resolve()), "channels": channels,
            "sample_width": width, "sample_rate": rate, "frames": frames,
            "duration_s": frames / rate}


def validate_result(result):
    """校验 B 的统一结果结构，保持其类别和中文映射约定。"""
    if not isinstance(result, dict) or any(key not in result for key in RESULT_KEYS):
        raise ValueError(f"预测结果必须包含 {RESULT_KEYS}")
    checked = make_result(result["label"], result["confidence"], result["kind"],
                          timestamp=result["timestamp"])
    if result["text"] != LABEL_TEXT_ZH[checked["label"]]:
        raise ValueError("结果 text 与 labels.py 不一致")
    if not math.isfinite(checked["timestamp"]):
        raise ValueError("timestamp 必须是有限数值")
    return checked
