# A/B 文件与交付检查（自动整理）

扫描路径：`D:\PYNQ\projects\sign-language-pynq`

## B：算法、模型与预测接口

### 已存在

- `labels.py`
- `preprocess.py`
- `feature_utils.py`
- `sequence_features.py`
- `batch_preprocess_signs.py`
- `batch_hog_features.py`
- `train_static_model.py`
- `evaluate_static_model.py`
- `train_dynamic_model.py`
- `evaluate_dynamic_model.py`
- `predictor.py`
- `realtime_sign_pc.py`
- `test_preprocess.py`、`test_predictor.py`
- `models/config.json`（由根目录 `config.json` 复制，供预测器默认读取）

### 缺少或尚未交付

- `models/static_model.joblib`
- `models/dynamic_model.joblib`
- 动态训练/测试数据目录（建议：`data/dynamic/`、`data/dynamic_test/`）
- 静态特征文件（建议：`data/features/static_train.npz`、`data/features/static_test.npz`）
- 模型指标和混淆矩阵报告

## A：采集、摄像头适配、HLS 与 Overlay

### 已存在

- `capture_dataset.py`
- `dataset_manifest.py`
- `dataset_audit.py`
- `fpga/hls/image_preprocess.h/.cpp`
- `fpga/hls/tb_image_preprocess.cpp`
- `fpga/hls/run_hls.tcl`
- `fpga/ip/image_preprocess_ip/component.xml`
- `fpga/export/sign_language_hw_2026_1.xsa`

### 缺少或尚未交付

- `capture_sequences.py`
- `board/camera_board_test.py`
- `board/run_sign_inference.py`
- `board/board_environment_check.py`
- `board/benchmark_cpu_fpga.py`
- `board/overlays/sign_preprocess_2026_1/sign_preprocess_2026_1.bit`
- `board/overlays/sign_preprocess_2026_1/sign_preprocess_2026_1.hwh`
- 静态/动态 manifest 和完整 audit 交付报告
- HLS/Python 对比报告、综合资源报告

## 说明

根目录的 B 脚本保留，以兼容现有导入；测试副本已放入 `tests/`，根目录测试文件未删除。模型文件和数据集不能自动生成替代品，需要真实训练数据和 B 的训练过程。
