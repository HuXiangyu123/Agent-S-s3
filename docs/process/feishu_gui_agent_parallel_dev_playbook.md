# 飞书 GUI Agent 并行开发执行规范

## 1. 目的

本文档回答一个问题：在多人和多 coding agent 协作下，如何把飞书 GUI Agent 做成“模块解耦、可并行实现、可 review、可回归”的工程。

相关文档：

- [文档索引](../README.md)
- [主方案](../feishu_gui_agent_master_plan.md)
- [Technical Spec](../spec/feishu_gui_agent_technical_spec.md)
- [Interface Doc](../interfaces/feishu_gui_agent_interfaces.md)

## 2. 并行开发前提

只有同时满足以下条件，才允许并行 coding：

1. 模块边界已经写入 `Technical Spec`
2. 输入输出契约已经写入 `Interface Doc`
3. 写入范围互不重叠
4. 已经完成模块级手动 plan

缺一项都不要并行。

## 3. 角色分工

- `Planner`：选择 workflow，绑定业务参数，保留前置条件和进入执行前断言。
- `Workflow`：定义运行时阶段推进、fallback、retry。
- `FeishuWorker`：串联模块，不承载业务规则。
- `Verifier`：输出标准化步骤级和用例级结果。
- `ReportBuilder`：只消费 `RuntimeContext`，不消费 `Worker` 私有状态。

## 4. 推荐拆分方式

### Track A

- `gui_agents/feishu/testcases/`
- `gui_agents/feishu/planner/`

目标：把自然语言稳定收敛为 `workflow + workflow_params + preconditions`

### Track B

- `gui_agents/feishu/pages/`
- `gui_agents/feishu/detectors/`
- `gui_agents/feishu/locators/`

目标：稳定产出 `FeishuState` 和 `LocatorResult`

### Track C

- `gui_agents/feishu/workflows/`
- `gui_agents/feishu/verifiers/`

目标：按单 workflow 落地阶段机和步骤级验证

### Track D

- `gui_agents/feishu/reports/`
- `gui_agents/feishu/maintenance/`

目标：沉淀 `RuntimeContext` 产物、截图、报告和维护能力

### Serial Track

- `gui_agents/feishu/agents/feishu_worker.py`
- `gui_agents/s3/agents/worker.py`
- `gui_agents/s3/agents/grounding.py`

目标：只在上游契约冻结后接入

## 5. 每个模块的手动 Plan 模板

每次 coding 前，plan 至少包含：

1. 目标文件
2. 依赖的上游契约
3. 本模块输出给谁消费
4. 最小验证方式
5. 风险和不做项

推荐格式：

```text
Module:
Owner:
Files:
Depends on:
Outputs:
Verification:
Out of Scope:
Risks:
```

## 6. 联调顺序

1. `Parser -> Planner`
2. `Pages/Detector -> Locator`
3. `Workflow -> Verifier`
4. `Worker -> RuntimeContext`
5. `ReportBuilder`

不要一开始就让 `Worker` 直接串所有模块。

## 7. 合并门禁

以下任一条件不满足，不合并：

1. 跨模块契约变更未同步更新文档
2. 没有最小验证样例
3. 同时修改高耦合文件和多个上游契约
4. `review` 不能说明失败归因如何进入 `failure_type`

## 8. Review 重点

Review 不要只看“能不能跑”，而要重点看：

1. 是否破坏模块边界
2. 是否引入新的隐式共享状态
3. 是否绕过 `RuntimeContext`
4. 是否把业务规则塞进 `Worker`
5. 是否让同一 workflow 被多个实现源共同定义

## 9. 当前建议执行顺序

1. 先冻结 `WorkflowPlan`（即 Planner output）、`ActionLog`、`StepResult`、`RuntimeContext`
2. 再做 `IM` 的单一 workflow 端到端打通
3. 再复制模式到 `Docs` 和 `Calendar`
4. 最后再做跨产品联动与自愈
