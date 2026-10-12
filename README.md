# Sign Language Recognition on PYNQ-Z2

本项目是 FPGA 创新赛作品，目标是在 PYNQ-Z2 平台上实现手语识别系统。当前系统支持静态数字手势识别、板端摄像头实时推理、JSON 结果输出，以及电脑端中文语音播报。

## 当前进度

- 已完成静态手势图像预处理流程
- 已完成 NumPy 轻量静态模型训练
- 已完成板端单张图片推理
- 已完成板端实时摄像头识别并输出 latest_static_result.json
- 已完成电脑端读取识别结果并语音播报
- 待完善动态手势识别、数据集清洗、模型评估和答辩材料

## 主要脚本

- `labels.py`：统一标签、中文文本、结果格式
- `preprocess.py`：图像预处理
- `batch_preprocess_signs.py`：批量处理静态手势图片
- `train_static_numpy_model.py`：训练静态识别模型
- `board_static_infer.py`：板端静态手势推理
- `board_static_live_json.py`：板端实时识别并写出 JSON
- `pc_speak_static.py`：电脑端读取结果并语音播报
