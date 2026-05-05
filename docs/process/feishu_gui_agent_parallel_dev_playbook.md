# 飞书 GUI Agent 开发协作手册

本文件回答三个问题：**为什么拆 Track、单人怎么推、多人怎么分。**

架构边界看 `master_plan`，提交规范看 `CONTRIBUTE.md`，模块接口看 `interfaces/`，约束文件看 `AGENTS.md`。

相关文档：

- [主方案](../feishu_gui_agent_master_plan.md)
- [PRD](../product/feishu_gui_agent_prd.md)
- [Technical Spec](../spec/feishu_gui_agent_technical_spec.md)
- [Interface Doc](../interfaces/feishu_gui_agent_interfaces.md)
- [CONTRIBUTE.md](../../CONTRIBUTE.md)
- [项目需求](../项目需求.md)

---

## 1. Track 架构的设计动机

### 1.1 纯 VLM 直通的问题

当前的 VLM 模型能力已经足够覆盖 M1–M3 的端到端测试——截图 → VLM → 点击，能跑通。Track 架构不是为了让代码"能跑"，而是为了解决纯 VLM 直通无法解决的四个问题：

| 维度 | 纯 VLM 直通 | Track 架构 |
|------|:---:|:---:|
| **可解释性** | 失败时只有黑盒坐标，不知道根因 | 每步有 `failure_type` / `failure_reason` / `evidence` |
| **可复现性** | 同一指令两次运行路径可能不同 | `Planner` 确定性选 workflow，步骤序列固定 |
| **领域知识复用** | 飞书 UI 规律每次从 prompt 重新推导 | `PageDescriptor`、锚点表、弹窗行为编码在 Track B |
| **成本控制** | 每步都调 VLM | 规则/缓存兜底，VLM 只在视觉理解必要时介入 |

### 1.2 Track 拆分的核心思想

把飞书的**领域知识从 prompt 里搬到代码里**。

通用 VLM 不知道"飞书 IM 聊天页的发送按钮永远在输入框右侧"——这是领域事实。放在 prompt 里是一次性的，放在 `PageDescriptor` 里是所有 workflow 可复用的。

Track 架构本质上是做一个**领域知识的结构化编码层**，夹在"通用 VLM"和"飞书 GUI"之间。

### 1.3 各 Track 一句话职责

```
自然语言指令
    │
    ▼
┌─ Track A ─────────────────────┐  "把话说清楚"
│ testcases/ + planner/         │  NL → TestCase → WorkflowPlan
│ 纯数据，可全自动测试            │
└──────────────┬────────────────┘
               │ WorkflowPlan
               ▼
┌─ Track B ─────────────────────┐  "把屏看清楚"
│ pages/ + detectors/ +         │  截图 → FeishuState + LocatorResult
│ locators/                     │  需要真实飞书截图校准
└──────────────┬────────────────┘
               │ state + coords
               ▼
┌─ Track C ─────────────────────┐  "把事做清楚"
│ workflows/ + verifiers/       │  Plan + State → step-by-step 调度
│                               │  需要真实飞书验证阶段转换
└──────────────┬────────────────┘
               │ StepResult[]
               ▼
┌─ Track D ─────────────────────┐  "把结果记清楚"
│ reports/ + maintenance/       │  运行日志 → 报告 + 产物
│ 消费 log，不依赖 GUI            │
└──────────────┬────────────────┘
               │
               ▼
┌─ Serial ──────────────────────┐  "把链串清楚"
│ feishu_worker + S3 高耦合文件  │  端到端集成
│ 需要真实飞书全链路验证          │
└───────────────────────────────┘
```

---

## 2. 单人开发流程

当前默认模式：**单 workspace、串行交付、1 code 1 review。** 不采用多 worktree 并行 coding。

### 2.1 完整交付流程

```
1. 阅读 source of truth → 2. 写模块分析文档 → 3. 输出手动 plan
       ↓
4. coding → 5. 补充测试 → 6. 跑测试 → 7. 交 review → 8. 修正后提交
```

### 2.2 各步骤要求

| 步骤 | 产物 | 要求 |
|------|------|------|
| 1. 理解 | — | 读 spec、interfaces、现有实现，理解模块职责与上下游 |
| 2. 文档 | `docs/implementation/<topic>.md` | 模块职责、边界、关键交互、目标文件、实现方案、验证方案、风险 |
| 3. plan | plan 写入上述文档 | target files / depends on / outputs / verification / risks & rollback |
| 4. coding | 代码文件 | 放在 `gui_agents/feishu/<module>/` 下 |
| 5. 测试 | `tests/feishu/<module>/test_*.py` | 单元测试或模块级测试 |
| 6. 验证 | 测试结果 | 记录通过/失败/未运行项及原因 |
| 7. review | review 结论 | 关注正确性、边界、契约一致性、测试证据 |
| 8. 修正 | 提交 | 根据 review 修正后 commit |

