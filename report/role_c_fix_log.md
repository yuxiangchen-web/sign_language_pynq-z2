# 角色 C 错误与修复记录

所有记录来自2026-10-09实际执行。C自身问题修复后回归；其他角色文件不擅自修改。最终当前计划105项通过，旧版全量124项通过/2项失败。

| 编号 | 原始错误 | 根本原因 | 修改文件/动作 | 修复方法 | 验证结果与证据 |
|---|---|---|---|---|---|
| E01 | `.venv/Scripts/python.exe` 提示No Python at另一用户路径 | 导入venv含原机器绝对解释器路径 | 只新增`.venv_role_c` | 使用本机可用Python3.12建立专用环境 | 之后解释器、pip和测试均实际运行；原venv未改 |
| E02 | ensurepip/pytest创建的目录PermissionError | 当前Windows受限进程无法访问Python设置权限后的临时目录 | 无工程源码修改 | 明确项目范围后使用允许的升级执行，依赖仅装专用venv | pip成功；当前测试通过。失败过程见`regression_first.txt`及本轮工具输出 |
| E03 | `ModuleNotFoundError: skimage` | B的feature_utils实际依赖scikit-image，原requirements缺项 | 新增`requirements_role_c.txt`，不改公共清单 | 补齐专用环境和完整锁文件 | pip check通过；B当前21项通过；原错误见`baseline.txt` |
| E04 | pytest import file mismatch | 根目录与tests有同名测试，默认导入方式冲突 | `board/verify_role_c.py` | 使用`--import-mode=importlib`，分别保存当前计划与包含旧版结果 | 完整收集126项；当前105项全通过，没有删除测试 |
| E05 | 语音生成子进程失败，最初日志缺具体stderr | PowerShell5.1/System.Speech枚举异常，受限上下文的SelectVoice也拒绝 | `audio/prepare_audio.py` | 优先可用pwsh，收集并报告stderr；实际生成使用允许访问本机语音的执行上下文 | 九个真实WAV生成通过；见`prepare_audio_retry.txt`、`prepare_audio_final.txt` |
| E06 | `cv2.imwrite` 对测试生成的长路径返回False | 本机OpenCV文件API对长Windows路径不可靠 | `board/role_c_benchmark.py`、C自己的测试夹具 | Python读写文件字节，OpenCV只做imdecode/imencode；保留图像内容及结果断言 | CPU工具和2项测试通过；未改变B源码 |
| E07 | 长路径修复后，无效图像测试抛FileNotFoundError而接口要求ValueError | 字节读取异常未转换成工具既定输入错误 | `board/role_c_benchmark.py` | 捕获OSError/cv2.error并以ValueError传播原异常链 | 测试通过；失败见`benchmark_missing_input_before_fix.txt` |
| E08 | 代码审查发现仅download重载会保留旧IP驱动缓存 | Python实例状态与新硬件状态可能不一致 | `board/load_overlay.py`、C自己的重载测试 | 重建OverlaySession/IP驱动，重复加载和地址校验；要求调用方先结束/复位旧事务 | 重载模型测试确认新Overlay和新GPIO实例；最终105通过 |
| E09 | 代码审查发现初始通道busy或halted可能被当作新事务使用 | SimpleDMA初次idle可为0，但后续busy必须拒绝 | `board/dma_transfer.py`、C的DMA测试 | 仅首次PYNQ标记允许idle=0；拒绝既有busy；halted/error转故障并记录 | 初始idle=0、busy、halted测试均通过 |
| U01 | 根目录静态/动态结果测试期待`涓€`/`浣犲ソ` | 旧版测试字面量已乱码，labels和当前测试的中文正确 | 未修改，保留B文件 | 向B报告编码问题；禁止将真实输出改成乱码或跳过断言 | 最终全量124通过2失败；`legacy_full/automated_tests.txt`有完整位置和断言 |

DMA的错误恢复还通过明确注入以下故障验证：缺完成/模拟缺TLAST、三种DMA错误位、提前结束导致字节不足、启动回调异常、复位不自清除、物理地址重叠或越界、对齐错误、CMA分配失败。故障实例禁止复用，未确认复位禁止释放缓冲；测试没有把复位失败改成通过。
