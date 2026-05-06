# Feishu Agent Parser Guardrails And Trace Fix (2026-05-05)

## Goal

Fix the first real launcher-side failure of the new Feishu agent mode:

1. the parser should not silently coerce unsupported complex instructions into the minimal `send_message` workflow
2. IM chat/message extraction should handle the actual instruction style used in manual testing
3. launcher trace output should show readable runtime signals instead of leaking generated code source fragments

## Failure Observed

Manual test instruction:

`打开消息中的bot功能测试群聊，在消息发送框输入hello，并且在聊天框点击右侧的表情图标，选择一个随机表情，并且发送`

Observed problems:

- parser did not reliably extract `bot功能测试`
- parser did not reject unsupported emoji/random-selection intent
- runtime continued into the minimal `send_message` path anyway
- launcher showed code-source fragments such as `_result_line = "FEISHU_UIA_CLICKED: " ...`

## Root Cause

### Parser Side

The current parser is still Track A MVP grade:

- quoted-text priority
- one fallback regex for `在/向/给 ... 发送/回复`
- final hardcoded default values

This is too weak for realistic launcher instructions like:

- `打开消息中的X群聊，在消息发送框输入Y`
- `打开X群聊...`
- `在X发送Y`

It also lacks any unsupported-intent guardrail, so extra actions such as:

- 表情
- 随机
- 点击右侧图标

are silently ignored.

### Launcher Trace Side

The launcher collapses `EXECUTING CODE:` blocks, but its signal extraction used substring matching inside code-block lines.

That means a source line like:

- `_result_line = "FEISHU_UIA_CLICKED: " + ...`

could be mistaken for a real runtime success line.

## Scope

### In Scope

- strengthen IM chat/message extraction patterns
- explicitly reject unsupported emoji/random-selection instructions in the new Feishu mode
- add parser tests for realistic launcher phrasing
- add readable `FEISHU_TRACE:` runtime lines
- fix launcher signal matching to only treat real runtime lines as runtime signals

### Out Of Scope

- actually supporting emoji-picker navigation
- adding free-form LLM planning to the new Feishu mode
- replacing the current minimal `send_message` workflow boundary

## Design Decision

The new Feishu mode remains:

- prior-knowledge-first
- deterministic for the currently supported IM MVP

This is intentional.

For supported tasks, the goal is:

- less model latency
- less planning drift
- more stable execution

For unsupported tasks, the correct behavior is not “best effort guess”.
It is:

- fail early
- explain unsupported capability clearly
- tell the user to use classic `s3` mode for broader free-form tasks

## Target Files

- `gui_agents/feishu/testcases/nl_parser.py`
- `gui_agents/feishu/agents/__init__.py`
- `launcher.py`
- `tests/feishu/testcases/test_nl_parser.py`

## Verification

- parser extracts `chat_name="bot功能测试"` and `message_text="hello"` from launcher-style instructions
- parser raises a clear `ValueError` on emoji/random-selection instructions
- launcher no longer logs code-source fragments as fake `FEISHU_UIA_CLICKED` runtime messages
- runtime emits readable `FEISHU_TRACE:` lines before step execution
