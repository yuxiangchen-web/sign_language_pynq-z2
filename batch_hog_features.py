import argparse, os, cv2, numpy as np
from feature_utils import hog_feature
from labels import STATIC_LABELS
IMG_EXTS=(".jpg",".jpeg",".png",".bmp")
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input',required=True); ap.add_argument('--output',required=True); a=ap.parse_args()
    features=[]; labels=[]; files=[]
    for label in sorted(os.listdir(a.input)):
        d=os.path.join(a.input,label)
        if not os.path.isdir(d) or label not in STATIC_LABELS: continue
        for name in sorted(os.listdir(d)):
            if not name.lower().endswith(IMG_EXTS): continue
            img=cv2.imread(os.path.join(d,name),cv2.IMREAD_GRAYSCALE)
            if img is None: continue
            binary=cv2.resize((img>0).astype(np.uint8)*255,(128,128),interpolation=cv2.INTER_NEAREST)
            features.append(hog_feature(binary)); labels.append(label); files.append(f'{label}/{name}')
    if not features: raise SystemExit('no features extracted')
    os.makedirs(os.path.dirname(os.path.abspath(a.output)),exist_ok=True)
    np.savez_compressed(a.output,X=np.stack(features).astype(np.float32),y=np.array(labels),files=np.array(files)); print(f'saved {len(features)} features to {a.output}')
if __name__=='__main__': main()
