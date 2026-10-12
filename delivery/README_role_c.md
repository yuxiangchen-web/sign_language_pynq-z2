# 角色 C 增量交付包

把 `role_c_delivery.zip` 中的目录结构合入团队现有 `sign-language-pynq` 工程。包只含C本轮新增文件，不包含A/B的代码、Overlay、模型、数据集或虚拟环境；它依赖既有 `labels.py`、`models/config.json` 和团队主工程。

先读 `report/role_c_delivery.md`，接口设计在 `report/role_c_analysis.md`，实机接入在 `board/README_role_c.md`，学习说明在 `report/role_c_learning.md`。

PC使用Python3.12建立独立环境并安装 `requirements_role_c.txt`，然后运行：

```powershell
python -m board.verify_role_c
```

当前计划应得到105项通过，包含C84项及B21项。加入 `--include-legacy` 应如实得到124通过/2个既有乱码断言失败。不要删除失败测试或将输出改成乱码。

在PYNQ镜像上使用其实际可用的Python/PYNQ/NumPy与ALSA，不要直接用PC锁定版本覆盖镜像。A未交付DMA/HLS接口，板卡步骤和待补接口详见板端说明。九个中文WAV可以直接复用，无需在板卡安装语音合成引擎。

`role_c_manifest.json` 列出包内源文件、资产、文档和日志的SHA-256，归档已校验CRC及逐文件内容。最终软件验证摘要在 `report/role_c_logs/final/summary.json`，旧版全量失败证据在 `report/role_c_logs/legacy_full/automated_tests.txt`。