### 2.3 Review 关注点

1. bug / behavioral regression
2. 模块边界是否被破坏
3. 契约是否与 `docs/spec`、`docs/interfaces` 一致
4. 测试是否真实执行，覆盖是否足够
5. fallback / failure handling 是否完整

风格问题优先级低于正确性、回归风险和测试证据。

---

## 3. 多人协作：Track 级分工

### 3.1 核心原则

**Track 之间文件不重叠，契约先冻结，不同人可以同时做不同 Track。**

Track A/B/C/D 各自操作独立的目录和文件：

| Track | 代码目录 | 测试目录 |
|-------|---------|---------|
| A | `gui_agents/feishu/testcases/` `gui_agents/feishu/planner/` | `tests/feishu/testcases/` `tests/feishu/planner/` |
| B | `gui_agents/feishu/pages/` `gui_agents/feishu/detectors/` `gui_agents/feishu/locators/` | `tests/feishu/pages/` `tests/feishu/detectors/` `tests/feishu/locators/` |
| C | `gui_agents/feishu/workflows/` `gui_agents/feishu/verifiers/` | `tests/feishu/workflows/` `tests/feishu/verifiers/` |
| D | `gui_agents/feishu/reports/` `gui_agents/feishu/maintenance/` | `tests/feishu/reports/` `tests/feishu/maintenance/` |
| Serial | `gui_agents/s3/agents/worker.py` `gui_agents/s3/cli_app.py` 等高耦合文件 | 集成测试 |

**共享文件**（所有人只读消费，修改走 freeze-v2 流程）：

- `gui_agents/feishu/contracts.py`
- `docs/spec/*`
- `docs/interfaces/*`

### 3.2 多人分支策略

多人协作时，每位开发者应在**各自本地开发环境**中，从同一 freeze SHA 切出自己的 feature 分支。

说明：

- 当前仓库默认模式仍是单人、单 workspace、1 code 1 review
- 只有在任务明确切换到多人 / 多 AI 并行模式时，才启用本节策略
- 不建议多人或多 AI 在同一个本地 workspace 中同时改代码

```bash
# 1. 团队负责人冻结 contracts → commit → push
# 2. 各开发者从 freeze commit 切分支
git checkout -b feat/track-a-<topic> <freeze-sha>
git checkout -b feat/track-b-<topic> <freeze-sha>
git checkout -b feat/track-c-<topic> <freeze-sha>
```

### 3.3 合流顺序

```
feat/track-a-*  ──┐
                   ├──► feat/TrackA-B ──► master
feat/track-b-*  ──┘
                   │
feat/track-c-*  ──┘ (A/B 合流后)
                   │
feat/track-d-*  ──┘ (C 合流后)
                   │
feat/serial-*   ──┘ (A/B/C/D 合流后)
```

合流规则：

1. 同 Track 内不同场景的扩展（如 IM send_message → IM create_group）可在同一分支上串行推进
2. 不同 Track 的开发者从同一 freeze SHA 切出后独立开发，各自测试通过后交 review
3. 合流前 rebase 到最新基线，解决冲突后重新跑测试
4. 合流顺序按 Track 依赖：A → B → C → D → Serial

### 3.4 典型三人分工示例

假设 Track A 的 IM send_message 基线已完成（当前状态），下一步扩展 IM 覆盖并启动 Track B：

| 人员 | Track | 工作内容 | 依赖 |
|------|-------|---------|------|
| 开发者 1 | Track A 扩展 | 创建群组、@提及、搜索消息记录的 TestCase/WorkflowPlan | 无 |
| 开发者 2 | Track B pages + detectors | IM 聊天主页、群组创建弹窗、@提及下拉的 PageDescriptor + FeishuState | 需要飞书截图 |
| 开发者 3 | Track B locators | VisionLocator 框架 + IM 页面锚点校准 | 需要开发者 2 的 PageDescriptor 契约 |

三人操作的文件互不重叠，无合并冲突。

### 3.5 手动测试的分工

Track A 可以全自动测试（NL → TestCase → WorkflowPlan 是纯数据变换），不需要飞书。

