# 内置低氧计算迁移验收记录

## 开发起点与现场保护

开发分支为 `refactor/timeseries-workflow`，起点 `b24c000`。开始时有 19 个已修改文件和 6 个未跟踪文件；内容涉及任务生命周期、评测保护、资源引用、文档及验收脚本。开始前已在被忽略的 `.runtime/migration-audit` 保存补丁与未跟踪文件副本。继续在这些改动上开发，没有 reset、清理或覆盖用户改动。

历史基线及原审查工作区只读。用户指南采用原审查文档中仍然准确的界面流程；架构及环境文档移除旧的外部项目运行要求。根 README 不修改。

## 验证环境与命令

目标是 Windows、Python 3.12.11、PyTorch 2.5.1+cpu。环境通过 `uv==0.8.22` 和仓库锁文件安装；平台与计算分开。运行下列命令前完成[安装步骤](hypoxemia-runtime-and-delivery.md)，验收安装加 `-WithVerification`。

```powershell
$env:SOTABAND_LOAD_DOTENV = '0'
$env:SOTABAND_USER_ID = 'synthetic-acceptance'
$env:SOTABAND_RUNTIME_ROOT = Join-Path (Get-Location) '.runtime/acceptance-new'
Remove-Item Env:SPO2_HYPOXEMIA_PROJECT -ErrorAction SilentlyContinue
Remove-Item Env:SPO2_HYPOXEMIA_PYTHON -ErrorAction SilentlyContinue
Remove-Item Env:SPO2_HYPOXEMIA_PIPELINE_SCRIPT -ErrorAction SilentlyContinue
Remove-Item Env:SOTABAND_HYPOXEMIA_PYTHON -ErrorAction SilentlyContinue
.venv-platform/Scripts/python.exe -m pytest tests/unit -q -p no:cacheprovider
.venv-platform/Scripts/python.exe scripts/check_hypoxemia_sources.py
.venv-platform/Scripts/python.exe scripts/verify_hypoxemia_pr.py
$env:SOTABAND_RUNTIME_ROOT = Join-Path (Get-Location) '.runtime/acceptance-dualscale-new'
.venv-platform/Scripts/python.exe scripts/verify_hypoxemia_pr.py --model SegRNNDualScaleV2 --skip-raw
cd frontend
npm ci
npm run build
```

每次使用新的运行目录。验收脚本生成合成 CSV/ZIP 与窗口数据，经真实计算进程训练，保存模型并按模型 ID 重新选择，再按另一个数据集 ID 评测。下载走 FastAPI 文件路由；用 openpyxl 打开 HTTP 响应中的 XLSX 并核对来源及指标。

## 当前结果

| 检查 | 结果 |
| --- | --- |
| 迁移前单元测试 | 105 通过 |
| 前端构建 | 通过；存在原有 chunk 大小及混合静态/动态导入警告 |
| 新建 Python 3.12.11 平台环境单元测试 | 109 通过 |
| 新平台环境健康接口 | HTTP 200，healthy |
| 模型实现来源校验 | 48 个文件（47 个 Python 文件和 LICENSE）通过 SHA-256 校验 |
| CPU 目录模型导入追踪 | 42 个导入通过；两个 Mamba 模型单独标记需要 CUDA 扩展 |
| CSV/ZIP 原始处理 | 24 个合成设备、28,800 行；生成并登记 24 个 256×5 窗口（12 阳性、12 阴性） |
| SegRNN 短训练、保存、重新选择 | 48 窗口训练 1 epoch；权重、scaler、配置、阈值、manifest 均保存并成功重载 |
| SegRNNDualScaleV2 短训练、保存、重新选择 | 同样通过 1 epoch 流程 |
| 指定另一数据集评测 | 按 ID 选择独立 60 窗口合成数据，验证划分 8 窗口；模型路径、数据路径和 ID 一致 |
| Excel | HTTP 200 attachment；openpyxl 打开响应内容，核对模型 ID、数据集 ID 和 F1 等单元格 |
| 失败分支 | 2 Hz、错误通道顺序、一个 255 行窗口、全部 255 行窗口、缺失权重均拒绝；实际子进程启动失败和取消状态正确 |
| 隔离源码安装与完整复跑 | 通过；新建两个环境、空登记表、无 `.env`、清除旧项目/解释器变量；完整复跑 CSV/ZIP → 训练 → 保存 → 按 ID 评测 → HTTP 下载 |

两次开发工作区评测的合成指标分别为：SegRNN accuracy=0.75、F1=0.666667、AUC=0.9375；SegRNNDualScaleV2 accuracy=0.375、F1=0.444444、AUC=0.4375。均来自单独选择的 60 窗口数据集的验证划分，不能用于医学性能判断。

独立安装复跑 SegRNN 得到相同结果，权重 SHA-256 均为 `c147ed12b734a2c64f66ffc2a8411581b85748a51aee31f02fa562fb3f55802a`。两次训练使用不同的源码根目录、虚拟环境、任务登记和运行根目录。训练及评测的 `runtime_provenance.json` 记录实际模块文件来源，全部属于当次检出的内置组件；计算进程的解释器属于当次新建环境。

本地证据（全部忽略，不随 PR 提交）：`.runtime/builtin-acceptance-2/acceptance.json`、`.runtime/builtin-acceptance-dual-2/acceptance.json`、`.runtime/clean-source-a/.runtime/clean-acceptance-1/acceptance.json`、`.runtime/migration-audit/clean-install-evidence.json`。隔离安装复用了可下载的包缓存，未复用旧虚拟环境；大包 wheel 与 PyPI 发布 SHA-256 核对。原外部研究项目没有移动或删除。

安装期间系统盘缓存空间不足，随后将下载缓存及临时目录切换至工作区 `.runtime`；没有删除用户数据。缓存只包含可重新下载的包，不包含旧虚拟环境或模型产物。

## 来源与范围

模型库上游为 `thuml/Time-Series-Library`，交付内容与固定提交 `4e938a1767106324dd753b2a44832bf870a0252e` 比对。45 个上游 Python 文件及 MIT LICENSE 一致；两个研究项目新增文件单独列入 `SOURCE.json`。备份本身缺少 Git 元数据，无法据此断言它原来的 checkout 提交；不把训练权重当作模型实现依赖。

合成指标只用于验证流程，不代表医学性能。GPU/CUDA/Mamba、Linux、所有目录模型的完整训练、人工浏览器逐步操作、在线 LLM 服务和真实临床数据性能不属于已经通过的验证。多实例、强杀恢复、实时报警和在线单窗口预测也不在本次交付范围。

## 审查分支

阶段 A 已完整通过，随后才开始准备新的本地审查分支。不会推送、创建 PR 或合并 main。
