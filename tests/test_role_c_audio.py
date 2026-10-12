"""角色 C 音频自动验证；测试波形/播放替身不代表扬声器或中文识别验收。"""

import json
import queue
import struct
import threading
import wave

import pytest

from audio import play_audio, prepare_audio
from audio.play_audio import AudioAnnouncer, play_wav_for_label
from audio.speech_map import SPEECH_MAP, inspect_wav, validate_result, wav_path_for_label
from board.audio_board_test import run_audio_test
from labels import ALL_LABELS, DYNAMIC_KIND, LABEL_TEXT_ZH, STATIC_KIND, make_result


def write_test_wave(path):
    # 小幅测试采样只用于解析器测试；不作为交付的中文音频。
    with wave.open(str(path), "wb") as wav:
        wav.setparams((1, 2, 16000, 32, "NONE", "not compressed"))
        wav.writeframes(struct.pack("<32h", *([1000, -1000] * 16)))


@pytest.fixture
def wav_dir(tmp_path):
    for filename in SPEECH_MAP.values():
        write_test_wave(tmp_path / filename)
    return tmp_path


@pytest.mark.parametrize("label", ALL_LABELS)
def test_mapping_uses_b_labels(label, wav_dir):
    path = wav_path_for_label(label, wav_dir)
    if label == "unknown":
        assert path is None
    else:
        assert path.name == label + ".wav"
        assert inspect_wav(path)["frames"] == 32
    assert set(SPEECH_MAP) == set(ALL_LABELS) - {"unknown"}


@pytest.mark.parametrize("label", ["palm", "sign_01", "../../x", "number_9"])
def test_invalid_label_rejected(label):
    with pytest.raises(ValueError):
        wav_path_for_label(label)


def test_unknown_never_calls_player(monkeypatch):
    monkeypatch.setattr(play_audio, "play_wav", lambda *a, **kw: pytest.fail("unknown 播放"))
    assert play_wav_for_label("unknown") is None


def test_b_compatibility_function(monkeypatch, wav_dir):
    calls = []
    monkeypatch.setattr(play_audio, "play_wav", lambda path, **kw: calls.append((path, kw)))
    play_wav_for_label("hello", wav_dir, "aplay", "plughw:1,0")
    assert calls == [(wav_dir / "hello.wav", {"backend": "aplay", "device": "plughw:1,0"})]


def test_missing_corrupt_silent_truncated_wav(wav_dir):
    with pytest.raises(FileNotFoundError):
        inspect_wav(wav_dir / "absent.wav")
    path = wav_dir / "hello.wav"
    path.write_bytes(b"wrong format")
    with pytest.raises((wave.Error, EOFError)):
        inspect_wav(path)
    with wave.open(str(path), "wb") as wav:
        wav.setparams((1, 2, 16000, 4, "NONE", "not compressed"))
        wav.writeframes(bytes(8))
    with pytest.raises(ValueError, match="静音"):
        inspect_wav(path)
    write_test_wave(path)
    path.write_bytes(path.read_bytes()[:-2])
    with pytest.raises(ValueError, match="截断"):
        inspect_wav(path)


@pytest.mark.parametrize("field,value", [("text", "错误"), ("kind", "invalid"),
                                         ("label", "palm"), ("confidence", float("nan")),
                                         ("timestamp", float("inf"))])
def test_invalid_result(field, value):
    result = make_result("hello", 0.9, DYNAMIC_KIND)
    result[field] = value
    with pytest.raises(ValueError):
        validate_result(result)


def test_announcer_threshold_cooldown_repeat_and_close(wav_dir):
    now = [10.0]
    calls = []
    announcer = AudioAnnouncer(wav_dir, player=lambda p: calls.append(p.name), clock=lambda: now[0])
    assert announcer.submit(None)["status"] == "no_result"
    assert announcer.submit(make_result("unknown", 1.0, STATIC_KIND))["status"] == "unknown"
    assert announcer.submit(make_result("hello", 0.49, DYNAMIC_KIND))["status"] == "low_confidence"
    assert announcer.submit(make_result("hello", 0.5, DYNAMIC_KIND))["status"] == "queued"
    now[0] = 11.0
    assert announcer.submit(make_result("thanks", 0.9, DYNAMIC_KIND))["status"] == "cooldown"
    now[0] = 11.5
    assert announcer.submit(make_result("hello", 0.9, DYNAMIC_KIND))["status"] == "repeat"
    now[0] = 13.0
    assert announcer.submit(make_result("hello", 0.9, DYNAMIC_KIND))["status"] == "queued"
    announcer.close()
    assert calls == ["hello.wav", "hello.wav"]
    assert [e["status"] for e in announcer.poll_events()] == ["played", "played"]
    announcer.close()
    with pytest.raises(RuntimeError):
        announcer.submit(make_result("thanks", 0.9, DYNAMIC_KIND))


