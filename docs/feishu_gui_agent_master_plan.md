# 飞书 GUI Agent 主方案

## 1. 目标

本方案直接服务 [项目需求.md](./项目需求.md)。

配套文档：

- [文档索引](./README.md)
- [PRD](./product/feishu_gui_agent_prd.md)
- [TECH SPEC](./spec/feishu_gui_agent_technical_spec.md)
- [INTERFACE DOC](./interfaces/feishu_gui_agent_interfaces.md)

当前目标不是做飞书 bot 或开放平台套壳，而是做一个面向飞书桌面端的 GUI 测试 Agent，覆盖以下必做能力：

1. 视觉感知
2. 语义理解
3. 自主操作
4. 状态验证
5. 评估报告

当前主路线：

- `Windows + 飞书桌面端 + GUI-first`
- `code agent` 仅做内容生成和局部辅助
- 开放平台 / bot / CLI 不进入当前主链

## 2. 需求映射

项目需求中的 5 个必做能力，对应当前架构应映射为：

- 视觉感知 -> `StateDetector` + `PageRegistry` + `Visual Anchor`
- 语义理解 -> `NL Testcase Parser` + `Tool Router / Guidance`
- 自主操作 -> `FeishuACI` + `gui_agents/s3/`
- 状态验证 -> `Verifier`
- 评估报告 -> `ReportBuilder` + `artifacts/test_runs/`

项目需求中的关键范围，对应当前优先级为：

- 子产品优先级：`IM -> Docs -> Calendar`
- 先做桌面 GUI 主路径
- 至少 2 个子产品覆盖
- 后续再做跨产品联动、自愈、录制回放

## 3. 主架构

```text
Natural Language Test Case
  -> NL Testcase Parser
  -> Tool Router / Domain Guidance
  -> AgentS3 + WindowsFeishuACI (LLM-driven agent loop)
      -> StateDetector / PageRegistry / Locator hints
      -> Verifier hints
  -> S3RuntimeRecorder
  -> ReportBuilder
  -> Structured Test Report
```

职责边界：

- `NL Testcase Parser`：把自然语言测试描述转成结构化测试用例
- `Tool Router / Domain Guidance`：按当前截图状态和意图提供可用工具、页面语义、下一步关注点
- `StateDetector`：给出当前页面和关键状态
- `Locator`：决定元素定位策略
- `FeishuACI`：把语义动作落成 GUI 操作
- `Verifier`：提供断言判定，不控制下一步 action
- `ReportBuilder`：生成结构化结果与可读报告

## 3.1 Track ABCD 核心原则：Agentic Tool Use，非确定性执行链

Track ABCD 的所有模块（`testcases/`, `tooling/`, `pages/`, `detectors/`, `locators/`, `verifiers/`, `reports/`）服务于唯一目标：**在 AgentS3 LLM agent loop 基础上，通过 agentic tool use 加速识别、定位和验证任务。**

### Track ABCD 是 Agent 的知识/工具层，不是独立执行路线

每个 Track 模块的角色：

- **Track A** (`testcases/` + `tooling/`)：将自然语言转为结构化意图提示和工具指导，供 Agent 理解任务目标。
- **Track B** (`pages/` + `detectors/` + `locators/`)：提供页面语义描述、状态识别、元素定位提示——Agent 按当前截图状态自行决策，不按固定坐标/流程。
- **Track C** (`verifiers/`)：提供成功判定合约和失败归因，不提供 runtime 阶段机。
- **Track D** (`reports/` + `maintenance/`)：被动记录 Agent 执行轨迹并生成产物，不控制执行流程。

### 严禁事项

1. Track ABCD 模块不得串联为 `Parser -> Planner -> Workflow -> Step Executor` 的确定性执行管线。
2. Track ABCD 不得绕过 AgentS3 的 LLM 决策循环，自行决定下一步 action。
3. 不得新增或恢复 `WorkflowPlan -> ordered steps`、`workflow.steps()`、固定阶段机 executor 等产品运行路径。
4. 任何模块不得引入硬编码坐标、固定点击流程、或假设特定 UI 分辨率/布局。
5. 截图抽取信息只保留语义事实，例如可见控件、页面类型、弹窗状态、文字锚点；不得记录坐标、相对范围、置信度、图片尺寸等量化图像指标。

