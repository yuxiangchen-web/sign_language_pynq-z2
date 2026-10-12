import cv2
import numpy as np

image = np.zeros((480, 640, 3), dtype=np.uint8)

cv2.rectangle(
    image,
    (180, 120),
    (460, 360),
    (255, 0, 0),
    -1
)

cv2.putText(
    image,
    "OpenCV Test",
    (190, 250),
    cv2.FONT_HERSHEY_SIMPLEX,
    1.2,
    (255, 255, 255),
    2
)

cv2.imwrite("test_output.png", image)

print("图片已保存为 test_output.png")