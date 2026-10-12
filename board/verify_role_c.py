"""一条命令复现当前计划的离线验证；可同时审计旧版根目录测试。"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from board.run_log import write_json


def main():
    ap = argparse.ArgumentParser(description="角色 C 离线交付检查")
    ap.add_argument("--include-legacy", action="store_true", help="加入旧版根目录测试，保留其真实失败")
    ap.add_argument("--log-dir", default="report/role_c_logs/reproduce")
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[1]
    logs = Path(args.log_dir).resolve()
    logs.mkdir(parents=True, exist_ok=True)
    python = sys.executable
    pytest_args = [python, "-m", "pytest", "tests", "--import-mode=importlib", "-q",
                   "--basetemp=" + str(root / ".role_c_tmp" / ("verify_" + str(os.getpid()))),
                   "--junitxml=" + str(logs / "tests.xml")]
    if args.include_legacy:
        legacy = root / "archive" / "root_legacy_20261010"
        pytest_args += [str(legacy / "test_preprocess.py"), str(legacy / "test_predictor.py")]
    bit = "board/overlays/led_test_2026_1/led_test_2026_1.bit"
    steps = [
        ("python_compile", [python, "-m", "compileall", "-q", "audio", "board", "tests"]),
        ("automated_tests", pytest_args),
        ("audio_assets", [python, "-m", "audio.test_audio", "--log", str(logs / "audio.json")]),
        ("gpio_metadata", [python, "-m", "board.overlay_register_test", "--inspect",
                           "--log", str(logs / "gpio.json")]),
        ("dma_metadata", [python, "-m", "board.dma_board_test", "--bit", bit, "--inspect",
                          "--log", str(logs / "dma.json")]),
        ("audio_mapping", [python, "-m", "board.audio_board_test", "--label", "hello",
                           "--validate-only", "--log", str(logs / "trigger.json")]),
        ("dependency_check", [python, "-m", "pip", "check"]),
    ]
    records = []
    env = dict(os.environ, PYTHONUTF8="1")
    for name, command in steps:
        result = subprocess.run(command, cwd=root, env=env, capture_output=True,
                                text=True, encoding="utf-8", errors="replace")
        path = logs / (name + ".txt")
        path.write_text(result.stdout + result.stderr, encoding="utf-8")
        records.append({"name": name, "command": command, "exit_code": result.returncode,
                        "passed": result.returncode == 0, "log": str(path)})
        print(f"{name}: {'PASS' if result.returncode == 0 else 'FAIL'} (exit={result.returncode})")
    snapshot = root / "report" / "role_c_logs" / "original_files.json"
    if snapshot.is_file():
        originals = json.loads(snapshot.read_text(encoding="utf-8-sig"))
        changed = [item["path"] for item in originals
                   if not (root / item["path"]).is_file()
                   or hashlib.sha256((root / item["path"]).read_bytes()).hexdigest().upper()
                   != item["sha256"]]
        records.append({"name": "original_files_unchanged", "checked": len(originals),
                        "passed": not changed, "changed": changed})
    summary = {"mode": "offline_verification", "includes_legacy": args.include_legacy,
               "passed": all(record["passed"] for record in records), "checks": records,
               "hardware_executed": False, "speaker_playback_executed": False}
    write_json(logs / "summary.json", summary)
    print("Summary: " + str(logs / "summary.json"))
    raise SystemExit(0 if summary["passed"] else 1)


if __name__ == "__main__":
    main()
