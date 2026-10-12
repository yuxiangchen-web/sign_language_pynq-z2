from pathlib import Path
import cv2

project_dir = Path(__file__).resolve().parent

image = cv2.imread(str(project_dir / "test_output.png"))
mask = cv2.imread(
    str(project_dir / "binary_cleaned.png"),
    cv2.IMREAD_GRAYSCALE
)

if image is None or mask is None:
    raise FileNotFoundError("找不到测试图片或二值化图片")

# 保证目标为白色、背景为黑色
if cv2.countNonZero(mask) > mask.size / 2:
    mask = cv2.bitwise_not(mask)

contours, _ = cv2.findContours(
    mask,
    cv2.RETR_EXTERNAL,
    cv2.CHAIN_APPROX_SIMPLE
)

if not contours:
    raise RuntimeError("没有检测到轮廓")

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

output_path = project_dir / "contour_result.png"
cv2.imwrite(str(output_path), result)

print("最大轮廓面积：", cv2.contourArea(largest))
print("处理完成：已生成 contour_result.png")