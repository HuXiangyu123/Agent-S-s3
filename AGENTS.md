# AGENTS

## Current Default Mode

当前项目默认采用 **单 workspace、串行交付、1 code 1 review** 模式，而不是多 track 并行 coding。

## Active Feishu Agent Principles

以下原则优先级高于后文历史 track / workflow 设计：

0. **Track ABCD 核心原则**：所有 Track 模块（`testcases/`、`tooling/`、`pages/`、`detectors/`、`locators/`、`verifiers/`、`reports/`）是 AgentS3 LLM agent loop 的 **agentic tool use 加速层**——提供领域知识、状态识别、元素定位提示和验证合约。Track ABCD 不是独立的确定性执行管线，任何时候不应串联为 `Parser -> Planner -> Workflow -> Step Executor` 绕过 AgentS3 的 LLM 决策。
1. 截图先验提取只沉淀语义信息，不沉淀坐标、比例、分辨率、bbox、confidence、score 等量化指标。
2. 新功能默认基于 `feishu_agent = AgentS3 + WindowsFeishuACI` 做 agentic prior / tool guidance 增强。
3. 不新增非 LLM 的确定性 runtime 路线，不把 `WorkflowPlan -> ordered steps` 接成产品执行路径。
4. 对新产品模块，优先交付页面语义、状态识别、工具选择提示、失败/弹窗语义；不要为了测试方便设计固定点击流程。
5. 不新增产品级 workflow 契约；测试/审阅辅助也必须表达为 semantic guidance、fixture、verifier 或 report，不作为 runtime controller。
6. Base、Docs、Calendar、VC 等新增产品域默认只进入 `feishu_agent` 的语义先验层；不得新增 `create_xxx` 固定 workflow 作为用户任务执行路线。
7. Base、VC 及后续新增截图 metadata 不允许包含 `relative_bounds`、`bbox`、`confidence`、`score`、`resolution`、`image_width`、`image_height`、像素坐标或比例字段。

角色分工固定为：

- `Codex`: 负责 `analysis -> plan -> docs -> coding -> testing`
- `Claude Code`: 负责 review

## Session Startup Check

每个新的 coding session 启动时，必须先执行 agent 启动自检：

```bash
python -m unittest tests.test_agent_startup -v
```

自检通过才允许进入 coding。如果自检失败，先修复再继续。

启动自检覆盖：
- Feishu domain layer 全部模块可导入
- S3 execution layer 可导入
- `feishu_agent` 路由和 semantic prior/tool guidance 核心链路可用
- 所有已有 feishu 测试通过

## Local CI Parity Check

提交前必须执行与 GitHub workflow 对齐的本地检查：

```bash
python scripts/run_ci_checks.py
```

该入口负责统一执行：

- `black --check launcher.py gui_agents tests`
- `python -m unittest tests.test_agent_startup -v`
- `python -m unittest tests.test_launcher_env_config -v`

原则：

- 本地未通过，不提交
- GitHub workflow 必须直接复用同一个入口，避免本地和 CI 分叉
- 若在 Windows shell 查看中文文档或测试文件，优先显式使用 UTF-8 读取，避免把正常 UTF-8 内容误判为乱码

当前默认要求：

1. 每次进入模块实现前，先理解模块职责、边界、上下游交互和当前实现现状。
2. 理解完成后，先写手动 plan，再进入 coding；不允许跳过 plan 直接写代码。
3. coding 前必须把本次模块分析、设计取舍、目标文件、验证方式等落文档到 `docs/` 下。
4. coding 完成后必须先测试，再交 review。
5. 测试时要跑该模块相关测试，以及仓库内现有测试脚本；新增模块测试统一放到独立 `tests/` 目录或其子目录下，不把临时测试散落到业务目录。
6. 当前默认不采用多 AI 同时改同一 workspace 的并行 coding；如确需并行，必须显式切换到后文的并行模式约束。

## Rule Priority

