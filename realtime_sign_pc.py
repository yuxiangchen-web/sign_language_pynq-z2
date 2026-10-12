import argparse, cv2, json, os
from audio.play_audio import play_wav_for_label
from predictor import RealtimeSignPredictor


def build_audio_player(enabled):
    return play_wav_for_label if enabled else None

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input',required=True); ap.add_argument('--mode',choices=('auto','static','dynamic'),default='auto'); ap.add_argument('--config',default='models/config.json'); ap.add_argument('--static-model',default='models/static_model.joblib'); ap.add_argument('--dynamic-model',default='models/dynamic_model.joblib'); a=ap.parse_args()
    rt=RealtimeSignPredictor(config=a.config,static_model_path=a.static_model,dynamic_model_path=a.dynamic_model)
    if a.mode=='static' or (a.mode=='auto' and os.path.isfile(a.input) and not a.input.lower().endswith(('.avi','.mp4','.mov','.mkv'))):
        img=cv2.imread(a.input)
        if img is None: raise SystemExit('cannot read input image')
        print(json.dumps(rt.predict_static(img),ensure_ascii=False)); return
    cap=cv2.VideoCapture(a.input); frames=[]
    while True:
        ok,frame=cap.read()
        if not ok: break
        frames.append(frame)
    cap.release()
    if len(frames)<2: raise SystemExit('not enough frames')
    print(json.dumps(rt.predict_sequence(frames),ensure_ascii=False))
if __name__=='__main__': main()
