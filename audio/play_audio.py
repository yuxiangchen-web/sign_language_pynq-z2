"""PC/PYNQ WAV 播放和非阻塞结果播报；兼容 B 预留的函数入口。"""

import math
import json
import os
import queue
import shutil
import subprocess
import threading
import time
from pathlib import Path

from audio.speech_map import inspect_wav, validate_result, wav_path_for_label


def play_wav(path, backend="auto", timeout_s=None, device=None):
    """同步播放真实 WAV。Linux 优先 ALSA aplay；Windows 使用 winsound。"""
    info = inspect_wav(path)
    if backend == "auto":
        backend = "winsound" if os.name == "nt" else "aplay"
    if backend == "winsound":
        if device:
            raise ValueError("winsound 不支持 ALSA device")
        if os.name != "nt":
            raise RuntimeError("winsound 仅可用于 Windows")
        import winsound
        winsound.PlaySound(info["path"], winsound.SND_FILENAME | winsound.SND_NODEFAULT)
    elif backend in ("aplay", "ffplay"):
        executable = shutil.which(backend)
        if not executable:
            raise RuntimeError(f"音频工具未安装: {backend}")
        if backend == "aplay":
            cmd = [executable, "-q"]
            if device:
                cmd += ["-D", device]
            cmd += [info["path"]]
        else:
            if device:
                raise ValueError("ffplay 不支持 ALSA device")
            cmd = [executable, "-nodisp", "-autoexit", "-loglevel", "error", info["path"]]
        timeout = info["duration_s"] + 5.0 if timeout_s is None else float(timeout_s)
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("播放超时必须为有限正数")
        subprocess.run(cmd, check=True, timeout=timeout, capture_output=True)
    else:
        raise ValueError(f"未知播放后端: {backend}")
    return info


def play_wav_for_label(label, audio_dir=None, backend="auto", device=None):
    """B 的 realtime_sign_pc.py 直接调用；unknown 返回 None。"""
    path = wav_path_for_label(label, audio_dir)
    return None if path is None else play_wav(path, backend=backend, device=device)


class AudioAnnouncer:
    """单工作线程和有界队列，保持推理线程畅通。

    submit(result) 返回状态 dict；播报错误可从 poll_events() 获取。
    时钟使用 monotonic，不依赖预测结果的墙上时间。
    """

    def __init__(self, audio_dir=None, config=None, queue_size=2, player=None,
                 clock=time.monotonic):
        self.audio_dir = audio_dir
        # 音频只依赖标签和共享 JSON 配置，不导入模型/OpenCV/skimage。
        config_path = Path(__file__).resolve().parents[1] / "models" / "config.json"
        with config_path.open(encoding="utf-8") as stream:
            self.config = json.load(stream)
        if config:
            self.config.update(config)
        for key in ("static_min_confidence", "dynamic_min_confidence"):
            value = float(self.config[key])
            if not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError(f"无效置信度阈值: {key}")
        for key in ("cooldown_s", "repeat_window_s"):
            value = float(self.config[key])
            if not math.isfinite(value) or value < 0:
                raise ValueError(f"无效时间窗口: {key}")
        if isinstance(queue_size, bool) or not isinstance(queue_size, int) or queue_size < 1:
            raise ValueError("queue_size 必须是正整数")
        self._player = player or play_wav
        self._clock = clock
        self._queue = queue.Queue(maxsize=queue_size)
        self._events = queue.Queue()
        self._lock = threading.Lock()
        self._last_label = None
        self._last_time = float("-inf")
        self._closed = False
        self._worker = threading.Thread(target=self._run, name="sign_audio", daemon=True)
        self._worker.start()

    def submit(self, result):
        if result is None:
            return {"status": "no_result"}
        checked = validate_result(result)
        label = checked["label"]
        with self._lock:
            if self._closed:
                raise RuntimeError("音频播报器已关闭")
            if label == "unknown":
                return {"status": "unknown", "label": label}
            threshold = float(self.config[f"{checked['kind']}_min_confidence"])
            if checked["confidence"] < threshold:
                return {"status": "low_confidence", "label": label}
            now = self._clock()
            age = now - self._last_time
            if age < float(self.config["cooldown_s"]):
                return {"status": "cooldown", "label": label}
            if label == self._last_label and age < float(self.config["repeat_window_s"]):
                return {"status": "repeat", "label": label}
            path = wav_path_for_label(label, self.audio_dir)
            inspect_wav(path)
            try:
                self._queue.put_nowait((checked, path))
            except queue.Full:
                return {"status": "queue_full", "label": label}
            self._last_label, self._last_time = label, now
            return {"status": "queued", "label": label}

    def _run(self):
        while True:
            item = self._queue.get()
            try:
                if item is None:
                    return
                result, path = item
                start = self._clock()
                try:
                    self._player(path)
                    event = {"status": "played", "label": result["label"],
                             "duration_s": self._clock() - start}
                except Exception as exc:
                    event = {"status": "failed", "label": result["label"],
                             "error": f"{type(exc).__name__}: {exc}"}
                self._events.put(event)
            finally:
                self._queue.task_done()

    def poll_events(self):
        events = []
        while True:
            try:
                events.append(self._events.get_nowait())
            except queue.Empty:
                return events

    def close(self, timeout_s=10.0):
        if not math.isfinite(timeout_s) or timeout_s <= 0:
            raise ValueError("关闭超时必须为有限正数")
        with self._lock:
            if not self._closed:
                # 队列已满时仍有期限，超时可再次调用 close。
                self._queue.put(None, timeout=timeout_s)
                self._closed = True
        self._worker.join(timeout_s)
        if self._worker.is_alive():
            raise TimeoutError("音频工作线程未在期限内关闭")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