def test_full_queue_nonblocking_and_rejected_request_does_not_update_state(wav_dir):
    entered, release = threading.Event(), threading.Event()
    now = [10.0]

    def blocked_player(path):
        entered.set()
        assert release.wait(3.0)

    announcer = AudioAnnouncer(wav_dir, config={"cooldown_s": 0, "repeat_window_s": 0},
                               queue_size=1, player=blocked_player, clock=lambda: now[0])
    try:
        assert announcer.submit(make_result("hello", 0.9, DYNAMIC_KIND))["status"] == "queued"
        assert entered.wait(1.0)
        now[0] += 1
        assert announcer.submit(make_result("thanks", 0.9, DYNAMIC_KIND))["status"] == "queued"
        now[0] += 1
        assert announcer.submit(make_result("help", 0.9, DYNAMIC_KIND))["status"] == "queue_full"
        assert announcer._last_label == "thanks"
    finally:
        release.set()
        announcer.close()


def test_play_failure_reported_worker_continues(wav_dir):
    def player(path):
        raise OSError("speaker unavailable")
    with AudioAnnouncer(wav_dir, player=player,
                        config={"cooldown_s": 0, "repeat_window_s": 0}) as announcer:
        announcer.submit(make_result("hello", 0.9, DYNAMIC_KIND))
        announcer.submit(make_result("thanks", 0.9, DYNAMIC_KIND))
    events = announcer.poll_events()
    assert len(events) == 2 and all(e["status"] == "failed" for e in events)
    assert "speaker unavailable" in events[0]["error"]


def test_prepare_import_and_atomic_failure(wav_dir, tmp_path, monkeypatch):
    output = tmp_path / "imported"
    manifest = prepare_audio.prepare_audio(output, source_dir=wav_dir)
    assert len(manifest["files"]) == len(ALL_LABELS) - 1
    assert all(r["origin"] == "recording_import" for r in manifest["files"])
    before = (output / "number_1.wav").read_bytes()

    def failing_generator(text, path):
        path.write_bytes(b"broken")
        raise RuntimeError("engine failed")
    monkeypatch.setattr(prepare_audio, "synthesize_windows", failing_generator)
    with pytest.raises(RuntimeError, match="engine failed"):
        prepare_audio.prepare_audio(output, engine="windows", overwrite=True)
    assert (output / "number_1.wav").read_bytes() == before
    assert not list(output.glob("number_1_*.wav"))


def test_offline_board_mapping(wav_dir):
    result = run_audio_test([make_result("hello", 0.9, DYNAMIC_KIND),
                             make_result("unknown", 1.0, STATIC_KIND)], wav_dir, True)
    assert result["passed"] and result["playback_executed"] is False
    assert [r["status"] for r in result["results"]] == ["validated", "unknown"]


def test_existing_b_audio_hook():
    from realtime_sign_pc import build_audio_player
    assert build_audio_player(True) is play_wav_for_label
    assert build_audio_player(False) is None


@pytest.mark.parametrize("config", [{"cooldown_s": -1}, {"repeat_window_s": float("nan")},
                                    {"static_min_confidence": 2}])
def test_invalid_audio_config(config):
    with pytest.raises(ValueError):
        AudioAnnouncer(config=config)


def test_aplay_command_and_failure_propagation(wav_dir, monkeypatch):
    calls = []
    monkeypatch.setattr(play_audio.shutil, "which", lambda name: "/usr/bin/" + name)
    monkeypatch.setattr(play_audio.subprocess, "run", lambda cmd, **kw: calls.append((cmd, kw)))
    info = play_audio.play_wav(wav_dir / "hello.wav", "aplay", device="plughw:1,0")
    assert calls[0][0] == ["/usr/bin/aplay", "-q", "-D", "plughw:1,0", info["path"]]
    assert calls[0][1]["check"] and calls[0][1]["timeout"] > info["duration_s"]
    monkeypatch.setattr(play_audio.shutil, "which", lambda name: None)
    with pytest.raises(RuntimeError, match="未安装"):
        play_audio.play_wav(wav_dir / "hello.wav", "aplay")


def test_close_timeout_can_be_retried(wav_dir):
    entered, release = threading.Event(), threading.Event()

    def blocked_player(path):
        entered.set()
        assert release.wait(3.0)
    announcer = AudioAnnouncer(wav_dir, player=blocked_player)
    announcer.submit(make_result("hello", 0.9, DYNAMIC_KIND))
    assert entered.wait(1.0)
    try:
        with pytest.raises(TimeoutError):
            announcer.close(.01)
    finally:
        release.set()
        announcer.close()


def test_delivered_chinese_assets_and_manifest():
    import hashlib
    from audio.speech_map import DEFAULT_AUDIO_DIR
    manifest = json.loads((DEFAULT_AUDIO_DIR / "manifest.json").read_text(encoding="utf-8"))
    assert {r["label"] for r in manifest["files"]} == set(ALL_LABELS) - {"unknown"}
    for item in manifest["files"]:
        path = DEFAULT_AUDIO_DIR / item["path"]
        info = inspect_wav(path)
        assert info["channels"] == 1 and info["sample_rate"] == 16000
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
        assert item["text"] == LABEL_TEXT_ZH[item["label"]]