Track B/C/Serial 需要真实飞书验证，**由能看到飞书界面的队友负责**：

| 需要飞书的环节 | 谁做 |
|---------------|------|
| 截图采集（页面锚点校准用） | 有飞书桌面端的队友 |
| PageDescriptor 字段填写 | 看着飞书界面提取 |
| 端到端手动验证 | 有飞书桌面端的队友 |
| 纯代码/Track A/自动化测试 | 不需要飞书，谁都可以 |

---

## 4. Contract Freeze Gate

### 4.1 冻结时机

Track A + B + C 可以同时启动 coding 的前提：**共享契约已冻结**。它们依赖的是契约结构，不是彼此的代码实现。

### 4.2 最小冻结清单

- `FailureType`
- `ActionId` / `TargetId` / `AssertionId`
- `TestCase`
- `WorkflowPlan`
- `FeishuState`
- `PageDescriptor`
- `LocatorResult`
- `ActionLog`
- `StepResult`
- `RuntimeContext`
- 当前 track map
- 当前 milestone scope

### 4.3 冻结记录

冻结 PR 描述中至少包含：

- freeze SHA
- freeze 日期
- owner
- reviewer
- 受影响 tracks

### 4.4 解冻流程 (freeze-v2)

1. 标记变更源和受影响 track
2. 暂停受影响文件上的 coding
3. 先更新 `spec` 与 `interfaces`
4. 重新 review
5. 生成新的 freeze SHA
6. 相关分支 rebase 到新基线后再继续

---

## 5. Track 拆分与交接门禁

本节定义的是 **Track 边界、交接门禁和完成定义**，不表示这些 Track 在当前仓库状态里已经完成。
当前实际进度、已完成范围和下一步安排，请看 `docs/process/project_state.md` 与 `docs/implementation/`。

### 5.1 Track Map

| Track | 模块 | Consumes | Produces | Start Gate | Done Gate | Blocks |
| --- | --- | --- | --- | --- | --- | --- |
| A | `testcases/`, `planner/` | 项目需求、PRD | `TestCase`, `WorkflowPlan` | freeze 完成 | 结构、样例、失败输出固定 | C, Serial |
| B | `pages/`, `detectors/`, `locators/` | 页面知识、视觉事实 | `PageDescriptor`, `FeishuState`, `LocatorResult` | freeze 完成 | 页面、状态、定位返回固定 | C, D, Serial |
| C | `workflows/`, `verifiers/` | `WorkflowPlan`, `FeishuACI`, `FeishuState` | workflow 阶段机、`StepResult` | A/B 契约冻结 | stage、retry、failure_type 固定 | D, Serial |
| D | `reports/`, `maintenance/` | `RuntimeContext`, `ActionLog`, `StepResult` | `summary.json`, `report.md`, artifact 约定 | 运行时事实模型冻结 | 报告与产物结构固定 | Serial |
| Serial | `feishu_worker` + `s3` 高耦合文件 | A/B/C/D 稳定实现 | 端到端集成链路 | A/B/C 完成最小验证 | 从 plan 到 runtime context 全链路可跑 | 最终发布 |

### 5.2 Track A（testcases + planner）

内部顺序：`testcases/` → `planner/`

- `testcases/` 完成定义：schema、preconditions、assertions、正反例齐全
- `planner/` 完成定义：`WorkflowPlan`、workflow 选路、params、preconditions 透传、失败原因固定

### 5.3 Track B（pages + detectors + locators）

内部顺序：`pages/` → `detectors/` → `locators/`

- `pages/` 完成定义：`page_id`、anchor、detector 消费字段固定
- `detectors/` 完成定义：`FeishuState` 公共字段和扩展策略固定
- `locators/` 完成定义：成功/失败返回格式、`bbox` 格式、`page_id` 失败语义固定

### 5.4 Track C（workflows + verifiers）

内部顺序：`workflows/` → `verifiers/`

- `workflows/` 完成定义：stage、retry、fallback、阶段输出固定
- `verifiers/` 完成定义：`StepResult`、`failure_type`、断言失败语义固定

### 5.5 Track D（reports + maintenance）

内部顺序：`reports/` → `maintenance/`

- `reports/` 完成定义：`summary.json`、`report.md`、artifact path 固定
- `maintenance/` 进入条件：报告和产物结构稳定

### 5.6 Serial Track

只在最后启动。

start gate：A/B/C 完成模块级最小验证；高耦合文件 owner 明确。

