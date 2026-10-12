import json
import subprocess
import time
from pathlib import Path

KEY = Path.home() / ".ssh" / "pynq_nopass_ed25519"
REMOTE = "xilinx@192.168.2.99:/home/xilinx/sign-language-pynq/report/latest_static_result.json"
LOCAL = Path("report/latest_static_result.json")
LOCAL.parent.mkdir(exist_ok=True)

last_label = None
last_time = 0

def speak(text):
    ps = f'''
Add-Type -AssemblyName System.Speech
$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer
$speak.Rate = 0
$speak.Volume = 100
$speak.Speak("{text}")
'''
    subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

while True:
    try:
        scp_cmd = ["scp", "-q"]
        if KEY.exists():
            scp_cmd.extend(["-i", str(KEY)])
        scp_cmd.extend([REMOTE, str(LOCAL)])

        subprocess.run(
            scp_cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=3,
            check=True,
        )

        data = json.loads(LOCAL.read_text(encoding="utf-8"))
        label = data["result"]["label"]
        text = data["result"]["text"]
        confidence = data["result"]["confidence"]

        print("label=", label, "text=", text, "confidence=", confidence)

        now = time.time()
        if label != "unknown" and confidence >= 0.7:
            if label != last_label or now - last_time > 3:
                speak(text)
                last_label = label
                last_time = now

    except Exception as e:
        print("wait/error:", e)
        if not KEY.exists():
            print("hint: configure ~/.ssh/pynq_nopass_ed25519 or run scp manually")

    time.sleep(0.8)
