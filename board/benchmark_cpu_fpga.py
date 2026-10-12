"""Measure CPU predictor throughput; FPGA path is enabled when a PYNQ overlay adapter is supplied."""
import argparse,time,json
from pathlib import Path
import cv2
sys_path=Path(__file__).resolve().parents[1]
import sys; sys.path.insert(0,str(sys_path))
from predictor import RealtimeSignPredictor

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--input",required=True); ap.add_argument("--frames",type=int,default=100); ap.add_argument("--output",default="report/benchmark_cpu_fpga.json"); args=ap.parse_args()
    img=cv2.imread(args.input)
    if img is None: raise SystemExit(f"无法读取 {args.input}")
    rt=RealtimeSignPredictor(); t=time.perf_counter()
    for _ in range(args.frames): rt.predict_static(img)
    elapsed=time.perf_counter()-t; result={"mode":"cpu_predictor","input":args.input,"frames":args.frames,"elapsed_s":elapsed,"fps":args.frames/elapsed if elapsed else 0,"fpga":"未连接板卡，待 PYNQ 实测"}
    p=Path(args.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8"); print(json.dumps(result,indent=2,ensure_ascii=False))
if __name__=="__main__": main()
