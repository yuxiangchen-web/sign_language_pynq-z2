import argparse
import json
import time
from pathlib import Path

import cv2

from board_static_infer import NumpyStaticPredictor


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="models/static_numpy_model.npz")
    ap.add_argument("--camera", default="/dev/video0")
    ap.add_argument("--interval", type=float, default=0.8)
    ap.add_argument("--output", default="report/latest_static_result.json")
    ap.add_argument("--save-frame", default="report/latest_static_frame.jpg")
    args = ap.parse_args()

    output = Path(args.output)
    save_frame = Path(args.save_frame)
    output.parent.mkdir(parents=True, exist_ok=True)
    save_frame.parent.mkdir(parents=True, exist_ok=True)

    predictor = NumpyStaticPredictor(args.model)

    cap = cv2.VideoCapture(args.camera, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

    if not cap.isOpened():
        raise SystemExit(f"camera open failed: {args.camera}")

    print("live json app started. Interrupt the kernel or press Ctrl+C to stop.")
    count = 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("camera read failed")
                time.sleep(args.interval)
                continue

            result, info = predictor.predict(frame)
            count += 1
            cv2.imwrite(str(save_frame), frame)

            payload = {
                "count": count,
                "timestamp": time.time(),
                "result": result,
                "preprocess": info,
            }
            output.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            print(
                f"[{count:04d}] label={result['label']} text={result['text']} "
                f"confidence={result['confidence']:.4f} raw={info.get('raw_label')} "
                f"edge={info.get('touches_edge')}"
            )
            time.sleep(args.interval)
    finally:
        cap.release()


if __name__ == "__main__":
    main()
