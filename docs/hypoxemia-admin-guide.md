# 低氧血症平台部署与维护说明（管理员版）

适用版本：当前低氧工作流重构版，更新日期：2026-10-10。普通使用者请阅读[操作指南](hypoxemia-operation-guide.md)。本文将原指南中的安装、路径、依赖和排错内容集中到管理员入口。

## 1. 部署前提

当前部署目标为单机研究环境。网页依赖平台后端、外部低氧项目和专用计算环境；只安装 SOTABand 的 Python 依赖并不构成完整低氧运行环境。

| 项目 | 要求 |
| --- | --- |
| 当前代码目录 | 本机为 `D:\code\SOTABand-refactor`；其他机器按实际路径替换 |
| 平台 Python | `pyproject.toml` 要求 Python >= 3.12 |
| Node.js | 锁定的 Vite 8.1.0 要求 `^20.19.0` 或 `>=22.12.0`；建议使用符合要求的 Node 22 LTS，旧指南的 Node 18 不适用 |
| 外部低氧项目 | 包含训练脚本、数据流水线和 `vendor/Time-Series-Library` |
| 专用 Python | `SPO2_HYPOXEMIA_PYTHON` 指向已安装外部计算依赖的 `python.exe` |
| 大模型服务 | 按 `.env.example` 配置，用于对话及部分参数/设计整理 |
| 数据与模型 | 确认通道、采样率、窗口、标签和预处理约定，准备相匹配的模型与数据 |

本版单样本 `predict` 仍未完成，交付范围为离线处理、训练和评测。会话状态在内存中，不以多进程后端或多实例方式交付连续工作流。

## 2. 首次安装与配置

以下为 Windows PowerShell 示例，只在新部署环境执行；已有可用环境可直接使用，避免重建和覆盖配置。

```powershell
cd D:\code\SOTABand-refactor
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
if (-not (Test-Path -LiteralPath .env)) {
    Copy-Item -LiteralPath .env.example -Destination .env
}
```

编辑 `.env`，将所有示例路径替换为真实路径。不要给使用者分发含密钥的配置文件。

```dotenv
LLM_PROVIDER=deepseek
LLM_API_KEY=填写部署使用的密钥
SPO2_HYPOXEMIA_PROJECT=D:\research\spo2-project
SPO2_HYPOXEMIA_PYTHON=D:\envs\spo2\python.exe
SOTABAND_RAW_STAGING_ROOT=D:\research\staging
SPO2_HYPOXEMIA_TRUSTED_DATA_ROOTS=D:\research\approved-data
```

按服务商要求补充 `LLM_BASE_URL`、`LLM_MODEL`。可信数据根目录可有多个，Windows 使用分号分隔。pickle 数据应确认来源；当前外部项目目录、运行时上传目录和处理输出目录也会进入工具的可信路径集合，不应把公网任意文件上传等同于经过审核的数据接入。

外部项目应包含 `scripts/run_tslib_classification_trial.py` 和模型库。原始处理脚本默认位于 `src/data_pipeline/monitor_data_pipeline/run_dedup_pipeline.py`，非默认布局需核对 runner 配置。

前端安装：

```powershell
cd D:\code\SOTABand-refactor\frontend
npm ci
```

项目工具检查可以使用 `python scripts/check_tool_env.py --dry-run`，但不能替代外部训练环境验收。

## 3. 启动当前重构版

后端终端：

```powershell
cd D:\code\SOTABand-refactor
.\.venv\Scripts\python.exe -m uvicorn app.main:app --env-file .env --host 127.0.0.1 --port 8002
```

前端终端：

```powershell
cd D:\code\SOTABand-refactor\frontend
$env:SOTABAND_API_PORT = '8002'
$env:SOTABAND_FRONTEND_PORT = '5174'
npm run dev -- --host 127.0.0.1 --port 5174 --strictPort
```

浏览器打开 `http://127.0.0.1:5174`，后端健康检查为 `http://127.0.0.1:8002/api/health`。前端 API 代理端口由前端进程的环境变量决定，修改后端 `.env` 不代表运行中的前端代理已同步改变。

此启动示例仅供本机使用。远程使用者应获得管理员部署并验证的实际网址。Python 代码或启动环境修改后重启后端，前端启动配置修改后也需重启前端；事先确认任务状态，重启后会话交互步骤不保证恢复。

基线使用 5173/8001，重构默认使用 5174/8002，不要混用页面与后端。详见[运行隔离说明](migration-runtime-isolation.md)。

## 4. 文件实际保存位置

默认运行根目录为当前 checkout 下的 `.runtime/refactor`。设置路径环境变量后，以实际配置和任务元数据为准。

| 内容 | 默认位置 |
| --- | --- |
| 上传文件 | `.runtime/refactor/uploads/` |
| 原始处理输出 | `.runtime/refactor/processed-data/<时间戳>/...` |
| 训练运行目录 | `.runtime/refactor/timeseries-runs/<模型ID>-<时间戳>/...` |
| 评测计算 JSON | `.runtime/refactor/timeseries-runs/evaluation-<唯一标识>.json` |
| Excel 导出 | `.runtime/refactor/timeseries-runs/evaluations/` |
| 结果仓库 | `.runtime/refactor/timeseries-runs/results/<result_id>/result.json` |
| 任务注册表 | `.runtime/refactor/tasks/registry.json` |
| 任务日志 | `.runtime/refactor/tasks/runs/<task_id>/task.log` |
| 模型注册表 | `.runtime/refactor/models/registry.json` |
| 数据注册表 | `.runtime/refactor/data/registry.json` |

