import argparse, os, joblib, numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from labels import DYNAMIC_LABELS
from train_dynamic_model import load_dataset

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input',required=True); ap.add_argument('--model',required=True); ap.add_argument('--seq-len',type=int,default=16,choices=(16,24)); ap.add_argument('--output',default='report/eval_dynamic.md'); a=ap.parse_args()
    X,y,files=load_dataset(a.input,a.seq_len)
    if not X: raise SystemExit('no test videos')
    pred=joblib.load(a.model).predict(np.stack(X)); labels=list(DYNAMIC_LABELS); cm=confusion_matrix(y,pred,labels=labels); acc=accuracy_score(y,pred); f1=f1_score(y,pred,labels=labels,average='macro',zero_division=0)
    report=f'# Dynamic evaluation\n\n- videos: {len(y)}\n- accuracy: {acc:.4f}\n- macro_f1: {f1:.4f}\n'; os.makedirs(os.path.dirname(os.path.abspath(a.output)),exist_ok=True); open(a.output,'w',encoding='utf-8').write(report); print(report)
if __name__=='__main__': main()
