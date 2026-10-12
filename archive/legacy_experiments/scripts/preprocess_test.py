import cv2

image = cv2.imread("test_output.png")

if image is None:
    print("找不到 test_output.png")
    raise SystemExit

gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

cv2.imwrite("gray_output.png", gray)

print("灰度图已保存为 gray_output.png")