from pathlib import Path
import cv2
import numpy as np

project_dir = Path(__file__).resolve().parent
image_path = (
    project_dir
    / "dataset"
    / "raw"
    / "palm"
    / "palm_001.jpg"
)

image = cv2.imread(str(image_path))
if image is None:
    raise FileNotFoundError(f"图片读取失败：{image_path}")

# 图片太大时缩小，方便后续处理
if image.shape[1] > 800:
    scale = 800 / image.shape[1]
    image = cv2.resize(image, None, fx=scale, fy=scale)

gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (5, 5), 0)

_, binary = cv2.threshold(
    blurred, 0, 255,
    cv2.THRESH_BINARY + cv2.THRESH_OTSU
)

# 让目标区域保持白色
if cv2.countNonZero(binary) > binary.size / 2:
    binary = cv2.bitwise_not(binary)

kernel = np.ones((5, 5), dtype=np.uint8)
cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel)

contours, _ = cv2.findContours(
    cleaned,
    cv2.RETR_EXTERNAL,
    cv2.CHAIN_APPROX_SIMPLE
)

result = image.copy()

if contours:
    largest = max(contours, key=cv2.contourArea)
    x, y, width, height = cv2.boundingRect(largest)

    cv2.drawContours(result, [largest], -1, (0, 0, 255), 2)
    cv2.rectangle(
        result,
        (x, y),
        (x + width, y + height),
        (0, 255, 0),
        2
    )

output_dir = project_dir / "outputs" / "real_hand_test"
output_dir.mkdir(parents=True, exist_ok=True)

cv2.imwrite(str(output_dir / "gray.png"), gray)
cv2.imwrite(str(output_dir / "binary.png"), binary)
cv2.imwrite(str(output_dir / "cleaned.png"), cleaned)
cv2.imwrite(str(output_dir / "contour.png"), result)

print("处理完成")
print(f"结果目录：{output_dir}")