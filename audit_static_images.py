import argparse
import csv
import shutil
from datetime import datetime
from pathlib import Path

import cv2

from preprocess import preprocess_frame

VALID_EXTS = {".jpg", ".jpeg", ".png"}


def audit_image(path):
    frame = cv2.imread(str(path))
    if frame is None:
        return False, "cannot_read", {}

    binary, info = preprocess_frame(frame)

    if not info.get("hand_found", False):
        return False, "no_hand", info

    area = info.get("area", 0)
    if area < 2500:
        return False, "area_too_small", info

    # For raw training images, large area and edge contact are warnings only.
    # Rejecting them would remove most close-up hand samples from this dataset.
    return True, "ok", info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="dataset/raw_static_v1")
    ap.add_argument("--reject-dir", default=None)
    ap.add_argument("--move", action="store_true")
    args = ap.parse_args()

    root = Path(args.input)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    reject_root = Path(args.reject_dir or f"dataset/rejected_static_{stamp}")
    report_path = Path("report") / f"static_image_audit_{stamp}.csv"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    total = ok_count = reject_count = 0

    for path in sorted(root.rglob("*")):
        if path.suffix.lower() not in VALID_EXTS:
            continue

        total += 1
        ok, reason, info = audit_image(path)

        rows.append({
            "path": str(path),
            "class": path.parent.name,
            "ok": ok,
            "reason": reason,
            "area": info.get("area"),
            "bbox": info.get("bbox"),
            "touches_edge": info.get("touches_edge"),
            "hand_found": info.get("hand_found"),
        })

        if ok:
            ok_count += 1
        else:
            reject_count += 1
            if args.move:
                rel = path.relative_to(root)
                dst = reject_root / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(path), str(dst))

    with report_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "path", "class", "ok", "reason", "area", "bbox", "touches_edge", "hand_found"
        ])
        writer.writeheader()
        writer.writerows(rows)

    print("total:", total)
    print("ok:", ok_count)
    print("rejected:", reject_count)
    print("report:", report_path)
    if args.move:
        print("moved_to:", reject_root)
    else:
        print("dry_run only, no files moved")

if __name__ == "__main__":
    main()