### 正确使用方式

```text
用户指令
  -> NL Parser (结构化意图提示)
  -> AgentS3 LLM loop (每一步由 LLM 决策)
      ├─ 截图 -> StateDetector (当前页面/状态识别)
      ├─ 截图 -> Locator (元素定位建议)
      ├─ Tool Router (按当前状态推荐可用工具子集)
      └─ LLM 生成 action code -> 执行
  -> S3RuntimeRecorder 被动记录
  -> ReportBuilder 聚合产物
```

## 4. 建议目录

```text
gui_agents/feishu/
  __init__.py
  agents/
    __init__.py
  detectors/
    __init__.py
    state_detector.py
  tooling/
    __init__.py
    tool_router.py
  testcases/
    __init__.py
    nl_parser.py
    scenario_schema.py
  verifiers/
    __init__.py
    completion_gate.py
  locators/
    __init__.py
    vision_locator.py
    accessibility_locator.py
    hybrid_locator.py
  pages/
    __init__.py
    registry.py
  reports/
    __init__.py
    report_builder.py
    models.py
  maintenance/
    __init__.py
    anchor_validator.py
    screenshot_recorder.py
```

## 5. 语义意图与工具指导层规格

这是当前方案里必须补齐的一层，不能只保留名字。

### 5.1 `NL Testcase Parser`

输入：

- 自然语言测试描述

输出：

- 结构化 `TestCase`

最低要求：

1. 识别目标子产品
2. 识别任务意图
3. 识别关键输入参数
4. 识别断言目标
5. 支持多步骤串联，不只支持单动作

### 5.2 `Tool Router / Domain Guidance`

输入：

- `TestCase`
- 当前运行上下文

输出：

- product / intent / action hint
- preferred tools
- next-step focus
- preconditions 透传结果
- entry assertions
- 失败原因

最低要求：

1. 根据自然语言、当前截图语义和 `FeishuState` 给出工具子集建议。
2. 不输出固定步骤序列，不负责运行时 `fallback` / `retry` / `next_step`。
3. 不命中时返回人工可审阅的失败原因。
4. 所有产品任务继续交由 `feishu_agent` 的 AgentS3 LLM loop 决策和执行。

## 6. 测试用例模型

当前必须支持多步骤串联场景。

建议最小模型：

```json
{
  "id": "tc_im_send_message_001",
  "product": "im",
  "title": "在测试群发送消息并验证发送成功",
  "preconditions": [
    "飞书桌面端已登录"
  ],
  "steps": [
    {
      "action": "open_chat",
      "target": "测试群"
    },
    {
      "action": "type_message",
      "payload": {
        "text": "Hello World"
      }
    },
    {
      "action": "send_message"
    }
  ],
  "assertions": [
    "chat_title_matched",
    "message_sent"
  ],
  "artifacts": {
    "collect_screenshots": true
  }
}
```

这个模型要能扩到：

- `Docs`：创建文档 -> 输入标题 -> 插入列表 -> 验证文档存在
- `Calendar`：打开日历 -> 创建日程 -> 邀请参会人 -> 验证创建成功
- 跨产品：IM 收到邀请 -> 跳日历确认 -> 返回 IM 验证状态

## 7. 定位层与 Electron 接入口

当前主定位策略仍然是视觉优先，但必须预留混合定位接入口。

建议定位层接口：

```text
Locator
  -> VisionLocator
  -> AccessibilityLocator
  -> HybridLocator
```

说明：

- `VisionLocator`：当前主路径，基于截图、OCR、VLM、视觉锚点
- `AccessibilityLocator`：未来接 Electron / Accessibility Tree / 原生可访问性信息
- `HybridLocator`：融合视觉与可访问性候选结果

当前要求：

1. 架构上必须有 `locators/` 目录和统一接口
2. 当前实现可以先只落 `VisionLocator`
3. 不要求当前版本就依赖 Accessibility，但不能把接入口堵死

## 8. 工具指导与 verifier

当前 runtime 不再实现产品级固定 workflow。任务推进由 `feishu_agent` 的 LLM loop 基于当前截图、状态识别和工具指导逐步决策。

