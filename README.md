# PYNQ-Z2 手语识别系统

基于 PYNQ-Z2 的静态手语识别项目。系统计划通过 USB 摄像头采集图像，在 PYNQ 的处理系统（PS）与可编程逻辑（PL）之间进行软硬件协同，实现手部图像预处理、特征提取和手势分类。

> 当前项目处于 PC 算法原型与 FPGA 基础工程验证阶段，最终性能数据将在板卡实测后补充。

## 1. 识别类别

当前规划识别以下 6 类：

| 标签 | 含义 |
|---|---|
| `palm` | 张开手掌 |
| `fist` | 握拳 |
| `victory` | 剪刀手 |
| `ok` | OK 手势 |
| `thumbs_up` | 点赞 |
| `unknown` | 其他动作或无有效手势 |

## 2. 系统流程

```text
USB 摄像头
    ↓
图像采集
    ↓
肤色分割与形态学处理
    ↓
最大轮廓与手部 ROI 提取
    ↓
128×128 标准化掩膜
    ↓
HOG 特征提取
    ↓
手势分类
    ↓
结果显示与性能统计
```

计划由 PS 负责摄像头输入、系统控制和分类，由 PL 加速适合并行计算的图像处理模块。

## 3. 当前进度

| 模块 | 状态 |
|---|---|
| Python/OpenCV 环境 | 已完成 |
| 灰度、二值化和形态学处理 | 已完成 |
| 肤色分割和轮廓提取 | 已完成原型 |
| 128×128 手部标准化 | 已完成 |
| HOG 特征提取 | 已完成 |
| PC 基线分类器 | 已完成流程验证 |
| PYNQ-Z2 Vivado 基础工程 | 已生成 Bitstream |
| PYNQ 系统镜像和板卡启动 | 待验证 |
| USB 摄像头实时采集 | 待验证 |
| FPGA 图像算法加速 | 待实现 |
| 准确率、延迟和资源测试 | 待完成 |

当前基线仅使用少量样本验证软件流程，训练集回测结果不能作为最终识别准确率。

## 4. 开发环境

- 操作系统：Windows
- Python：3.11.9
- OpenCV：4.14.0.94
- NumPy：2.4.6
- 编辑器：Visual Studio Code
- FPGA 工具：Vivado ML Standard 2025.2、Vitis 2025.2
- 目标板卡：PYNQ-Z2（XC7Z020）

## 5. 项目结构

```text
sign-language-pynq/
├─ board/                      # PYNQ Overlay 和板卡端文件
├─ dataset/
│  ├─ raw/                    # 原始手势图片
│  ├─ processed/              # 128×128 手部掩膜
│  └─ features/               # HOG 特征数据
├─ fpga/                       # Vivado 与后续 HLS 工程
├─ models/                     # 训练得到的模型
├─ outputs/                    # 图像处理测试输出
├─ report/
│  ├─ requirements_matrix.md  # 竞赛要求对应矩阵
│  └─ ai_collaboration.md     # AI 协作记录
├─ batch_preprocess.py         # 批量图像预处理
├─ batch_hog_features.py       # 批量提取 HOG 特征
├─ train_baseline.py           # 基线分类器训练
├─ requirements.txt            # Python 依赖
├─ LICENSE                     # 开源许可证
└─ README.md
```

## 6. PC 端运行方法

### 6.1 创建并激活虚拟环境

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

### 6.2 安装依赖

```powershell
python -m pip install -r requirements.txt
```

### 6.3 批量预处理

将图片放入 `dataset/raw` 下对应的类别文件夹，然后运行：

```powershell
python batch_preprocess.py
```

### 6.4 提取 HOG 特征

```powershell
python batch_hog_features.py
```

### 6.5 训练基线分类器

```powershell
python train_baseline.py
```

模型将保存到：

```text
models/prototype_model.npz
```

## 7. FPGA 工程

Vivado 工程当前包含：

- ZYNQ7 Processing System
- AXI GPIO
- AXI SmartConnect
- Processor System Reset
- PYNQ-Z2 板卡接口和 LED 约束

已生成用于基础验证的：

```text
board/overlays/led_test/led_test.bit
board/overlays/led_test/led_test.hwh
```

板卡可用后，将首先加载该 Overlay 验证 PS、PL 与 LED 控制链路，再进行图像算法加速开发。

## 8. 后续计划

- 使用摄像头为每类采集足量样本
- 划分训练集、验证集和独立测试集
- 生成准确率、混淆矩阵和错误样本分析
- 完成 PYNQ 镜像写入及网络连接
- 在板卡上验证 USB 摄像头
- 使用 Vitis HLS 实现图像处理加速模块
- 对比 CPU 与 FPGA 的延迟、帧率和资源占用
- 完成报告、演示视频与答辩材料

## 9. 数据与结果说明

- 不将训练集回测结果作为最终准确率。
- 最终性能数据必须来自实际板卡和测试集。
- 使用网络图片时应确认授权，不提交无权再分发的数据。
- 建议正式数据由参赛者自行采集，并记录采集条件。

## 10. AI 协作说明

本项目使用 AI 辅助项目规划、示例代码编写、错误分析和文档整理。所有 AI 输出均需经过参赛者运行或审核。详细记录见：

```text
report/ai_collaboration.md
```

## 11. 许可证

本项目源代码计划使用 MIT License，详情见 `LICENSE`。