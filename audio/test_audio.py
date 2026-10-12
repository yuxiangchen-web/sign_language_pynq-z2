"""独立音频资产检查；加 --play 才调用真实扬声器。"""

import argparse
import json

from audio.play_audio import play_wav_for_label
from audio.speech_map import DEFAULT_AUDIO_DIR, SPEECH_MAP, inspect_wav, wav_path_for_label


def check_audio(audio_dir=None, play=False, backend="auto", device=None):
    records = []
    for label in SPEECH_MAP:
        try:
            info = inspect_wav(wav_path_for_label(label, audio_dir))
            if play:
                play_wav_for_label(label, audio_dir, backend, device)
            records.append({"label": label, "status": "played" if play else "validated", **info})
        except Exception as exc:
            records.append({"label": label, "status": "failed", "error": str(exc)})
    return {"mode": "hardware_audio" if play else "file_validation",
            "passed": all(item["status"] != "failed" for item in records), "files": records}


def main():
    ap = argparse.ArgumentParser(description="检查或播放全部中文词汇")
    ap.add_argument("--audio-dir", default=str(DEFAULT_AUDIO_DIR))
    ap.add_argument("--play", action="store_true")
    ap.add_argument("--backend", choices=("auto", "aplay", "ffplay", "winsound"), default="auto")
    ap.add_argument("--device")
    ap.add_argument("--log")
    args = ap.parse_args()
    result = check_audio(args.audio_dir, args.play, args.backend, args.device)
    if args.log:
        from board.run_log import write_json
        write_json(args.log, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
