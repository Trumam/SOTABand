# 低氧血症文档入口

第一次使用，请从[从零安装与完整操作指南](hypoxemia-operation-guide.md)开始。该指南包括依赖安装、API 配置、前后端启动、逐项按钮与参数说明，以及三个可以照着操作的合成数据示例。

| 文档 | 适合谁、解决什么问题 |
| --- | --- |
| [从零安装与完整操作指南](hypoxemia-operation-guide.md) | 使用者：从下载源码到处理、训练、保存、重载评测及 Excel 下载 |
| [架构与扩展说明](hypoxemia-admin-guide.md) | 管理员和开发者：模块边界、运行组件、来源与扩展方式 |
| [运行依赖与交付说明](hypoxemia-runtime-and-delivery.md) | 部署人员：依赖锁文件、两个 Python 环境、可选 GPU 和交付限制 |
| [运行目录与端口隔离](migration-runtime-isolation.md) | 同机保留多份检出的人员：避免连错服务或混用产物 |
| [迁移状态](migration-status.md) | 开发者：目前的代码归属和后续工作 |
| [验收记录](pr-readiness.md) | 审查者：实际命令、结果、证据与未验证范围 |
| [历史版本对比](sotaband-version-comparison.md) | 查阅旧提交的改造背景；其中统计和待办不是当前状态 |

原 `docs/` 顶层的低氧指南、迁移记录和版本对比已归并到本目录。通用平台设计文档仍在 `docs/`。本目录原有的 `迁移prompt.md`、`一些感想.md` 保持原内容。
