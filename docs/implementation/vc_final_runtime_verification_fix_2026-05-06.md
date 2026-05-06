# VC Final Runtime Verification Fix

## Background

当前 `feishu_agent` 路线在 live VC 场景里已经可以通过大模型 + agentic tools 完成操作，但在任务末尾生成 `Track D` 报告时，存在“agent 已输出 `done`，最终 `summary/report` 仍标记 `failed`”的问题。

本次定位基于以下运行产物：

- `artifacts/test_runs/s3_feishu_20260506_143929_9bf3c9a9`
- `artifacts/test_runs/s3_feishu_20260506_144554_02fda0f0`

## Current Behavior

当前链路：

1. `gui_agents/s3/cli_app.py::run_agent()` 在每轮循环开始抓取一次 `obs`
2. agent 返回 `done` 后立即 `break`
3. `finally` 中调用 `recorder.finalize(..., final_observation=obs)`
4. `gui_agents/feishu/reports/s3_runtime_recorder.py::_record_final_assertions()` 使用 `detect_vc_state(final_observation)` + `AssertionVerifier.verify_assertion(...)`
5. 若 detector 无法从最终截图稳定识别 `vc_meeting_active` / `vc_invite_dialog`，则最终报告翻成 `failed`

## Root Cause

本问题不是单纯的 markdown/report 渲染错误，而是最终验证语义过度依赖单帧截图 detector。

已确认的具体问题：

1. `run_agent()` 传给 `recorder.finalize()` 的 `final_observation` 通常是当前轮推理前抓到的截图，不保证是 `done()` 之后的最新界面。
2. live VC 截图 OCR 质量不稳定，`detect_vc_state()` 在最终截图上容易返回 `page_type=unknown`。
3. `S3RuntimeRecorder` 在 final assertion 阶段没有利用运行时已知事实，只要 detector 判不出来，就直接把整次 run 标成 verification failed。

## Scope

本次修复只处理 `feishu_agent` 路线下的最终验证可靠性，不引入非 LLM 固定 workflow，不改变主 agent 的决策方式。

## Target Files

- `gui_agents/s3/cli_app.py`
- `gui_agents/feishu/reports/s3_runtime_recorder.py`
- `tests/feishu/reports/test_s3_runtime_recorder.py`
- `tests/feishu/reports/test_s3_cli_recorder_integration.py`

## Design

### 1. Refresh final observation after terminal action

当 agent 返回 `done` / `fail` 时，在进入 `recorder.finalize()` 之前补抓一帧新的最终 observation，避免 final assertion 继续用动作前的旧截图。

### 2. Add runtime semantic hints for final assertions

在 `S3RuntimeRecorder` 内维护最小运行时语义 breadcrumbs，只记录动作语义，不记录坐标或图片量化信息。

计划支持的 VC 提示：

- 当前 run 的 `task_id`
- 最近一次 `done` 动作
- 最近一次成功执行的关键 action 语义
- 对 VC 任务的最小 terminal hint，例如：
  - `agentic_vc_start_meeting` 且以 `done` 结束，可作为 `meeting_active` 的弱确认来源
  - `agentic_vc_open_invite_dialog` 且以 `done` 结束，可作为 `invite_dialog_visible` 的弱确认来源

该 hint 只在最终 detector 仍无法稳定分类时使用，优先级低于显式 metadata 和 detector 命中。

### 3. Keep verification on feishu_agent path

不恢复 `feishu_workflow` 或其他固定流程执行器；最终报告仍属于 agent 路线的事后验证增强。

## Verification Plan

1. 单测：
   - `S3RuntimeRecorder` 在 detector 失败但 runtime hint 明确时仍可输出 `completed`
   - `run_agent()` 在 `done()` 后会把 fresh final observation 传给 recorder
2. 集成测试：
   - `python -m unittest tests.feishu.reports.test_s3_runtime_recorder`
   - `python -m unittest tests.feishu.reports.test_s3_cli_recorder_integration`
   - `python -m unittest tests.test_agent_startup`
3. 仓库一致性：
   - `python scripts/run_ci_checks.py`

## Risks

1. 不能把“agent 说 done”直接无条件等价为任务成功，否则会掩盖真实失败。
2. runtime hint 只能作为 detector 失效时的有限兜底，必须与 `task_id` 和终态动作语义绑定，避免跨任务误判。
3. 如果终态前最后一步本身就是错误点击，过强的 hint 会引入 false positive，因此需要保守限定使用范围。

## Rollback

若 runtime hint 造成误判，可回退到“仅 fresh final observation + detector”的版本，并保留单测覆盖以便继续迭代。