规则优先级按下面顺序解释：

1. 本文档开头的 `Current Default Mode`、`Core Rules`、`Standard Delivery Flow`、`Documentation Rule`、`Testing Rule`
2. source of truth 文档中的模块边界与共享契约
3. 后文并行开发 / worktree / merge 规则

解释原则：

- 如果后文旧并行规则与当前单 workspace 模式冲突，以开头的新默认规则为准。
- 只有任务明确切换到并行 track 模式时，后文并行规则才提升为当前有效规则。

## Purpose

本仓库是基于 `Agent-S` 的飞书桌面端 GUI Agent 二次开发。
当前主线路线是 `Windows + 飞书桌面端 + GUI-first`，不是飞书开放平台 CLI、bot 或 API-first。

## Source Of Truth

涉及需求、架构、模块边界时，按下面顺序阅读：

1. `docs/项目需求.md`
2. `docs/feishu_gui_agent_master_plan.md`
3. `docs/product/feishu_gui_agent_prd.md`
4. `docs/spec/feishu_gui_agent_technical_spec.md`
5. `docs/interfaces/feishu_gui_agent_interfaces.md`
6. `CONTRIBUTE.md`

## Core Rules

1. 任何模块改动都走 `analysis -> manual plan -> coding -> review`。
2. 人和模型都理解手动 plan 之前，不进入 coding。
3. `Codex` 负责 plan and code，`Claude Code` 负责 review；默认是一写一审，不做同 workspace 并行 coding。
4. 每次模块开工前，必须先输出模块分析文档到 `docs/` 下，再进入 coding。
5. 模块分析文档至少写清：模块职责、边界、关键交互、目标文件、实现方案、验证方案、风险。
6. 共享契约变更时，文档必须与实现同 PR 或更早落地。
7. Feishu 业务逻辑优先落在 `gui_agents/feishu/`，不要持续污染 `gui_agents/s3/`。
8. 默认假设飞书开放平台能力不可用，除非任务明确要求。
9. coding 完成后必须执行测试；能跑的测试脚本都要跑，并补充模块级测试到独立 `tests/` 目录。

## Standard Delivery Flow

每次模块实践按下面顺序执行：

1. 阅读 source of truth 和现有实现，理解模块功能、上下游依赖和失败路径。
2. 在 `docs/` 下写本次模块分析/实现文档。
3. 输出手动 plan，至少包含：
   - target files
   - depends on
   - outputs
   - verification
   - risks / rollback
4. 进入 coding。
5. 在 `tests/` 目录补充或更新模块测试。
6. 跑相关测试与现有测试脚本，记录结果。
7. 交给 `Claude Code` review。
8. 根据 review 结论修正后再提交。

输出要求：

- `docs/` 下必须有本次模块分析/实现文档
- `tests/` 下必须有新增或更新的模块测试（如果该模块适合自动化测试）
- review 前必须给出实际测试结果、未运行项和原因

## Documentation Rule

模块实现前必须先留文档，默认落在 `docs/` 下，建议按主题建子目录，例如：

- `docs/implementation/`
- `docs/process/`
- 或与模块同主题的专项文档

文档不是事后补；它是 coding 的前置产物。

## Testing Rule

1. 新增或重构模块时，优先在独立 `tests/` 目录下补测试，不要把测试脚本散落在运行时代码目录。
2. 模块完成后至少执行：
   - 该模块直接相关测试
   - 仓库已有相关测试脚本
   - 若存在统一测试入口，则一并执行；当前统一入口为 `python scripts/run_ci_checks.py`
3. 如果某些测试因为环境或依赖无法运行，必须在 review 证据里明确写出未运行项与原因。

## Review Rule

`Claude Code` 的 review 默认关注：

1. bug / behavioral regression
2. 模块边界是否被破坏
3. 契约是否与 `docs/spec`、`docs/interfaces` 一致
4. 测试是否真实执行，覆盖是否足够
5. fallback / failure handling 是否完整

