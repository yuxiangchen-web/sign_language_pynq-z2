"""璁粌闈欐€佹墜璇垎绫绘ā鍨嬶紙B 璐熻矗锛夈€?

鐢ㄦ硶锛?
    python train_static_model.py \
        --train-features data/features/static_train.npz \
        --test-features data/features/static_test.npz \
        --model models/static_model.joblib
"""

import argparse
import json
import os

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from labels import STATIC_LABELS


def load_features(path):
    data = np.load(path, allow_pickle=False)
    return data["X"], data["y"]


def evaluate(model, X, y):
    pred = model.predict(X)
    labels = list(STATIC_LABELS)
    return {
        "accuracy": float(accuracy_score(y, pred)),
        "macro_f1": float(f1_score(y, pred, labels=labels, average="macro", zero_division=0)),
        "per_class_recall": {
            label: float(score) for label, score in zip(
                labels, recall_score(y, pred, labels=labels, average=None, zero_division=0))
        },
        "confusion_matrix": confusion_matrix(y, pred, labels=labels).tolist(),
        "labels": labels,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train-features", required=True)
    ap.add_argument("--test-features", default=None,
                    help="鐙珛娴嬭瘯鐗瑰緛锛涚己鐪佹椂浠庤缁冮泦涓垎灞傚垝鍒?20%%")
    ap.add_argument("--model", default="models/static_model.joblib")
    ap.add_argument("--metrics-out", default="report/metrics_static.json")
    args = ap.parse_args()

    X, y = load_features(args.train_features)
    if args.test_features:
        X_test, y_test = load_features(args.test_features)
    else:
        X, X_test, y, y_test = train_test_split(
            X, y, test_size=0.2, random_state=0, stratify=y)

    model = make_pipeline(
        StandardScaler(),
        SVC(kernel="rbf", C=10.0, gamma="scale", probability=True, random_state=0),
    )
    model.fit(X, y)

    metrics = evaluate(model, X_test, y_test)
    metrics["train_samples"] = int(len(y))
    metrics["test_samples"] = int(len(y_test))

    os.makedirs(os.path.dirname(os.path.abspath(args.model)), exist_ok=True)
    joblib.dump(model, args.model)
    os.makedirs(os.path.dirname(os.path.abspath(args.metrics_out)), exist_ok=True)
    with open(args.metrics_out, "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    print(f"璁粌鏍锋湰 {len(y)}锛屾祴璇曟牱鏈?{len(y_test)}")
    print(f"accuracy={metrics['accuracy']:.4f} macro_f1={metrics['macro_f1']:.4f}")
    for label, recall in metrics["per_class_recall"].items():
        print(f"  recall[{label}]={recall:.4f}")
    print(f"妯″瀷宸蹭繚瀛? {args.model}")
    print(f"鎸囨爣宸蹭繚瀛? {args.metrics_out}")


if __name__ == "__main__":
    main()




