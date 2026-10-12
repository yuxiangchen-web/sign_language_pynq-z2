import argparse, os, joblib, numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, recall_score
from labels import STATIC_LABELS

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--features',required=True); ap.add_argument('--model',required=True); ap.add_argument('--output',default='report/eval_static.md'); a=ap.parse_args()
    d=np.load(a.features,allow_pickle=False); y=d['y']; pred=joblib.load(a.model).predict(d['X']); labels=list(STATIC_LABELS); cm=confusion_matrix(y,pred,labels=labels); acc=accuracy_score(y,pred); f1=f1_score(y,pred,labels=labels,average='macro',zero_division=0)
    report=f'# Static evaluation\n\n- samples: {len(y)}\n- accuracy: {acc:.4f}\n- macro_f1: {f1:.4f}\n\n| label | recall |\n|---|---|\n'+'\n'.join(f'| {l} | {r:.4f} |' for l,r in zip(labels,recall_score(y,pred,labels=labels,average=None,zero_division=0)))+'\n'
    os.makedirs(os.path.dirname(os.path.abspath(a.output)),exist_ok=True); open(a.output,'w',encoding='utf-8').write(report); print(report)
if __name__=='__main__': main()