review 不是只看代码风格；风格问题优先级低于正确性、回归风险和测试证据。

## Contract Freeze Gate

以下规则仅在**明确启用并行 coding / 多 track 开发**时生效；当前默认单 workspace 模式下不自动启用。

并行 coding 的启动条件不是“别人代码写完了”，而是“共享契约冻结了”。

冻结至少包含：

- `docs/spec/`
- `docs/interfaces/`
- track 拆分与依赖关系
- 当前 milestone scope

冻结记录至少包含：

- freeze commit SHA
- freeze 日期
- owner
- reviewer

冻结后如果共享契约还要改，按 `freeze-v2` 处理：

1. 暂停受影响 track 的相关文件开发。
2. 先更新 spec/interfaces。
3. 重新 review。
4. 再恢复 coding。

## Ownership Boundaries

以下默认轨道只在并行模式下使用，不是当前默认开发模式。

默认并行轨道：

- `Track A`: `gui_agents/feishu/testcases/` -> `gui_agents/feishu/tooling/`
- `Track B`: `gui_agents/feishu/pages/` -> `gui_agents/feishu/detectors/` -> `gui_agents/feishu/locators/`
- `Track C`: `gui_agents/feishu/verifiers/`
- `Track D`: `gui_agents/feishu/reports/` -> `gui_agents/feishu/maintenance/`
- `Serial Track`: `s3` 高耦合集成文件 (执行统一走 `AgentS3` LLM 循环，无独立 FeishuWorker)

默认顺序：

1. 第一波并行 `Track A + Track B + Track C`
2. `Track D` 在运行时事实模型稳定后接入
3. `Serial Track` 最后做总装

## High-Coupling Files

以下文件默认串行开发，并且需要集成级 review；即使启用并行模式也不应多人同时修改：

- `gui_agents/s3/agents/worker.py`
- `gui_agents/s3/agents/grounding.py`
- `gui_agents/s3/cli_app.py`
- `gui_agents/s3/memory/procedural_memory.py`
- `gui_agents/feishu/agents/__init__.py`

## Planning Standard

每个模块开工前都要有短 plan，至少包含：

- target files
- owner
- depends on
- outputs
- verification
- risks / rollback

## Worktree Rules

以下规则只在明确启用并行 coding 时使用。

1. 默认分支当前是 `master`，它是集成基线，不是日常功能开发分支。
2. `master` worktree 保持干净，只做同步、冻结、集成检查。
3. 一个 worktree 只对应一个活跃分支。
4. 一个分支只在一个 worktree 中主动开发。
5. 开新 worktree 前先看 `git worktree list`。
6. 合并完成后及时 `git worktree remove` 清理废弃 worktree。
7. 需要临时联调或修补时，新开 `review/<topic>` 或 `fix/<topic>`，不要直接在 `master` worktree 改。
8. 如果旧分支和当前默认分支没有共同祖先，不要直接 `rebase`，改为从当前默认分支新切分支后手动移植改动。

## Merge And Review Rules

以下合流规则只在并行模式下使用；当前默认单 workspace 模式仍按 `plan -> code -> test -> review` 串行推进。

1. 先冻结契约，再切并行分支。
2. A/B/C 从同一个 freeze SHA 切出。
3. track 分支合并前先同步默认分支，再 rebase 到最新基线。
4. rebase 改到了已 review 的冲突区域，必须重新 review。
5. `Serial Track` 从 A/B/C/D 合入后的新基线切出，并最后合并。

Review 分三层：

- Gate 1 Self-check: plan、最小验证、证据齐全
- Gate 2 Module review: 看边界、契约、失败路径
- Gate 3 Integration review: 高耦合文件或多 track 合流必过

## Delivery Standard

每个完成模块都应交付：

- 明确边界
- 成功判定或 verifier
- fallback / failure handling
- 最小回归证据
- 简短 review 结论与剩余风险
