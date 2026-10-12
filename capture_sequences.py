"""Capture labeled dynamic gesture videos and frame metadata."""
from pathlib import Path
from datetime import datetime
import argparse, csv, time
import cv2

LABEL_KEYS = {str(i): f"number_{i}" for i in range(1, 6)}
LABEL_KEYS["6"] = "unknown"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--camera", type=int, default=1)
    ap.add_argument("--output", default="dataset/raw_dynamic_v1")
    ap.add_argument("--collector", default="A")
    ap.add_argument("--background", default="indoor_wall")
    ap.add_argument("--lighting", default="room_light")
    ap.add_argument("--distance-cm", type=float, default=60)
    ap.add_argument("--fps", type=float, default=20)
    args = ap.parse_args()
    root = Path(args.output); root.mkdir(parents=True, exist_ok=True)
    manifest = root / "dynamic_metadata.csv"
    cap = cv2.VideoCapture(args.camera, cv2.CAP_DSHOW)
    if not cap.isOpened(): raise RuntimeError(f"无法打开摄像头 {args.camera}")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640); cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    if not manifest.exists():
        with manifest.open("w", newline="", encoding="utf-8-sig") as f:
            csv.writer(f).writerow(["filename","label","timestamp","collector","background","lighting","distance_cm","batch_id","fps","frame_count","width","height"])
    print("按 1-5 选择数字手势，6=unknown；按 q 退出；每次按键录制 3 秒")
    try:
        while True:
            ok, frame = cap.read()
            if not ok: break
            cv2.putText(frame, "1-6 record 3s | Q exit", (15, 30), 0, .7, (0,255,0), 2)
            cv2.imshow("Dynamic Capture", frame); key = cv2.waitKey(1) & 0xff
            if key in (ord('q'), ord('Q'), 27): break
            label = LABEL_KEYS.get(chr(key))
            if not label: continue
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f"); batch = f"dynamic_{stamp}"
            out = root / label / f"{label}_{stamp}.avi"; out.parent.mkdir(parents=True, exist_ok=True)
            writer = cv2.VideoWriter(str(out), cv2.VideoWriter_fourcc(*"MJPG"), args.fps, (640,480))
            count=0; start=time.time()
            while time.time()-start < 3.0:
                ok, frame = cap.read()
                if not ok: break
                writer.write(frame); count += 1
                cv2.imshow("Recording", frame)
                if cv2.waitKey(1) & 0xff in (27, ord('q')): break
            writer.release()
            if count:
                with manifest.open("a", newline="", encoding="utf-8-sig") as f:
                    csv.writer(f).writerow([out.name,label,stamp,args.collector,args.background,args.lighting,args.distance_cm,batch,args.fps,count,640,480])
                print(f"已保存 {out}，{count} 帧")
    finally:
        cap.release(); cv2.destroyAllWindows()
if __name__ == "__main__": main()
