"""生成或导入真实中文语音，不用提示音或静音冒充 WAV 词汇。"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from audio.speech_map import DEFAULT_AUDIO_DIR, SPEECH_MAP, inspect_wav
from labels import LABEL_TEXT_ZH


def synthesize_windows(text, path):
    env = dict(os.environ, ROLE_C_TTS_TEXT=text, ROLE_C_TTS_OUTPUT=str(Path(path).resolve()))
    script = Path(__file__).with_name("synthesize_windows.ps1")
    executable = shutil.which("pwsh") or shutil.which("powershell.exe")
    if not executable:
        raise RuntimeError("Windows 语音生成需要 PowerShell")
    process = subprocess.run([executable, "-NoProfile", "-NonInteractive", "-File", str(script)],
                             env=env, timeout=60, capture_output=True)
    if process.returncode:
        message = process.stderr.decode("utf-8", errors="replace")
        raise RuntimeError(f"中文语音生成失败: {message}")


def synthesize_espeak(text, path):
    executable = shutil.which("espeak-ng") or shutil.which("espeak")
    if not executable:
        raise RuntimeError("需要 espeak-ng/espeak，或使用 --source-dir 导入真人录音")
    subprocess.run([executable, "-v", "cmn", "-w", str(path), text],
                   check=True, timeout=60, capture_output=True)


def prepare_audio(output_dir=None, source_dir=None, engine="auto", overwrite=False):
    output = Path(output_dir or DEFAULT_AUDIO_DIR).resolve()
    output.mkdir(parents=True, exist_ok=True)
    if engine == "auto":
        engine = "windows" if os.name == "nt" else "espeak"
    if engine not in ("windows", "espeak"):
        raise ValueError(f"未知语音引擎: {engine}")
    records = []
    for label, filename in SPEECH_MAP.items():
        target = output / filename
        origin = "existing"
        if overwrite or not target.exists():
            # 同目录临时文件 + replace，生成失败时保留原录音。
            fd, name = tempfile.mkstemp(prefix=label + "_", suffix=".wav", dir=output)
            os.close(fd)
            temporary = Path(name)
            try:
                if source_dir:
                    shutil.copyfile(Path(source_dir) / filename, temporary)
                    origin = "recording_import"
                else:
                    generate = synthesize_windows if engine == "windows" else synthesize_espeak
                    generate(LABEL_TEXT_ZH[label], temporary)
                    origin = engine
                inspect_wav(temporary)
                temporary.replace(target)
            finally:
                temporary.unlink(missing_ok=True)
        info = inspect_wav(target)
        info.update({"label": label, "text": LABEL_TEXT_ZH[label], "origin": origin,
                     "sha256": hashlib.sha256(target.read_bytes()).hexdigest()})
        info["path"] = filename
        records.append(info)
    manifest = {"source": "labels.py", "unknown_policy": "silent", "files": records}
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                                         encoding="utf-8")
    return manifest


def main():
    ap = argparse.ArgumentParser(description="准备项目中文 WAV 词汇")
    ap.add_argument("--output-dir", default=str(DEFAULT_AUDIO_DIR))
    ap.add_argument("--source-dir", help="以 labels.py 标签命名的 16-bit PCM 真人录音目录")
    ap.add_argument("--engine", choices=("auto", "windows", "espeak"), default="auto")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()
    result = prepare_audio(args.output_dir, args.source_dir, args.engine, args.overwrite)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
