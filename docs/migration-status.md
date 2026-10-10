# 时序工作流迁移状态

本文件记录 `refactor/timeseries-workflow` 相对 `hypoxemia-baseline-v1` 的当前落地状态。

## 已落地

- 平台 Agent 通过 `WorkflowRegistry` 挂载领域工作流；低氧交互阶段、选择解析、参数收集和结果卡片位于 `resources/workflows/hypoxemia/`。
- Agent 保留通用会话、工具匹配、工具执行、任务提交和 SSE 输出；低氧工具 ID 不再出现在平台 Agent 的业务分支中。
- Worker 使用任务处理器注册表。训练完成处理器负责模型资源更新；原始数据处理完成处理器校验窗口文件、写入 `dataset_manifest.json` 并注册数据集。
- 模型产物完成后写入 `manifest.json`，检查模型时校验五通道顺序、序列长度和采样率。
- 评测结果通过 `TimeSeriesWorkflowService` 的 `JsonResultStore` 持久化，保存 `result_id` 和模型、数据集、任务来源信息。
- 主页训练和评测经 `TimeSeriesWorkflowService` 调用低氧后端；工具仍在独立子进程中执行。工作流通过公开宿主接口调用平台能力。
- Worker 在产物校验与资源登记完成后，才把任务标记为完成；新低氧任务使用专属任务类型，旧任务类型仍可读取。
- 任务、数据和模型注册表的主要更新使用跨进程锁及原子文件替换。
- 核心模型注册表只读取显式 `group_path`，低氧工作流在注册时提供“低氧血症预测”分组。
- 运行时继续使用 `.runtime/refactor`，不会共享基线任务、日志、临时文件和模型输出。
- 评测会按模型资源 ID 定位产物，核对数据集 ID、模型与数据元数据，并检查实际五通道窗口长度；不再静默裁剪或补齐后输出指标。
- 任务启动失败、重复领取和取消的状态转换已有保护；新模型说明写入隔离运行目录。
- 使用合成窗口完成数据检查、短训练、保存及重选模型、验证集评测和 Excel 生成；验收记录见 [PR 验收记录](pr-readiness.md)。

## 仍需后续演进

- 训练器和评估器仍由低氧工具调用专用解释器，外部训练脚本尚未拆成多个可替换实现。
- 工作流会话状态仍保存在进程内；后端重启后需要重新进入交互流程。
- 结果查询 API 和前端历史结果浏览仍可继续补充；当前评测完成后已能通过 `result_id` 复用 JSON 结果。
- 目录模型、配置模型和训练模型的前端分组展示仍依赖现有模型空间页面，空自定义分组和原生文件选择器可继续优化。
- 单机单进程部署；没有自动任务重试、异常退出后的孤儿任务恢复或多实例协调。旧模型缺少兼容性清单时需先补录可信元数据。

## 回退

```powershell
cd D:\code\SOTABand-refactor
git log --oneline --decorate -8
git revert <migration-commit>
```

基线目录 `D:\code\SOTABand` 的 `hypoxemia-baseline-v1` 分支不被本次修改触碰，可直接启动对照版本。
