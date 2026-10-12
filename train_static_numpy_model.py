import argparse
import json
import os

import cv2
import numpy as np

from labels import STATIC_LABELS

IMG_EXTS = (".png",)


def _feature_from_binary(path):
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None
    binary = cv2.resize((img > 0).astype(np.float32), (128, 128),
                        interpolation=cv2.INTER_NEAREST)
    x = binary.reshape(-1)
    norm = np.linalg.norm(x)
    return x / (norm + 1e-8)


def train(input_dir, model_out):
    centroids = []
    labels = []
    counts = {}

    for label in STATIC_LABELS:
        label_dir = os.path.join(input_dir, label)
        if not os.path.isdir(label_dir):
            continue
        features = []
        for name in sorted(os.listdir(label_dir)):
            if not name.lower().endswith(IMG_EXTS):
                continue
            feat = _feature_from_binary(os.path.join(label_dir, name))
            if feat is not None:
                features.append(feat)
        if not features:
            continue
        centroid = np.mean(np.stack(features), axis=0)
        centroid = centroid / (np.linalg.norm(centroid) + 1e-8)
        centroids.append(centroid.astype(np.float32))
        labels.append(label)
        counts[label] = len(features)

    if not centroids:
        raise SystemExit("no training images found")

    os.makedirs(os.path.dirname(os.path.abspath(model_out)), exist_ok=True)
    np.savez_compressed(
        model_out,
        centroids=np.stack(centroids).astype(np.float32),
        labels=np.array(labels),
        counts=np.array([counts[label] for label in labels], dtype=np.int32),
    )
    return {"model": model_out, "labels": labels, "counts": counts}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="dataset/processed_static_v1")
    ap.add_argument("--model", default="models/static_numpy_model.npz")
    ap.add_argument("--summary", default="report/static_numpy_model.json")
    args = ap.parse_args()

    summary = train(args.input, args.model)
    os.makedirs(os.path.dirname(os.path.abspath(args.summary)), exist_ok=True)
    with open(args.summary, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
