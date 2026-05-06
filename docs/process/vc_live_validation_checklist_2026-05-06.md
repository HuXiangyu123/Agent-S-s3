# VC Live Validation Checklist 2026-05-06

## Purpose

This checklist is for the next real launcher validation round of `VC` on the
active `feishu_agent` route.

The current codebase already has:

- `VC` semantic state detection
- `VC` final-state verification for Track D artifacts
- `VC` agentic helper tools for start / join / invite

What remains is live runtime proof on the actual Feishu desktop client.

## Runtime Assumptions

- execution mode: `feishu_agent`
- main model: current default Doubao route
- grounding model: current default Doubao visual grounding route
- Feishu desktop client is already logged in
- the task is executed on the same primary screen used by launcher capture

## Validation Cases

### Case 1: Start Meeting

Instruction:

`发起视频会议并验证进入成功`

Expected live behavior:

1. model recognizes `VC home`
2. model prefers the `发起会议` entry instead of generic long descriptions
3. model reaches the preview window
4. model clicks `开始会议`
5. final state reaches active meeting

Pass signal:

- `summary.json` status is `completed`
- final assertion contains `vc_meeting_active` and `passed=true`

### Case 2: Join Meeting

Instruction template:

`加入会议，会议 ID 为 <meeting_id>，并验证进入成功`

Expected live behavior:

1. model recognizes `VC home` or `VC join preview`
2. model uses the dedicated meeting-ID input helper
3. model clicks the visible `加入会议` button
4. final state reaches active meeting

Pass signal:

- `summary.json` status is `completed`
- final assertion contains `vc_joined` and `passed=true`

### Case 3: Open Invite Dialog

Instruction:

`在当前视频会议中打开邀请面板`

Expected live behavior:

1. model starts from active meeting
2. model uses the invite toolbar helper
3. if a small invite popover appears, model continues through the invite entry
4. final state reaches the full invite dialog

Pass signal:

- `summary.json` status is `completed`
- final assertion contains `vc_invite_dialog_opened` and `passed=true`

## Artifact Collection

After each live run, keep these artifacts:

- latest run directory under `artifacts/test_runs/`
- `summary.json`
- `report.md`
- `actions.jsonl`
- `logs/execution-trace.log`

If the run fails, capture:

1. the full terminal output from launcher
2. the latest `summary.json`
3. the last relevant section of `execution-trace.log`
4. one screenshot if the failure is visually ambiguous

## Failure Reading Guide

### If start/join keeps using long natural-language click descriptions

Check whether the plan text mentions:

- `agent.feishu_vc_click_start_card()`
- `agent.feishu_vc_click_join_card()`
- `agent.feishu_vc_type_meeting_id(...)`

If not, the worker prompt path is not steering strongly enough.

### If invite gets stuck on the active-meeting toolbar

Check whether the detector identified:

- `modal_type=vc_invite_popover`

If not, the popover surface was not semantically recognized from OCR/runtime
observation.

### If final report says failed but the UI looked correct

Check:

- detector page classification in the last state
- final assertion name and failure reason in `summary.json`
- whether OCR enrichment happened for the final observation

## Next Engineering Action After Live Run

- If all 3 cases pass: move `VC` from “main remaining app-level repair item” to
  “basic runnable”.
- If any case fails: fix the smallest runtime gap on `feishu_agent` directly,
  then rerun only the failed case first.
