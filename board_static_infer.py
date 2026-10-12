import argparse
import json

import cv2
import numpy as np

from labels import STATIC_KIND, make_result
from preprocess import preprocess_frame


class NumpyStaticPredictor:
    def __init__(
        self,
        model_path="models/static_numpy_model.npz",
        margin_threshold=0.006,
        unknown_gap_threshold=0.025,
    ):
        data = np.load(model_path, allow_pickle=False)
        self.centroids = data["centroids"].astype(np.float32)
        self.labels = data["labels"].astype(str)
        self.margin_threshold = float(margin_threshold)
        self.unknown_gap_threshold = float(unknown_gap_threshold)

    def predict(self, frame_bgr):
        binary, info = preprocess_frame(frame_bgr)
        if binary is None:
            return make_result("unknown", 1.0, STATIC_KIND), info
        x = (binary > 0).astype(np.float32).reshape(-1)
        x = x / (np.linalg.norm(x) + 1e-8)
        scores = self.centroids @ x
        order = np.argsort(scores)[::-1]
        best = int(order[0])
        second = int(order[1]) if len(order) > 1 else best
        score = float(scores[best])
        second_score = float(scores[second])
        margin = score - second_score

        raw_label = str(self.labels[best])
        final_label = raw_label

        unknown_score = None
        if "unknown" in self.labels:
            unknown_idx = int(np.where(self.labels == "unknown")[0][0])
            unknown_score = float(scores[unknown_idx])

        if raw_label != "unknown":
            if margin < self.margin_threshold:
                final_label = "unknown"
            if (unknown_score is not None
                    and score - unknown_score < self.unknown_gap_threshold):
                final_label = "unknown"

        info["raw_label"] = raw_label
        info["raw_score"] = score
        info["second_label"] = str(self.labels[second])
        info["second_score"] = second_score
        info["score_margin"] = float(margin)
        if unknown_score is not None:
            info["unknown_score"] = unknown_score

        # Map cosine similarity from [-1, 1] to a bounded confidence-like value.
        confidence = max(0.0, min(1.0, (score + 1.0) / 2.0))
        return make_result(final_label, confidence, STATIC_KIND), info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--model", default="models/static_numpy_model.npz")
    ap.add_argument("--output", default=None)
    ap.add_argument("--margin-threshold", type=float, default=0.006)
    ap.add_argument("--unknown-gap-threshold", type=float, default=0.025)
    args = ap.parse_args()

    frame = cv2.imread(args.input)
    if frame is None:
        raise SystemExit(f"cannot read input image: {args.input}")

    predictor = NumpyStaticPredictor(
        args.model,
        margin_threshold=args.margin_threshold,
        unknown_gap_threshold=args.unknown_gap_threshold,
    )
    result, info = predictor.predict(frame)
    payload = {"result": result, "preprocess": info}
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    print(text)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)


if __name__ == "__main__":
    main()
