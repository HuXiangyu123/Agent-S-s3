# Track A Foundation (2026-05-05)

## Status

Historical implementation record. The fixed `WorkflowPlan` / planner output
described here was removed by
`docs/implementation/feishu_agent_migration_remove_workflows_2026-05-06.md`.
Current Track A output is semantic intent and tool guidance for
`feishu_agent`, not an executable workflow plan.

## Goal

为 `gui_agents/feishu/` 建立 Track A 的最小可用基础层，覆盖：

- `testcases/`
- `planner/`

本轮目标不是接入真实飞书执行链，而是先把自然语言测试输入收敛为可消费的结构化 `TestCase` 与 `WorkflowPlan`，为后续 `workflows/`、`verifiers/`、`feishu_worker` 提供稳定接口。

## Source Of Truth

本轮实现遵循以下文档：

1. `docs/项目需求.md`
2. `docs/feishu_gui_agent_master_plan.md`
3. `docs/product/feishu_gui_agent_prd.md`
4. `docs/spec/feishu_gui_agent_technical_spec.md`
5. `docs/interfaces/feishu_gui_agent_interfaces.md`
6. `AGENTS.md`

## Scope

### In Scope

- 创建 `gui_agents/feishu/` 包基础结构
- 冻结 Track A 直接消费与产出的共享 contracts
- 实现最小 `NL Testcase Parser`
- 实现最小 `Workflow Selector / Planner`
- 为 IM `send_message` 主路径提供正例支持
- 为无法命中 workflow 的输入提供结构化失败输出
- 在 `tests/` 下补充 Track A 自动化测试

### Out Of Scope

- `pages/`、`detectors/`、`locators/`
- `workflows/`
- `verifiers/`
- `feishu_worker`
- 真实 GUI 操作
- 基于飞书截图的状态知识库

## Module Boundaries

### `testcases/`

职责：

- 接收自然语言 `instruction`
- 解析出 `product`、`title`、`steps`、`preconditions`、`assertions`
- 输出与接口文档一致的结构化 `TestCase`
- 做最小 schema 校验与标准化

不负责：

- workflow 选择
- 运行时 fallback / retry
- GUI 侧状态判断

### `planner/`

职责：

- 根据 `TestCase` 和可选 `FeishuState` 选择显式 workflow
- 绑定 `workflow_params`
- 透传 `preconditions`
- 产出 `entry_assertions`
- 若未命中，返回结构化 `failure_type` / `failure_reason`

不负责：

- `next_step`
- 运行时阶段推进
- fallback / retry
- 实际执行前置条件

## Contracts To Freeze In Code

本轮需要在代码中显式落下的最小共享契约：

- `FailureType`
- `ActionId`
- `TargetId`
- `AssertionId`
- `TestCase`
- `WorkflowPlan`

同时为后续模块预留但不实现的结构：

- `PageDescriptor`
- `FeishuState`
- `LocatorResult`
- `ActionLog`
- `StepResult`
- `RuntimeContext`

原因：

- 当前 `gui_agents/feishu/` 目录还不存在，直接把 contracts 放进代码可以减少后续 Track B/C 的字段漂移
- 这些契约已经在 `spec/interfaces` 中冻结为当前里程碑的 source of truth

## Planned Files

### Code

- `gui_agents/feishu/__init__.py`
- `gui_agents/feishu/contracts.py`
- `gui_agents/feishu/testcases/__init__.py`
- `gui_agents/feishu/testcases/scenario_schema.py`
- `gui_agents/feishu/testcases/nl_parser.py`
- `gui_agents/feishu/planner/__init__.py`
- `gui_agents/feishu/planner/workflow_selector.py`
- `gui_agents/feishu/planner/task_planner.py`

### Tests

- `tests/feishu/testcases/test_nl_parser.py`
- `tests/feishu/planner/test_task_planner.py`

## Implementation Strategy

1. 先在 `contracts.py` 中定义 TypedDict / type alias，避免后续模块围绕裸字典各自发挥。
2. `scenario_schema.py` 提供：
   - 标准化
   - 校验
   - 生成稳定 `id`
3. `nl_parser.py` 先做规则驱动版本，优先支持 IM `send_message`。
4. `workflow_selector.py` 只做显式 workflow 命中，不引入黑盒自由规划。
5. `task_planner.py` 负责把 selector 输出包装成完整 `WorkflowPlan`。

## Verification Plan

自动化测试至少覆盖：

1. 自然语言 IM 发消息指令 -> 结构化 `TestCase`
2. 缺省字段自动补齐：`step_id`、`payload`、`preconditions`
3. `send_message` workflow 命中成功
4. 未命中 workflow -> 返回 `failure_type="precondition"` 或等价结构化失败
5. planner 透传 `preconditions`
6. planner 输出不包含 runtime 级字段，如 `fallback` / `retry_limit`

## Risks

1. 规则 parser 过度写死中文表达，后续扩展 Docs / Calendar 时需要重构。
2. 过早把 runtime 语义塞进 planner，会与 Track C 的 workflow 责任冲突。
3. contracts 如果定义得过细，Track B/C 后续改动半径会变大。

## Rollback

如果本轮实现被证明边界不合理，回滚优先级如下：

1. 保留 `contracts.py`
2. 回滚 `nl_parser.py` 的具体规则
3. 回滚 `workflow_selector.py` 的命中策略
4. 保留测试作为契约证据

## Screenshot Dependency

本轮 Track A 不依赖飞书截图知识。

后续如果出现以下需求，再请人工补本地截图资产：

- 基于页面锚点反推更细的 `TargetId`
- 为 Docs / Calendar 的自然语言步骤补更具体的业务词典
