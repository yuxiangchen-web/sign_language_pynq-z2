"""Check optional PYNQ runtime and required overlay files."""
import argparse, json
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--overlay",default="board/overlays/sign_preprocess_2026_1"); args=ap.parse_args(); p=Path(args.overlay)
    result={"overlay_dir":str(p),"exists":p.exists(),"files":sorted(x.name for x in p.glob("*")) if p.exists() else []}
    try:
        import pynq; result["pynq_version"]=getattr(pynq,"__version__","unknown")
    except Exception as e: result["pynq_import_error"]=str(e)
    try:
        import cv2; result["opencv_version"]=cv2.__version__
    except Exception as e: result["opencv_import_error"]=str(e)
    print(json.dumps(result,indent=2,ensure_ascii=False))
if __name__=="__main__": main()
