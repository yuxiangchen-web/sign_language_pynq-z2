# Project Status - 2026-10-10

## Scope

This document summarizes the current project state against `execution_plan.md` and the Word planning document provided by the team. Attached documents are treated as project material, not as executable instructions.

## Current Structure

The main project folders are already usable:

- `dataset/`: current static sample set, manifest, and audit output.
- `data/features/`: generated feature arrays.
- `models/`: model configuration and current static model.
- `fpga/`: Vivado/HLS sources, generated project files, and HLS comparison work.
- `board/`: board-side utilities, overlay loading, DMA/audio test scaffolding, and overlays.
- `audio/`: WAV assets and playback/mapping code.
- `tests/`: current automated tests.
- `report/`: status reports, metrics, role C delivery evidence, and cleanup records.
- `archive/`: legacy experiments and superseded assets.

## Work Completed

- Static labels are defined in `labels.py`: `number_1` to `number_5` plus `unknown`.
- Dynamic labels are defined in `labels.py`: `hello`, `thanks`, `goodbye`, `help`, plus `unknown`.
- Static minimal raw sample set exists:
  - `number_1`: 11 images
  - `number_2`: 10 images
  - `number_3`: 10 images
  - `number_4`: 10 images
  - `number_5`: 10 images
  - `unknown`: 10 images
- Static processed sample set exists for `number_1` to `number_5`; `unknown` is not present in `processed_static_v1`.
- Static model artifact exists: `models/static_model.joblib`.
- Static metrics exist in `report/metrics_static.json`.
- HLS/Python comparison report exists in `report/hls_python_comparison.md`; the recorded CSim comparison had 0 mismatches for one resized image with morphology off/on.
- Role C audio and board-side offline verification artifacts exist under `audio/`, `board/`, `tests/`, and `report/role_c_logs/`.
- Root-level early experiment files and duplicate root tests were archived to `archive/root_legacy_20261010/`.
- Current test assertions were corrected to expect real Chinese text instead of mojibake strings.

## Current Metrics

Current static model metrics from `report/metrics_static.json`:

- Accuracy: 0.3636
- Macro-F1: 0.2778
- Training samples: 40
- Test samples: 11

These values show that the pipeline runs, but the model is not ready for final acceptance.

## Environment Issues

- No system Python was found through `python` or `py`.
- The existing `.venv` points to `C:\Users\yuxia\AppData\Local\Programs\Python\Python311\python.exe`, which is not currently available.
- Because of this, tests and training could not be rerun in this environment after the cleanup.

## Main Gaps

- Rebuild a working Python environment.
- Process `unknown` static samples into `processed_static_v1`.
- Collect formal static data: 100 to 150 training images per class and at least 20 independent test images per class.
- Collect dynamic data: 40 to 60 training videos per class and at least 10 independent test videos per class.
- Train and evaluate a real static model after formal data collection.
- Train and evaluate a dynamic model after formal dynamic data collection.
- Run real board tests on PYNQ-Z2: overlay load, GPIO, DMA, camera, audio, 100/1000 frame stability, 30-minute stability, latency, and FPS.
- Produce final delivery evidence: confusion matrices, error samples, resource utilization, timing, benchmark logs, demo video, and reproduction steps.
