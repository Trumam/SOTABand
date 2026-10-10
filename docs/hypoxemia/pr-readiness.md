# 低氧离线工作流 PR 验收记录

更新日期：2026-10-10。目标分支为原项目当前 `main`；本次交付仅涵盖离线数据检查、训练、模型登记、评测与 Excel 导出。工作流是静态、进程内挂载，不支持实时预测、动态安装插件或多实例部署。

当前干净审查分支基于本地缓存的原项目 `origin/main`（`f6ea292`）。本次 GitHub 连接失败，尚未确认远端是否有新提交，也未推送到个人 fork 或创建 PR。推送前应重新 `git fetch origin main`，必要时将分支更新到最新上游基底并复跑检查。外部低氧计算项目未包含在本仓库中；维护者要复现实训，需获得其可用版本及专用 Python 环境，否则只能运行本仓库的单元测试和前端构建。

## 变更与实际结果

- 评测从选定的模型资源 ID 解析权重目录；显式目录与 ID 不一致时拒绝。数据集 ID 与目录不一致时也拒绝。
- 模型和数据清单核对五通道顺序、采样率、窗口长度；评测脚本再核对每个 pickle 窗口的真实通道与长度，不做静默裁剪或补齐。旧产物缺少模型清单时需先补齐可信元数据。
- 任务领取与完成状态有原子条件保护。可捕获的 worker 启动失败标记 failed，取消先落盘再终止进程；训练完成处理可重复调用而不重复注册资源。
- 新模型说明及任务、模型、数据注册表写入隔离运行目录。审查分支须从原项目 `main` 建立，不带入旧分支已提交的任务日志、注册表和模型定义运行记录。

验收环境：Windows 11，平台测试环境 Python 3.12，专用计算环境 PyTorch 2.5.1+cpu；外部训练项目需提供 `scripts/run_tslib_classification_trial.py` 与 `vendor/Time-Series-Library`。验收数据由 `scripts/verify_hypoxemia_pr.py` 固定随机种子生成：24 个组、48 个窗口，每窗口 256 行，列为 `Time, SpO2, HR, PR, RR, PI`，采样率清单为 1 Hz，正负样本各 24 个。不含患者记录。

运行脚本完成：数据文件检查、SegRNN 训练 1 轮、任务完成及模型产物清单、登记保存模型、按模型 ID 再选模型、对指定数据验证集评测、生成有效 XLSX，并拒绝 2 Hz 错配清单及真实长度为 255 的窗口。本次验证集为 8 个窗口，accuracy、F1 均为 0.75，AUC 为 0.6875；这些是合成数据的流程检查值，不能作为医学性能结论。

复验时先将以下路径替换为部署环境路径，并确保运行根目录不含真实研究数据：

```powershell
$env:SOTABAND_RUNTIME_ROOT = Join-Path (Get-Location) '.runtime/pr-acceptance'
$env:SPO2_HYPOXEMIA_TRUSTED_DATA_ROOTS = $env:SOTABAND_RUNTIME_ROOT
$env:SPO2_HYPOXEMIA_PROJECT = 'D:\path\to\spo2-project'
$env:SPO2_HYPOXEMIA_PYTHON = 'D:\path\to\spo2-env\python.exe'
& $env:SPO2_HYPOXEMIA_PYTHON scripts/verify_hypoxemia_pr.py
python -m pytest tests/unit -q -p no:cacheprovider
cd frontend
npm run build
```

已验证：单元测试 105 项通过（含 Excel HTTP 下载）；前端 TypeScript 与 Vite 构建通过。构建仍报告现有大包和无效动态导入警告。未在本次验收中验证原始监护数据处理、浏览器逐步操作、跨机器部署或任务进程被操作系统强制终止后的自动恢复。生产使用前仍需以当地数据和部署环境复验，且本功能仅供研究，不用于临床诊断。
