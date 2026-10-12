"""Run B predictor with camera frames; works on host and PYNQ once models exist."""
import argparse, time, cv2
from pathlib import Path
import sys; sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from predictor import RealtimeSignPredictor

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--camera",type=int,default=0); ap.add_argument("--config",default="models/config.json"); ap.add_argument("--static-model",default="models/static_model.joblib"); args=ap.parse_args()
    rt=RealtimeSignPredictor(config=args.config, static_model_path=args.static_model); cap=cv2.VideoCapture(args.camera)
    if not cap.isOpened(): raise SystemExit("无法打开摄像头")
    try:
        while True:
            ok,frame=cap.read()
            if not ok: break
            result=rt.predict_static(frame); text=f"{result['label']} {result['confidence']:.2f}"; cv2.putText(frame,text,(20,35),0,.8,(0,255,0),2); cv2.imshow("Sign Inference",frame)
            if cv2.waitKey(1)&0xff in (27,ord('q')): break
    finally: cap.release(); cv2.destroyAllWindows()
if __name__=="__main__": main()
