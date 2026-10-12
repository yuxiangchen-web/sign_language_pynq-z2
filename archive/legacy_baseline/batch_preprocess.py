from pathlib import Path
import cv2
import numpy as np

PROJECT_DIR = Path(__file__).resolve().parent
RAW_DIR = PROJECT_DIR / "dataset" / "raw"
OUT_DIR = PROJECT_DIR / "dataset" / "processed"

CLASSES = ["palm", "fist", "victory", "ok", "thumbs_up", "unknown"]
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}


def square_resize(image, size=128):
    h, w = image.shape[:2]
    side = max(h, w)

    top = (side - h) // 2
    bottom = side - h - top
    left = (side - w) // 2
    right = side - w - left

    padded = cv2.copyMakeBorder(
        image,
        top, bottom, left, right,
        cv2.BORDER_CONSTANT,
        value=0
    )

    return cv2.resize(
        padded,
        (size, size),
        interpolation=cv2.INTER_NEAREST
    )


def make_skin_mask(image):
    blurred = cv2.GaussianBlur(image, (5, 5), 0)

    ycrcb = cv2.cvtColor(blurred, cv2.COLOR_BGR2YCrCb)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

    ycrcb_mask = cv2.inRange(
        ycrcb,
        np.array([0, 125, 70], dtype=np.uint8),
        np.array([255, 185, 140], dtype=np.uint8)
    )

    hsv_mask = cv2.inRange(
        hsv,
        np.array([0, 25, 40], dtype=np.uint8),
        np.array([25, 255, 255], dtype=np.uint8)
    )

    mask = cv2.bitwise_and(ycrcb_mask, hsv_mask)

    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (7, 7)
    )

    mask = cv2.morphologyEx(
        mask, cv2.MORPH_OPEN, kernel, iterations=1
    )
    mask = cv2.morphologyEx(
        mask, cv2.MORPH_CLOSE, kernel, iterations=3
    )

    return mask


def process_one(image_path, output_path):
    image = cv2.imread(str(image_path))

    if image is None:
        print("读取失败：", image_path)
        return False

    if image.shape[1] > 800:
        scale = 800 / image.shape[1]
        image = cv2.resize(
            image,
            None,
            fx=scale,
            fy=scale,
            interpolation=cv2.INTER_AREA
        )

    mask = make_skin_mask(image)
    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    if contours:
        largest = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest)
        x, y, w, h = cv2.boundingRect(largest)

        # 太小的区域视为没有有效手部
        if area >= image.shape[0] * image.shape[1] * 0.01:
            roi = mask[y:y + h, x:x + w]
        else:
            roi = np.zeros((1, 1), dtype=np.uint8)
    else:
        roi = np.zeros((1, 1), dtype=np.uint8)

    result = square_resize(roi, 128)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), result)

    return True


total = 0
success = 0

for class_name in CLASSES:
    input_dir = RAW_DIR / class_name
    output_dir = OUT_DIR / class_name

    files = [
        p for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    ]

    print(f"\n[{class_name}] 找到 {len(files)} 张图片")

    for image_path in files:
        output_path = output_dir / f"{image_path.stem}_mask.png"

        if process_one(image_path, output_path):
            success += 1

        total += 1

print("\n批量预处理完成")
print(f"总图片数：{total}")
print(f"成功输出：{success}")
print(f"输出目录：{OUT_DIR}")