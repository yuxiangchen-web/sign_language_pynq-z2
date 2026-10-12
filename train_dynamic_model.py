"""训练动态手语分类模型（B 负责）。

以完整视频为单位提取序列特征，训练随机森林或线性 SVM。
训练集和测试集必须来自不同视频，不允许把一段视频拆成两份。

用法：
    python train_dynamic_model.py \
        --input data/dynamic \
        --test-input data/dynamic_test \
        --model models/dynamic_model.joblib \
        --seq-len 16 --classifier rf
"""

import argparse
import json
import os

import cv2
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.svm import LinearSVC

from labels import DYNAMIC_LABELS
from sequence_features import extract_sequence_features

VIDEO_EXTS = (".avi", ".mp4", ".mov", ".mkv")


def video_frames(path):
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise RuntimeError(f"无法打开视频: {path}")
    frames = []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frames.append(frame)
    cap.release()
    return frames


def load_dataset(root, seq_len):
    """读取 <root>/<label>/<video> 结构的数据集，返回 (features, labels, files)。"""
    features, labels, files = [], [], []
    if not root or not os.path.isdir(root):
        return features, labels, files
    for label in sorted(os.listdir(root)):
        label_dir = os.path.join(root, label)
        if not os.path.isdir(label_dir) or label not in DYNAMIC_LABELS:
            continue
        for name in sorted(os.listdir(label_dir)):
            if not name.lower().endswith(VIDEO_EXTS):
                continue
            frames = video_frames(os.path.join(label_dir, name))
            if len(frames) < 2:
                print(f"[warn] 视频帧数不足，跳过: {label}/{name}")
                continue
            features.append(extract_sequence_features(frames, seq_len))
            labels.append(label)
            files.append(f"{label}/{name}")
    return features, labels, files


def build_classifier(kind):
    if kind == "rf":
        return RandomForestClassifier(n_estimators=200, random_state=0, n_jobs=-1)
    if kind == "linear_svm":
        return LinearSVC(C=1.0, random_state=0)
    raise ValueError(f"未知分类器: {kind}")


def main():
    ap = argparse.ArgumentParser(description="训练动态手语分类模型")
    ap.add_argument("--input", required=True, help="训练视频根目录")
    ap.add_argument("--test-input", default=None, help="独立测试视频根目录")
    ap.add_argument("--model", default="models/dynamic_model.joblib")
    ap.add_argument("--seq-len", type=int, default=16, choices=(16, 24))
    ap.add_argument("--classifier", default="rf", choices=("rf", "linear_svm"))
    ap.add_argument("--metrics-out", default="report/metrics_dynamic.json")
    args = ap.parse_args()

    X, y, _ = load_dataset(args.input, args.seq_len)
    if not X:
        raise SystemExit(f"没有读到任何训练视频: {args.input}")

    model = build_classifier(args.classifier)
    model.fit(np.stack(X), np.array(y))

    metrics = {
        "classifier": args.classifier,
        "seq_len": args.seq_len,
        "train_samples": len(y),
    }
    if args.test_input:
        Xt, yt, _ = load_dataset(args.test_input, args.seq_len)
        if Xt:
            pred = model.predict(np.stack(Xt))
            labels = list(DYNAMIC_LABELS)
            metrics.update({
                "test_samples": len(yt),
                "accuracy": float(accuracy_score(yt, pred)),
                "macro_f1": float(f1_score(
                    yt, pred, labels=labels, average="macro", zero_division=0)),
                "confusion_matrix": confusion_matrix(
                    yt, pred, labels=labels).tolist(),
                "labels": labels,
            })
        else:
            print(f"[warn] 测试目录没有可用视频: {args.test_input}")

    os.makedirs(os.path.dirname(os.path.abspath(args.model)), exist_ok=True)
    joblib.dump(model, args.model)
    os.makedirs(os.path.dirname(os.path.abspath(args.metrics_out)), exist_ok=True)
    with open(args.metrics_out, "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    print(f"训练视频 {len(y)} 段（seq_len={args.seq_len}, {args.classifier}）")
    if "accuracy" in metrics:
        print(f"测试视频 {metrics['test_samples']} 段，"
              f"accuracy={metrics['accuracy']:.4f} macro_f1={metrics['macro_f1']:.4f}")
    print(f"模型已保存: {args.model}")
    print(f"指标已保存: {args.metrics_out}")


if __name__ == "__main__":
    main()