`SOTABAND_RUNTIME_ROOT` 可调整运行根目录；`SOTABAND_TIMESERIES_RUNS_DIR`、`SOTABAND_PROCESSED_DATA_DIR` 等可覆盖子目录。ZIP 临时解压位置以配置/任务记录为准。

首次初始化可能从静态注册表复制数据和模型元信息，但不会复制这些条目引用的真实文件。资源定义文档仍可能在 `resources/.../definitions`，也不能将运行目录隔离理解为外部依赖全部独立。

备份时同时保留注册信息与其指向的真实文件。训练模型至少包括 `best_model.pt`、`scaler.pkl`、`tslib_model_config.json`、`threshold_report_f1.json`，以及当前训练写出的 `manifest.json`，不要只备份权重。

## 5. 数据与参数交付

已处理数据应同时准备 `window_features.pkl`、`window_info.pkl`、`window_stats.json`；原始处理完成后还会生成 `dataset_manifest.json`。当前领域约定为 SpO2、HR、PR、RR、PI 五通道，默认采样率 1 Hz。

文件扫描不会读取全部 pickle 内容。缺少统计文件时，卡片数量不能证明实际样本数。评测会核对模型和数据清单中的五通道顺序、采样率、窗口长度，并在读取实际窗口后拒绝长度不符的数据；旧模型若缺少 `manifest.json`，需先补齐可信元数据，不能直接评测。预处理和标签语义仍需管理员核对，元数据检查不能证明临床适配性。

常用处理参数如下。完整字段见 `resources/workflows/hypoxemia/conversation_config.py` 和 runner 规范/校验。医学标签和参数值由研究方案决定。

| 参数 | 当前默认值 | 含义 |
| --- | --- | --- |
| `configs` | `["256:30"]` | 窗口秒数:预测间隔秒数 |
| `min_segment_seconds` | 600 | 最短连续监护段 |
| `spo2_threshold` | 94 | 低氧标签使用的 SpO2 阈值 |
| `hypoxemia_duration_seconds` | 20 | 连续低氧时长 |
| `min_hypo_duration_seconds` | 20 | 窗口内低氧最短时长 |
| `max_non_hypo_ratio` | 2.0 | 非低氧/低氧最大比例，不保证最终严格相等 |
| `nan_ratio_threshold` | 0.1 | 缺失比例上限 |
| `pi_threshold` | 0.3 | PI 质量阈值 |
| `seed` | 42 | 采样随机种子 |

训练公共默认值包括 `epochs=140`、`batch_size=32`、`learning_rate=0.00025`、`optimizer=adamw`、`seed=42`。模型配置可能覆盖默认值，以提交前确认的配置和实际日志为准。参数卡不是每种模型单独定制的完整 schema。

交付初期建议每次使用一组窗口配置。更改窗口长度后验证对应模型的真实短训练和加载；多组窗口输出需逐个确认登记及选择结果，不能仅凭脚本结束认定全部已接入。

## 6. 常见故障的管理员检查顺序

| 故障 | 检查方向 |
| --- | --- |
| 卡片与指南不符 | 确认 checkout、提交、端口及代理后端，重启已加载旧代码的进程 |
| 长期 queued | 检查 worker 是否启动和任务日志；已捕获的启动失败会标记 failed，进程异常退出后的遗留状态仍需管理员检查 |
| 取消后状态不一致 | 检查 worker/训练进程和模型状态；取消会先落盘再终止进程，单机异常中断后仍需人工核查 |
| 训练完成处理失败 | 检查产物、日志、序列长度/采样率元数据；旧任务可能缺新字段，不直接改为 completed |
| `MemoryError` 出现在 `pickle.load` | 检查数据体积、可用内存与解释器；缩小 batch 不一定解决一次性加载的内存峰值 |
| 模型产物不完整 | 从任务元数据、`trial_result.json` 找实际目录；权重可能在 trial 下的嵌套 runs 目录 |
| 来源 ID 为空或不符 | 核对会话选项、传入路径、注册条目和结果元数据 |
| 重启后无法续接 | 会话是内存状态；先查持久任务和产物，再引导重新选择数据/模型，不默认重训 |
| 评测缺指标 | 查计算脚本输出；卡片仅展示部分指标，声明支持的名称不代表每次都返回数值 |

架构缺口与修复顺序见[版本对比说明](sotaband-version-comparison.md)。

## 7. 发给使用者之前的验收

以下需要在部署环境执行，不代表编写本文时已全部通过。

1. 填写使用者指南开头的网址、数据集、模型、参数要求及联系人。
2. 用普通用户浏览器走一次已登记数据选择，并走一次配套文件上传。
3. 用小数据完成原始处理和扫描，确认统计、输出目录与登记一致。
4. 完成短训练，验证保存架构与保存训练模型两个选择，确认保存模型可再次选择。
5. 对指定数据评测，核对实际模型、数据与结果来源，验证 Excel 链接及文件内容。
6. 验证失败和停止任务的显示，记录恢复办法，补充该部署实际页面的示例截图。
7. 记录代码提交、外部项目版本、Python/依赖环境、测试数据及验收日期，注明未验证路径。

本版使用 48 个合成窗口完成了数据检查、单轮训练、保存并重新选择模型、验证集评测及 Excel 生成；`tests/unit` 为 105 项通过。复验命令与边界见[PR 验收记录](pr-readiness.md)。这不代表另一台机器或浏览器页面已经验收。
