"""手工标签/真实预测 JSONL 的音频触发联调；可先只验证文件和结果结构。"""

import argparse
import json

from audio.play_audio import AudioAnnouncer, play_wav
from audio.speech_map import DEFAULT_AUDIO_DIR, inspect_wav, validate_result, wav_path_for_label
from board.run_log import write_json
from labels import ALL_LABELS, DYNAMIC_LABELS, STATIC_KIND, DYNAMIC_KIND, make_result


def run_audio_test(results, audio_dir=None, validate_only=False, backend="auto", device=None):
    checked = [validate_result(result) for result in results]
    if not checked:
        raise ValueError("音频测试结果序列为空")
    if validate_only:
        records = []
        for result in checked:
            path = wav_path_for_label(result["label"], audio_dir)
            records.append({"label": result["label"], "status": "unknown" if path is None else "validated",
                            "wav": None if path is None else inspect_wav(path)})
        return {"mode": "offline_audio_mapping", "passed": True, "playback_executed": False,
                "results": records}
    with AudioAnnouncer(audio_dir, player=lambda path: play_wav(path, backend, device=device)) as announcer:
        records = [announcer.submit(result) for result in checked]
    events = announcer.poll_events()
    return {"mode": "hardware_audio", "passed": all(e["status"] != "failed" for e in events),
            "playback_executed": bool(events), "results": records, "events": events}


def main():
    ap = argparse.ArgumentParser(description="板端音频触发测试")
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--results", help="B 的统一预测结果 JSONL 文件")
    group.add_argument("--label", choices=ALL_LABELS, help="手工触发，不代表模型识别结果")
    ap.add_argument("--audio-dir", default=str(DEFAULT_AUDIO_DIR))
    ap.add_argument("--validate-only", action="store_true")
    ap.add_argument("--backend", choices=("auto", "aplay", "ffplay", "winsound"), default="auto")
    ap.add_argument("--device")
    ap.add_argument("--log", default="board/logs/audio.json")
    args = ap.parse_args()
    mode = "offline_audio_mapping" if args.validate_only else "hardware_audio"
    try:
        if args.results:
            with open(args.results, encoding="utf-8") as stream:
                results = [json.loads(line) for line in stream if line.strip()]
        else:
            kind = DYNAMIC_KIND if args.label in DYNAMIC_LABELS else STATIC_KIND
            results = [make_result(args.label, 1.0, kind)]
        result = run_audio_test(results, args.audio_dir, args.validate_only, args.backend, args.device)
        result["input_source"] = "predictor_jsonl" if args.results else "manual_label"
    except Exception as exc:
        result = {"mode": mode, "passed": False, "error": f"{type(exc).__name__}: {exc}"}
    write_json(args.log, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
