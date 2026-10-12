from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import cv2


PROJECT_DIR = Path(__file__).resolve().parent
MANIFEST_PATH = PROJECT_DIR / "dataset" / "static_manifest.csv"
AUDIT_DIR = PROJECT_DIR / "dataset" / "audit"
REPORT_PATH = AUDIT_DIR / "static_audit.json"

EXPECTED_LABELS = {
    "number_1",
    "number_2",
    "number_3",
    "number_4",
    "number_5",
    "unknown",
}


def read_manifest() -> list[dict[str, str]]:
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(
            f"找不到 manifest：{MANIFEST_PATH}"
        )

    with MANIFEST_PATH.open(
        "r",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        return list(csv.DictReader(file))


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)

    return digest.hexdigest()


def audit_manifest() -> dict:
    rows = read_manifest()

    result = {
        "manifest_rows": len(rows),
        "missing_files": [],
        "unreadable_files": [],
        "size_mismatches": [],
        "unknown_labels": [],
        "duplicate_files": [],
        "split_batch_conflicts": [],
        "duplicate_hashes": [],
        "label_counts": {},
        "manual_review": [],
        "passed": True,
    }

    label_counts = Counter()
    hash_to_files = defaultdict(list)
    batch_to_splits = defaultdict(set)

    for row_number, row in enumerate(rows, start=2):
        relative_path = row.get("relative_path", "").strip()
        label = row.get("label", "").strip()
        split = row.get("split", "").strip()
        batch_id = row.get("batch_id", "").strip()

        if label not in EXPECTED_LABELS:
            result["unknown_labels"].append({
                "row": row_number,
                "label": label,
                "file": relative_path,
            })
            continue

        label_counts[label] += 1

        if batch_id and split:
            batch_to_splits[batch_id].add(split)

        image_path = PROJECT_DIR / relative_path

        if not image_path.exists():
            result["missing_files"].append(relative_path)
            continue

        image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)

        if image is None:
            result["unreadable_files"].append(relative_path)
            continue

        actual_height, actual_width = image.shape[:2]

        try:
            expected_width = int(row.get("width", "0"))
            expected_height = int(row.get("height", "0"))
        except ValueError:
            expected_width = 0
            expected_height = 0

        if (
            expected_width != actual_width
            or expected_height != actual_height
        ):
            result["size_mismatches"].append({
                "file": relative_path,
                "recorded": [
                    expected_width,
                    expected_height,
                ],
                "actual": [
                    actual_width,
                    actual_height,
                ],
            })

        digest = file_hash(image_path)
        hash_to_files[digest].append(relative_path)

        # 这里只做提示，不自动判定手是否出框。
        # 因为原始图片是彩色 ROI，是否出框需要人工查看。
        result["manual_review"].append({
            "file": relative_path,
            "label": label,
            "checks": [
                "手指是否完整",
                "手部是否接触图像边缘",
                "标签是否与动作一致",
                "unknown 是否确实为非目标手势",
            ],
        })

    for digest, paths in hash_to_files.items():
        if len(paths) > 1:
            result["duplicate_hashes"].append({
                "sha256": digest,
                "files": paths,
            })

    for batch_id, splits in batch_to_splits.items():
        if len(splits) > 1:
            result["split_batch_conflicts"].append({
                "batch_id": batch_id,
                "splits": sorted(splits),
            })

    result["label_counts"] = {
        label: label_counts.get(label, 0)
        for label in sorted(EXPECTED_LABELS)
    }

    result["duplicate_files"] = [
        item
        for item in result["duplicate_hashes"]
    ]

    critical_keys = [
        "missing_files",
        "unreadable_files",
        "size_mismatches",
        "unknown_labels",
        "split_batch_conflicts",
        "duplicate_hashes",
    ]

    result["passed"] = not any(
        result[key]
        for key in critical_keys
    )

    return result


def main() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)

    result = audit_manifest()

    with REPORT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            result,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print(f"manifest 行数：{result['manifest_rows']}")
    print(f"审计报告：{REPORT_PATH}")

    print("\n类别数量：")
    for label, count in result["label_counts"].items():
        print(f"{label}: {count}")

    print("\n检查结果：")
    print(f"缺失文件：{len(result['missing_files'])}")
    print(f"损坏文件：{len(result['unreadable_files'])}")
    print(f"尺寸不匹配：{len(result['size_mismatches'])}")
    print(f"未知标签：{len(result['unknown_labels'])}")
    print(f"重复文件：{len(result['duplicate_hashes'])}")
    print(f"批次划分冲突：{len(result['split_batch_conflicts'])}")
    print(f"需要人工查看：{len(result['manual_review'])}")

    if result["passed"]:
        print("\n自动审计通过。")
    else:
        print("\n自动审计未通过，请查看 JSON 报告。")

    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())