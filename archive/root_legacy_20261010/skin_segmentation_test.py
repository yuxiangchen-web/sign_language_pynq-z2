from pathlib import Path
import cv2
import numpy as np

project_dir = Path(__file__).resolve().parent
image_path = project_dir / "dataset/raw/palm/palm_002.jpg"

image = cv2.imread(str(image_path))
if image is None:
    raise FileNotFoundError(f"无法读取：{image_path}")

if image.shape[1] > 800:
    scale = 800 / image.shape[1]
    image = cv2.resize(image, None, fx=scale, fy=scale)

blurred = cv2.GaussianBlur(image, (5, 5), 0)

# 分别转换到 YCrCb 和 HSV 色彩空间
ycrcb = cv2.cvtColor(blurred, cv2.COLOR_BGR2YCrCb)
hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

# 初始肤色范围，后续使用自己的摄像头时还会重新调整
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

# 两种判断同时满足，减少木纹背景干扰
skin_mask = cv2.bitwise_and(ycrcb_mask, hsv_mask)

kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
skin_mask = cv2.morphologyEx(
    skin_mask, cv2.MORPH_OPEN, kernel, iterations=1
)
skin_mask = cv2.morphologyEx(
    skin_mask, cv2.MORPH_CLOSE, kernel, iterations=3
)

contours, _ = cv2.findContours(
    skin_mask,
    cv2.RETR_EXTERNAL,
    cv2.CHAIN_APPROX_SIMPLE
)

if not contours:
    raise RuntimeError("没有检测到肤色区域")

largest = max(contours, key=cv2.contourArea)
x, y, width, height = cv2.boundingRect(largest)

result = image.copy()
cv2.drawContours(result, [largest], -1, (0, 0, 255), 2)
cv2.rectangle(
    result,
    (x, y),
    (x + width, y + height),
    (0, 255, 0),
    2
)

output_dir = project_dir / "outputs/skin_test"
output_dir.mkdir(parents=True, exist_ok=True)

# 根据绿色框裁剪手部
roi_color = image[y:y + height, x:x + width]
roi_mask = skin_mask[y:y + height, x:x + width]


def square_and_resize(source, size=128):
    roi_height, roi_width = source.shape[:2]
    side = max(roi_height, roi_width)

    top = (side - roi_height) // 2
    bottom = side - roi_height - top
    left = (side - roi_width) // 2
    right = side - roi_width - left

    square = cv2.copyMakeBorder(
        source,
        top,
        bottom,
        left,
        right,
        cv2.BORDER_CONSTANT,
        value=0
    )

    interpolation = (
        cv2.INTER_NEAREST
        if source.ndim == 2
        else cv2.INTER_AREA
    )

    return cv2.resize(
        square,
        (size, size),
        interpolation=interpolation
    )


roi_color_128 = square_and_resize(roi_color)
roi_mask_128 = square_and_resize(roi_mask)

cv2.imwrite(
    str(output_dir / "hand_color_128.png"),
    roi_color_128
)
cv2.imwrite(
    str(output_dir / "hand_mask_128.png"),
    roi_mask_128
)
cv2.imwrite(str(output_dir / "skin_mask.png"), skin_mask)
cv2.imwrite(str(output_dir / "skin_contour.png"), result)

print("肤色分割完成")
print("轮廓面积：", cv2.contourArea(largest))
print(f"结果目录：{output_dir}")