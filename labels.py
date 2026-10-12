"""标签定义与统一预测结果结构（B 负责）。

A 和 C 不得在各自模块中重新定义类别名；
所有类别、中文映射、结果结构统一从本模块导入。
"""

import time

STATIC_KIND = "static"
DYNAMIC_KIND = "dynamic"

# 静态类别（5 类数字 + unknown）
STATIC_LABELS = (
    "number_1",
    "number_2",
    "number_3",
    "number_4",
    "number_5",
    "unknown",
)

# 动态类别（4 类动作 + unknown）
DYNAMIC_LABELS = (
    "hello",
    "thanks",
    "goodbye",
    "help",
    "unknown",
)

ALL_LABELS = tuple(dict.fromkeys(STATIC_LABELS + DYNAMIC_LABELS))

# 标签 -> 中文文本
LABEL_TEXT_ZH = {
    "number_1": "一",
    "number_2": "二",
    "number_3": "三",
    "number_4": "四",
    "number_5": "五",
    "hello": "你好",
    "thanks": "谢谢",
    "goodbye": "再见",
    "help": "帮助",
    "unknown": "未知",
}

RESULT_KEYS = ("label", "text", "confidence", "kind", "timestamp")


def is_static_label(label):
    return label in STATIC_LABELS


def is_dynamic_label(label):
    return label in DYNAMIC_LABELS


def is_valid_label(label):
    return label in ALL_LABELS


def validate_confidence(confidence):
    confidence = float(confidence)
    if not 0.0 <= confidence <= 1.0:
        raise ValueError(f"confidence 必须在 [0,1]，当前为 {confidence}")
    return confidence


def make_result(label, confidence, kind, timestamp=None):
    """构造统一预测结果 dict，并做合法性检查。

    返回:
        {"label": str, "text": str, "confidence": float,
         "kind": "static"|"dynamic", "timestamp": float}
    """
    if not is_valid_label(label):
        raise ValueError(f"非法标签: {label!r}，合法标签: {ALL_LABELS}")
    if kind not in (STATIC_KIND, DYNAMIC_KIND):
        raise ValueError(f"非法 kind: {kind!r}，必须为 {STATIC_KIND} 或 {DYNAMIC_KIND}")
    if kind == STATIC_KIND and not is_static_label(label):
        raise ValueError(f"标签 {label!r} 不属于静态类别")
    if kind == DYNAMIC_KIND and not is_dynamic_label(label):
        raise ValueError(f"标签 {label!r} 不属于动态类别")
    if timestamp is None:
        timestamp = time.time()
    else:
        timestamp = float(timestamp)
    return {
        "label": label,
        "text": LABEL_TEXT_ZH[label],
        "confidence": round(validate_confidence(confidence), 4),
        "kind": kind,
        "timestamp": timestamp,
    }
