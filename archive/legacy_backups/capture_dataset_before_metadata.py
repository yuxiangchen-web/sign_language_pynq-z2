from pathlib import Path
from datetime import datetime
import cv2

PROJECT_DIR = Path(__file__).resolve().parent
RAW_DIR = PROJECT_DIR / "dataset" / "raw_static_v1"
CAMERA_INDEX = 1

CLASS_KEYS = {
    ord("1"): "number_1",
    ord("2"): "number_2",
    ord("3"): "number_3",
    ord("4"): "number_4",
    ord("5"): "number_5",
    ord("6"): "unknown",
}

camera = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)

if not camera.isOpened():
    raise RuntimeError("无法打开外接摄像头")

camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

for class_name in CLASS_KEYS.values():
    (RAW_DIR / class_name).mkdir(parents=True, exist_ok=True)

print("1=number_1  2=number_2  3=number_3")
print("4=number_4  5=number_5  6=unknown")
print("Q 或 Esc：退出")

while True:
    ok, frame = camera.read()
    if not ok:
        print("读取画面失败")
        break

    frame = cv2.flip(frame, 1)

    height, width = frame.shape[:2]
    x1, y1 = 140, 60
    x2, y2 = 500, 420
    clean_roi = frame[y1:y2, x1:x2].copy()

    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
    cv2.putText(
        frame,
        "1-6: Save    Q/ESC: Exit",
        (15, 25),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (0, 255, 0),
        2
    )

    cv2.imshow("Dataset Capture", frame)
    key = cv2.waitKey(1) & 0xFF

    if key in (ord("q"), ord("Q"), 27):
        break

    if key in CLASS_KEYS:
        class_name = CLASS_KEYS[key]
        roi = clean_roi

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        output_path = RAW_DIR / class_name / f"{class_name}_{timestamp}.jpg"

        cv2.imwrite(str(output_path), roi)
        print(f"已保存：{output_path.name}")

camera.release()
cv2.destroyAllWindows()