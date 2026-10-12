# Next Steps - 2026-10-10

## Priority 1: Restore The Development Environment

Install or restore Python, then rebuild the virtual environment from the project root:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest tests --import-mode=importlib -q
```

If Python 3.11 is not installed, install Python 3.11 or 3.12 first. Do not rely on the current `.venv`; it points to a missing interpreter path.

## Priority 2: Finish Static Data Pipeline

- Process `dataset/raw_static_v1/unknown` into `dataset/processed_static_v1/unknown`.
- Rebuild `dataset/static_manifest.csv`.
- Rerun `dataset_audit.py`.
- Expand each static class to at least 100 training images and 20 independent test images.
- Retrain static model and update `report/metrics_static.json`.

## Priority 3: Build Dynamic Dataset

- Confirm action rules for `hello`, `thanks`, `goodbye`, `help`, and `unknown`.
- Capture at least 3 minimum test videos per dynamic class first.
- Then capture 40 to 60 training videos and at least 10 independent test videos per class.
- Ensure train/test split is by complete video, not by frames from the same video.

## Priority 4: Model Quality

- Static target: accuracy and Macro-F1 close to or above the project acceptance line.
- Dynamic target: per-class recall and unknown rejection must be reported, not only overall accuracy.
- Save confusion matrices and error samples under `report/`.

## Priority 5: Board Verification

Run in this order on PYNQ-Z2:

1. Load LED overlay and verify GPIO.
2. Load `sign_preprocess_2026_1` overlay and inspect HWH metadata.
3. Run register checks.
4. Run single-frame DMA golden-vector comparison.
5. Run 100-frame and 1000-frame tests.
6. Run camera input.
7. Run audio playback.
8. Run full end-to-end inference.
9. Record FPS, latency, resource use, and 30-minute stability.

## Priority 6: Final Delivery

- Keep `labels.py` as the only label source.
- Keep current tests under `tests/`; legacy root tests are archived.
- Use `report/project_status_20261010.md` as the current status snapshot.
- Keep new experiment results in `report/`, not in the project root.
