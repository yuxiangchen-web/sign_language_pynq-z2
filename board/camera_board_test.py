"""Check camera capabilities on a board or host."""
import argparse, json, time
from pathlib import Path
import cv2

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--camera",type=int,default=0); ap.add_argument("--frames",type=int,default=100); ap.add_argument("--output",default="report/camera_board_test.json"); args=ap.parse_args()
    cap=cv2.VideoCapture(args.camera)
    if not cap.isOpened(): raise SystemExit(f"camera {args.camera} unavailable")
    w=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); h=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)); fps=cap.get(cv2.CAP_PROP_FPS)
    n=0; t=time.perf_counter()
    for _ in range(args.frames):
        ok,_=cap.read(); n += int(ok)
    elapsed=time.perf_counter()-t; cap.release()
    result={"camera":args.camera,"width":w,"height":h,"reported_fps":fps,"frames_ok":n,"measured_fps":n/elapsed if elapsed else 0}
    p=Path(args.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(result,indent=2),encoding="utf-8"); print(json.dumps(result,indent=2))
if __name__=="__main__": main()
