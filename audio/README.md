# 角色 C 中文音频

此目录实现 B 已预留的 `audio.play_audio.play_wav_for_label(label)`，并为板端提供非阻塞 `AudioAnnouncer`。标签和中文文字只来自根目录 `labels.py`；播报阈值、冷却和防重复窗口读取 `models/config.json`。`unknown` 始终静默。

已交付九个真实中文语音文件，位于 `wav/`，格式为单声道、16 kHz、16-bit PCM。由本机 Windows 中文语音引擎生成；逐文件格式、长度和 SHA-256 已验证。文件检查不等于扬声器播放或人工听辨。

在工程根目录运行：

```powershell
python -m audio.test_audio
python -m audio.test_audio --play
python -m audio.prepare_audio --source-dir my_recordings --overwrite
```

PYNQ/Linux 使用 ALSA：

```bash
aplay -l
python -m audio.test_audio --play --backend aplay --device plughw:1,0
```

`plughw:1,0` 是命令示例，必须根据实际 `aplay -l` 选择。当前 LED Overlay 没有音频 IP；不假定存在 `overlay.audio`。可使用板卡实际可用的 USB/HDMI ALSA 输出。Windows 使用 `winsound`；Linux 可显式选择 `ffplay`。缺设备、缺播放程序、损坏或缺失 WAV 会报错，不用静音降级伪装成功。

重新生成语音可以运行 `python -m audio.prepare_audio --engine windows --overwrite`；Linux 可使用 `--engine espeak`，需要已安装支持中文的 espeak/espeak-ng。正式演示也可以导入团队自录的同名 WAV。已有有效录音默认保留；生成失败保留原文件。

同步兼容入口供 B 的现有 PC 程序直接使用：

```python
from audio.play_audio import play_wav_for_label
play_wav_for_label("hello")
```

板端推理推荐使用非阻塞入口，示例中的 `rt` 和 `frame_iter` 由 A 的程序提供：

```python
from audio.play_audio import AudioAnnouncer

with AudioAnnouncer(config=rt.config) as audio:
    for frame_bgr in frame_iter:
        result = rt.feed(frame_bgr)
        outcome = audio.submit(result)
        # 将 outcome 和 audio.poll_events() 写入实际联调日志。
```

`submit()` 返回 `no_result/unknown/low_confidence/cooldown/repeat/queue_full/queued`。后台播放事件为 `played/failed`，播放失败含错误文本。默认队列最多两条待播放记录，加一个正在播放的记录；满队列立即拒绝，避免无限积压。`close()` 等待队列完成并有超时；Windows 同步 winsound 本身不能被安全强制中断，关闭超时时应继续回收工作线程。现有 B 的同步函数调用不会自动改成后台播放。
