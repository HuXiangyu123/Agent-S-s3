# 飞书 GUI Agent 文档索引

## 1. 阅读顺序

1. [项目需求](./项目需求.md)
2. [Project State](./process/project_state.md)
3. [Requirements Coverage Audit](./process/requirements_coverage_audit_2026-05-06.md)
4. [主方案](./feishu_gui_agent_master_plan.md)
5. [PRD](./product/feishu_gui_agent_prd.md)
6. [Technical Spec](./spec/feishu_gui_agent_technical_spec.md)
7. [Interface Doc](./interfaces/feishu_gui_agent_interfaces.md)
8. [Implementation Records Index](./implementation/README.md)
9. [参考文档](#5-参考文档)
10. [Archive](./archive/)

补充阅读（按需查阅）：
- [Interface Compatibility](./interfaces/interface_compatibility.md)：API 兼容性与迁移指南
- [OSCAR State Verification](./spec/oscar_state_verification.md)：已实现的逐步骤状态验证设计
- [并行开发执行规范](./process/feishu_gui_agent_parallel_dev_playbook.md)：仅在明确启用并行 track 模式时使用；默认单 workspace 串行交付以 `AGENTS.md` 为准。

## 2. 文档职责

- `项目需求.md`：外部输入，定义竞赛题目和原始要求。
- `process/project_state.md`：当前项目实现状态、有效 runtime、已完成能力与下一步优先级。
- `process/requirements_coverage_audit_2026-05-06.md`：需求覆盖审计，区分 semantic/unit/runtime/live evidence。
- `feishu_gui_agent_master_plan.md`：唯一主设计文档，回答“整体怎么做”。
- `product/feishu_gui_agent_prd.md`：产品范围、阶段目标、验收口径，回答“做什么、做到什么程度”。
- `spec/feishu_gui_agent_technical_spec.md`：模块拆分、数据模型、并行开发边界，回答“工程上怎么落地”。
- `interfaces/feishu_gui_agent_interfaces.md`：内部模块契约，回答“模块之间如何对接”。
- `implementation/README.md`：实现记录索引，标明哪些文档是当前有效记录，哪些是历史迁移记录。
- `process/feishu_gui_agent_parallel_dev_playbook.md`：并行模式参考手册，不是当前默认交付流程。
- `../CONTRIBUTE.md`：仓库级贡献规范，回答“提交前要检查什么、PR 怎么提、并行开发怎么守规则”。
- `interfaces/interface_compatibility.md`：API 兼容性对照与迁移 check list，补充 interfaces 契约文档。
- `spec/oscar_state_verification.md`：已实现的 OSCAR 逐步骤状态验证设计，记录 worker.py 预期状态追踪机制。
- `archive/feishu_decisions_log.md`：Windows Feishu 开发关键决策记录（9 项已定决策）。
- `archive/feishu_test_log_2026-05-03.md`：2026-05-03 测试证据与根因分析。
- `archive/`：历史草案归档，不再作为主维护入口。

## 3. 推荐协作流程

1. 先看 `项目需求.md` 和 `master plan`，确认目标与架构边界。
2. 再看 `process/project_state.md` 和 `requirements_coverage_audit`，确认当前完成度和缺口。
3. 针对单个模块，先写手动 plan，再对照 `spec` 和 `interfaces` 校准边界。
4. 默认按 `AGENTS.md` 的单 workspace 串行流程交付；并行开发只有在明确切换时才查阅 parallel playbook。
5. plan 审阅通过后再 coding。
6. coding 后先做最小验证，再做 review。
7. 若改动影响跨模块契约，必须同步更新 `interfaces`。

## 4. 变更规则

- 产品范围或里程碑调整：更新 `PRD`。
- 架构、模块职责或并行开发边界调整：更新 `master plan` 和 `spec`。
- 输入输出、数据结构、调用方式调整：更新 `interfaces`。
- 当前状态或需求覆盖变化：更新 `process/project_state.md` 和 `process/requirements_coverage_audit_2026-05-06.md`。
- 新增实现记录：写入 `docs/implementation/`，并更新 `docs/implementation/README.md`。
- 过时设计稿移入 `archive/`；若保留在 `implementation/` 中作为迁移记录，必须在索引中标明历史状态。

## 5. 参考文档

- [openai_api_parameters.md](./llmapi/openai_api_parameters.md)：模型参数与推理配置参考。属于通用参考资料，不是当前飞书 GUI Agent 架构的 source of truth。