done gate：端到端链路 `WorkflowPlan` → `RuntimeContext` 全链路可跑；关键失败路径落到统一 `failure_type`。

---

## 6. 依赖暂停矩阵

| 变更源 | 影响 | 停止范围 |
| --- | --- | --- |
| `TestCase` / `WorkflowPlan` | C, Serial | 暂停消费 plan 的文件 |
| `PageDescriptor` / `FeishuState` | B 下游, C, D, Serial | 暂停消费页面与状态结构的文件 |
| workflow stage / verifier 结果 | D, Serial | 暂停报告和集成相关文件 |
| `RuntimeContext` | D, Serial | 暂停所有运行时产物消费者 |

规则：

1. 只暂停受影响文件，不做全仓停工。
2. 受影响范围由契约 owner 判断。
3. 判断不清时按"受影响"处理。

---

## 7. 手动测试触发节点

并非所有阶段都需要启动飞书。以下标记各 Track 对手动测试的依赖：

| Track | 能全自动测试 | 需要飞书 |
|-------|:---:|:---:|
| A | ✅ NL → TestCase → WorkflowPlan 纯数据 | 不需要 |
| B pages | ⚠️ PageDescriptor 结构可自动 | 字段内容需要截图校准 |
| B detectors | ❌ | 需要真实截图验证状态识别 |
| B locators | ❌ | 需要真实飞书验证坐标 |
| C workflows | ⚠️ 阶段机逻辑可自动 | 阶段转换需要真实 UI 状态 |
| C verifiers | ⚠️ 断言逻辑可自动 | 验证结果需要真实截图对比 |
| D | ✅ 消费 log 数据 | 不需要 |
| Serial | ❌ | 端到端全链路必须真实飞书 |

**简单原则：Track A 和 D 不需要飞书，Track B 和 C 和 Serial 需要。** 由能看到飞书界面的队友负责这些验证。

---

## 8. 高耦合文件

以下文件即使在多人协作时也不应多人同时修改。

以 `AGENTS.md` 中的高耦合文件清单为最高优先级；本节是在当前实现下的补充提醒：

- `gui_agents/s3/agents/worker.py`
- `gui_agents/s3/agents/grounding.py`
- `gui_agents/s3/agents/grounding_feishu.py`
- `gui_agents/s3/agents/_feishu_exec.py`
- `gui_agents/s3/cli_app.py`
- `gui_agents/s3/memory/procedural_memory.py`
- `launcher.py`

这些文件属于 Serial Track，最后串行处理。

---

## 9. 分支与合流规则

### 9.1 分支命名

- 功能分支：`feat/track-<letter>-<topic>`（如 `feat/track-a-create-group`）
- 修复分支：`fix/<topic>`
- 集成分支：`feat/serial-<topic>`

### 9.2 合流流程

1. 在基线分支完成 freeze commit
2. 各开发者从同一 freeze SHA 切出 feature 分支
3. 独立开发并各自完成测试
4. 合并前 rebase 到最新基线
5. 通过 review 后按依赖顺序合并（A → B → C → D → Serial）

### 9.3 Rebase 规则

1. rebase 前先 `git status`
2. 有未提交改动先 commit 或 stash
3. rebase 改到已 review 的冲突区域时必须重新 review
4. 不接受未 rebase 到最新基线的陈旧 PR

### 9.4 特殊规则

如果旧分支和当前默认分支没有共同祖先，不做常规 rebase，改为从当前默认分支新切分支后手工移植需要的改动。

---

## 10. Review Gate Ladder

### Gate 1 Self-check

- 手动 plan
- 文档同步
- 最小本地验证
- 验证证据

### Gate 2 Module Review

- 模块边界是否被破坏
- 契约是否一致
- fallback / failure path 是否完整

### Gate 3 Integration Review

触发条件：涉及高耦合文件或多 track 合流。

- reviewer 独立于 owner
- 明确集成风险
- 明确回滚方式

---

## 11. 当前状态的记录位置

本手册是**稳定流程规范**，不记录阶段性实现进度、当前完成度或短期 next steps。

这类会持续变化的信息应记录到：

- `docs/process/project_state.md`
- `docs/implementation/`
- 或单次迭代 / review / dev log 文档

使用原则：

1. playbook 负责回答“为什么这样拆、多人怎么协作、何时冻结、如何合流”
2. `project_state.md` 负责回答“现在做到哪了、下一步做什么”
3. 模块实现细节与审阅证据放 `docs/implementation/`
