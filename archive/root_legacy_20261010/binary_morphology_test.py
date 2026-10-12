from pathlib import Path
import cv2
import numpy as np

project_dir = Path(__file__).resolve().parent
image_path = project_dir / "test_output.png"

image = cv2.imread(str(image_path))
if image is None:
    raise FileNotFoundError(f"找不到图片：{image_path}")

gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# 自动选择阈值，将灰度图变为黑白图
_, binary = cv2.threshold(
    gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
)

# 开运算去除小噪点，闭运算填补小孔洞
kernel = np.ones((5, 5), dtype=np.uint8)
cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel)

cv2.imwrite(str(project_dir / "binary_raw.png"), binary)
cv2.imwrite(str(project_dir / "binary_cleaned.png"), cleaned)

print("处理完成：已生成 binary_raw.png 和 binary_cleaned.png")