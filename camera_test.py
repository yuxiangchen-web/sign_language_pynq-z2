import cv2

CAMERA_INDEX = 1

camera = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)

if not camera.isOpened():
    raise RuntimeError(
        f"无法打开编号 {CAMERA_INDEX} 的摄像头"
    )

camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

print("摄像头已打开，按 Q 退出")

while True:
    ok, frame = camera.read()

    if not ok:
        print("读取画面失败")
        break

    cv2.imshow("Camera Test - Press Q to Exit", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()