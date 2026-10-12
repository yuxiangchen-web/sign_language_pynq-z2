from pathlib import Path
import sys

import numpy as np
from PIL import Image


WIDTH = 360
HEIGHT = 360

INPUT_ROOT = Path("dataset/raw_static_v1")
OUTPUT_ROOT = Path("dataset/processed_static_v1")


def rgb_to_ycrcb(rgb):
    r = rgb[..., 0].astype(np.int32)
    g = rgb[..., 1].astype(np.int32)
    b = rgb[..., 2].astype(np.int32)

    y = (77 * r + 150 * g + 29 * b) >> 8
    cr = ((131 * r - 110 * g - 21 * b) >> 8) + 128
    cb = ((-43 * r - 85 * g + 128 * b) >> 8) + 128

    return (
        np.clip(y, 0, 255),
        np.clip(cr, 0, 255),
        np.clip(cb, 0, 255),
    )


def make_mask(image):
    y, cr, cb = rgb_to_ycrcb(image)

    mask = (
        (y >= 45) & (y <= 225) &
        (cr >= 135) & (cr <= 190) &
        (cb >= 80) & (cb <= 145)
    )

    return np.where(mask, 255, 0).astype(np.uint8)


def main():
    files = sorted(INPUT_ROOT.glob("number_*/*.jpg"))

    if not files:
        print(f"没有找到图片：{INPUT_ROOT}")
        sys.exit(1)

    for index, source_path in enumerate(files, start=1):
        relative_path = source_path.relative_to(INPUT_ROOT)
        target_path = OUTPUT_ROOT / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)

        image = Image.open(source_path).convert("RGB")
        image = image.resize((WIDTH, HEIGHT))

        rgb = np.array(image, dtype=np.uint8)
        mask = make_mask(rgb)

        Image.fromarray(mask, mode="L").save(target_path)

        if index % 50 == 0 or index == len(files):
            print(f"{index}/{len(files)} 已处理")

    print("批量处理完成")
    print(f"输出目录：{OUTPUT_ROOT}")


if __name__ == "__main__":
    main()