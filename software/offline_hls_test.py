from PIL import Image
import sys

import numpy as np
from pathlib import Path


WIDTH = 360
HEIGHT = 360


def clamp_u8(value):
    return np.clip(value, 0, 255).astype(np.uint8)


def rgb_to_ycrcb(rgb):
    r = rgb[..., 0].astype(np.int32)
    g = rgb[..., 1].astype(np.int32)
    b = rgb[..., 2].astype(np.int32)

    y = (77 * r + 150 * g + 29 * b) >> 8
    cr = ((131 * r - 110 * g - 21 * b) >> 8) + 128
    cb = ((-43 * r - 85 * g + 128 * b) >> 8) + 128

    return clamp_u8(y), clamp_u8(cr), clamp_u8(cb)


def image_preprocess_offline(rgb):
    y, cr, cb = rgb_to_ycrcb(rgb)

    mask = (
        (y >= 45) & (y <= 225) &
        (cr >= 135) & (cr <= 190) &
        (cb >= 80) & (cb <= 145)
    )

    return np.where(mask, 255, 0).astype(np.uint8)


def main():
    if len(sys.argv) != 2:
        print("用法: python offline_hls_test.py 图片路径")
        return

    image_path = Path(sys.argv[1])

    image = Image.open(image_path).convert("RGB")
    image = image.resize((WIDTH, HEIGHT))

    rgb = np.array(image, dtype=np.uint8)
    output = image_preprocess_offline(rgb)

    output_path = Path(__file__).with_name("real_mask.npy")
    np.save(output_path, output)
    mask_png = Path(__file__).with_name("real_mask.png")
    Image.fromarray(output).save(mask_png)
    print(f"Saved: {output_path}")
    print(f"Saved PNG: {mask_png}")

    print("Real image test passed.")
    print(f"Input: {image_path}")
    print(f"Input shape: {rgb.shape}")
    print(f"Foreground pixels: {np.count_nonzero(output == 255)}")
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()

    from PIL import Image

