# 内置低氧功能测试记录

本文只记录测试环境、测试命令、实际结果和未覆盖范围。运行数据、患者数据、模型权重和日志均保存在被 Git 忽略的 `.runtime/` 目录，不属于交付内容。

## 测试环境

- Windows，Python 3.12.11，平台环境 `.venv-platform`。
- 低氧计算环境 `.venv-hypoxemia`，PyTorch 2.5.1+cpu。
- 前端 Node.js/npm，依赖由 `frontend/package-lock.json` 安装。
- 测试使用合成数据；运行时清除 `SPO2_HYPOXEMIA_PROJECT`、旧解释器路径和 `.env` 读取。

## 测试命令

```powershell
$env:SOTABAND_LOAD_DOTENV = '0'
Remove-Item Env:SPO2_HYPOXEMIA_PROJECT -ErrorAction SilentlyContinue
Remove-Item Env:SPO2_HYPOXEMIA_PYTHON -ErrorAction SilentlyContinue
.\.venv-platform\Scripts\python.exe -m pytest tests/unit -q
.\.venv-hypoxemia\Scripts\python.exe scripts/check_hypoxemia_sources.py
.\.venv-hypoxemia\Scripts\python.exe scripts/check_hypoxemia_model_catalog.py
Push-Location frontend
npm ci
npm run build
Pop-Location
```

完整链路验收使用 `scripts/verify_hypoxemia_pr.py`：合成原始 CSV/ZIP 或窗口数据 → 数据检查 → 短训练 → 保存模型 → 按模型 ID 重选 → 另一数据集评测 → HTTP 下载 Excel。每次验收使用新的 `SOTABAND_RUNTIME_ROOT`，不读取旧任务登记表、旧模型绝对路径或外部研究项目。

## 测试结果

| 检查 | 结果 |
| --- | --- |
| 平台单元测试 | 131 项通过，其中包含模型分组 API 测试和创建模型示例测试 |
| 前端构建 | `npm run build` 通过；保留既有动态导入和 bundle 大小警告 |
| 模型实现来源校验 | 内置 Time-Series-Library 来源文件和许可证校验通过 |
| 目录模型计算烟测 | 44 个条目：38 个通过，6 个明确跳过，0 个失败；覆盖训练前向、反向、AdamW 更新、普通评估和 EMA 评估 |
| 目录模型跳过项 | `KANAD`、`MultiPatchFormer`、`TiDE`、`WPMixer` 上游未实现分类；两个 Mamba 模型需要 CUDA 扩展 |
| 已登记模型配置 | 21 个资源中 20 个有效；历史无效 TimeMixer 配置在提交前拒绝，不自动修改 |
| 低氧端到端流程 | TimeMixer、SegRNN、SegRNNDualScaleV2 已用合成数据完成训练、保存、模型 ID 重载、独立数据集评测和 Excel 打开检查 |
| 数据契约失败分支 | 错误采样率、错误通道顺序、短窗口、缺失权重、模型或数据元数据不完整均明确拒绝 |
| 任务生命周期 | 启动失败、取消、重复领取和重复完成状态有单元测试覆盖 |
| 模型空间分类与分组 | 空分组、同名跨类别分组、刷新持久化、系统分组删除保护、非空分组删除保护测试通过；训练产物不完整时不会进入已训练列表 |
| 创建新的模型示例 | 使用 `GuideSegRNNDerived` 描述在隔离运行目录调用真实注册接口，得到 `configured`、`creation_type=custom-model`、`model_name=SegRNN` 的可训练配置资源；未生成权重，符合配置与权重分离规则 |
| 服务健康 | 后端 `8002/api/health`、前端代理 `/api/health` 和前端首页均返回 HTTP 200 |

## 测试证据

- 目录模型逐项 JSON 报告位于 `.runtime/model-catalog-checks/`，不提交到 Git。
- 端到端证据位于各自的 `.runtime/*/acceptance.json` 或 `evidence.json`，不提交到 Git。
- Excel 使用 `openpyxl` 打开下载响应，并核对模型 ID、数据集 ID、指标和来源字段。

## 未覆盖范围

- 未在 Windows CPU 环境验证 Mamba/CUDA 扩展；不宣称原生 Windows GPU 可用。
- 目录模型烟测不等于每个模型都完成完整数据处理、长轮次训练或医学性能验证。