工具指导示例：

```text
IM send message intent
  -> preferred_tools: [click, type, hotkey]
  -> next_step_focus: message_input
  -> verification_hints: [chat_title_matched, message_sent]
```

`Verifier` 最少要支持：

- 当前页面是否正确
- 当前目标对象是否正确
- 本步动作是否成功
- 整条用例是否完成

## 9. 报告层

项目需求里的“评估报告层”是必做项，因此必须从第一阶段就开始设计。

建议测试产物结构：

```text
artifacts/
  test_runs/
    2026-05-04_153000/
      screenshots/
      actions.jsonl
      summary.json
      report.md
```

`summary.json` 建议最少包含：

- `task_id`
- `product`
- `intent`
- `status`
- `steps`
- `duration_sec`
- `assertions`
- `failure_type`
- `failure_reason`

`report.md` 建议最少包含：

- 用例描述
- 执行轨迹摘要
- 验证结果
- 成功率 / 耗时 / 步骤数

## 10. 收缩后的里程碑

### M0：运行基线

- 启动稳定
- 截图和日志可留存
- 有固定 smoke case

### M1：单步验证

只做需求里的单步能力验证，不上固定多步 workflow。

目标：

- 截图 -> 识别 -> 单步点击
- 截图 -> 识别 -> 单步输入
- 至少 5 个单步操作可重复验证

验收：

- 对应 `项目需求.md` 的 M1

### M2：单产品流程串联

目标：

- 先只做 `IM`
- 基于 `feishu_agent` 的发送消息、发送文件或表情回复语义指导
- `Verifier`
- 最小 `ReportBuilder`

验收：

- 完成 1 个子产品的 3 条端到端测试流程

### M3：多产品覆盖

目标：

- `IM`
- `Docs`
- `Calendar`

验收：

- 至少 2 个子产品稳定可跑
- 向 IM / Calendar / Docs 各有 2+ 用例靠拢

### M4：评估体系

目标：

- regression runner
- 结构化报告
- 成功率 / 耗时 / 步骤数统计

验收：

- 满足需求里的评估报告层

### M5：进阶能力

目标：

- 异常处理
- 自愈式执行
- 跨产品联动
- 录制回放

验收：

- 至少落地 1-2 项

## 11. 文档边界

当前文档职责收敛为：

- [feishu_gui_agent_master_plan.md](./feishu_gui_agent_master_plan.md)：唯一主方案
- `docs/product/`：产品文档
- `docs/spec/`：技术规格
- `docs/interfaces/`：接口文档
- `docs/archive/`：历史设计稿归档，不再作为主维护入口

## 12. 归档说明

以下原文件已转为归档参考：

- [archive/feishu_secondary_dev_guide.md](./archive/feishu_secondary_dev_guide.md)
- [archive/feishu_tools_skills_architecture.md](./archive/feishu_tools_skills_architecture.md)

## 13. 执行治理

`master_plan` 负责回答“做什么、为什么这样拆”，并行开发的具体操作以 [并行开发 Playbook](./process/feishu_gui_agent_parallel_dev_playbook.md) 为准。

本方案的 milestone 推进受以下门禁约束：

1. 进入任何并行开发阶段前，必须先完成共享契约冻结。
2. Track 内部必须按 handoff gate 串行推进，不能因为“理解差不多了”就提前并写下游模块。
3. 高耦合文件和多 track 合流必须经过集成级 review。
4. `Serial Track` 只在上游 tracks 完成最小验证后启动。

里程碑入口标准：

- M0 / M1：基础运行链路可启动，最小 smoke case 可复现
- M2：`TestCase`、`FeishuToolGuidance`、`FeishuState`、`LocatorResult`、`StepResult` 已冻结
- M3：至少一个单产品 agentic tool guidance 路径已经稳定，运行时事实模型可复用
- M4：`RuntimeContext` 与报告产物结构已冻结
- M5：前序链路稳定，允许引入更复杂的异常恢复与跨产品联动

里程碑退出标准：

- 有明确验收结果
- 对应契约与实现一致
- 最小验证证据可追溯
- 剩余风险已经在 review 或 follow-up 中记录
