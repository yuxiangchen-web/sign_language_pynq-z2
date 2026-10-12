from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
RAW_DIR = PROJECT_DIR / "dataset" / "raw_static_v1"
METADATA_PATH = RAW_DIR / "static_metadata.csv"
MANIFEST_PATH = PROJECT_DIR / "dataset" / "static_manifest.csv"

EXPECTED_LABELS = {
    "number_1",
    "number_2",
    "number_3",
    "number_4",
    "number_5",
    "unknown",
}

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def load_metadata() -> list[dict[str, str]]:
    if not METADATA_PATH.exists():
        raise FileNotFoundError(
            f"找不到元数据文件：{METADATA_PATH}"
        )

    with METADATA_PATH.open(
        "r",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        return list(csv.DictReader(file))


def collect_images() -> list[Path]:
    if not RAW_DIR.exists():
        raise FileNotFoundError(
            f"找不到原始数据目录：{RAW_DIR}"
        )

    return sorted(
        path
        for path in RAW_DIR.rglob("*")
        if path.is_file()
        and path.suffix.lower() in IMAGE_EXTENSIONS
        and path.name != METADATA_PATH.name
    )


def build_manifest() -> int:
    rows = load_metadata()
    images = collect_images()

    images_by_name: dict[str, list[Path]] = {}
    for image_path in images:
        images_by_name.setdefault(image_path.name, []).append(image_path)

    manifest_rows: list[dict[str, str]] = []
    used_names: set[str] = set()
    warnings: list[str] = []

    for row_number, row in enumerate(rows, start=2):
        filename = row.get("filename", "").strip()
        label = row.get("label", "").strip()

        if not filename:
            warnings.append(f"第 {row_number} 行缺少 filename")
            continue

        if label not in EXPECTED_LABELS:
            warnings.append(
                f"第 {row_number} 行存在未知标签：{label}"
            )
            continue

        candidates = images_by_name.get(filename, [])

        if not candidates:
            warnings.append(
                f"CSV 有记录但图片不存在：{filename}"
            )
            continue

        if len(candidates) > 1:
            warnings.append(
                f"图片文件名重复，无法唯一定位：{filename}"
            )
            continue

        image_path = candidates[0]
        relative_path = image_path.relative_to(PROJECT_DIR).as_posix()

        manifest_rows.append({
            "relative_path": relative_path,
            "filename": filename,
            "label": label,
            "timestamp": row.get("timestamp", "").strip(),
            "collector": row.get("collector", "").strip(),
            "background": row.get("background", "").strip(),
            "lighting": row.get("lighting", "").strip(),
            "distance_cm": row.get("distance_cm", "").strip(),
            "batch_id": row.get("batch_id", "").strip(),
            "split": row.get("split", "").strip(),
            "width": row.get("width", "").strip(),
            "height": row.get("height", "").strip(),
        })

        used_names.add(filename)

    for image_path in images:
        if image_path.name not in used_names:
            warnings.append(
                f"图片没有元数据：{image_path.relative_to(PROJECT_DIR).as_posix()}"
            )

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "relative_path",
        "filename",
        "label",
        "timestamp",
        "collector",
        "background",
        "lighting",
        "distance_cm",
        "batch_id",
        "split",
        "width",
        "height",
    ]

    with MANIFEST_PATH.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(manifest_rows)

    print(f"图片文件数量：{len(images)}")
    print(f"CSV 元数据行数：{len(rows)}")
    print(f"有效 manifest 行数：{len(manifest_rows)}")
    print(f"manifest 输出：{MANIFEST_PATH}")

    print("\n类别统计：")
    counts = Counter(row["label"] for row in manifest_rows)

    for label in sorted(EXPECTED_LABELS):
        print(f"{label}: {counts.get(label, 0)}")

    if warnings:
        print("\n警告：")
        for warning in warnings:
            print(f"- {warning}")
    else:
        print("\n没有发现图片和元数据不一致。")

    return 0


if __name__ == "__main__":
    raise SystemExit(build_manifest())