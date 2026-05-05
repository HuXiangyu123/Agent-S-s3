# S3 Feishu Agentic Tools Optimization (2026-05-05)

## Goal

Optimize the first Feishu agentic-tools refactor using real runtime evidence from launcher logs.

This round is not a new architecture change.
It is a targeted correction to make the current `feishu_agent -> AgentS3 + WindowsFeishuACI` route actually useful in runtime.

## Runtime Findings From The Real Log

Using the instruction:

`打开消息中的bot功能测试群聊，在消息发送框输入hello，并且在聊天框点击右侧的表情图标，选择一个随机表情，并且发送`

the current runtime showed three concrete problems:

### 1. Guidance is printed every step

`DYNAMIC_TOOL_GUIDANCE` is logged verbosely on every turn, even when nothing changed.

This creates two problems:

- noisy terminal output
- repeated prompt content with low incremental value

The user only needs to see meaningful tool-routing changes, not the same tool table each step.

### 2. Live state stays `page_type=unknown`

The router produced:

- `Detected state: page_type=unknown, product=im`

even though the UI was clearly already on the IM chat main page.

Root cause:

- fixture-backed detection works
- live runtime `obs` only contains screenshot bytes
- `detect_feishu_state(...)` depends on metadata or `ocr_text`
- current Feishu guidance path does not enrich live observations with OCR before routing

So the router falls back to a generic branch instead of using page-specific prior knowledge.

### 3. Tool guidance still does not narrow enough for icon-only controls

For the emoji step, the model chose:

- `agent.feishu_click("... smiley face emoji icon ...")`

This is structurally weak because `feishu_click(...)` is a text-based UIA helper.
Emoji icons, plus buttons, and other icon-only composer controls are often not text-addressable.

That means the current guidance still over-recommends `feishu_click(...)` in cases where a grounded `agent.click(...)` is the correct fallback.

### 4. UIA target-text extraction is too aggressive

`WindowsFeishuACI._extract_feishu_target_text(...)` still tries to heuristically pull a short token out of a long natural-language description.

That creates wrong-click risk when the description contains:

- the real target
- surrounding context
- reference elements

Example failure shapes:

- `... bot功能测试 chat window` -> wrongly extracts `bot功能测试`
- `... right of the 'Aa' text format button ...` -> wrongly extracts `Aa`

For UIA text helpers, a false positive is worse than a miss.
This extractor should therefore be conservative:

- if the description looks like a long relational sentence, pass it through unchanged
- only collapse to a shorter target when the input already looks like explicit visible text

## Why It Did Not Speed Up Much

The first refactor improved architecture alignment, but speed gains were limited because:

1. the router often had no live page state, so it stayed generic
2. the same large guidance block was injected each turn
3. the worker system prompt still exposed a broad action surface even in clear IM-only tasks
4. icon-only controls were not separated from text-addressable controls

So the current solution added prior knowledge text, but did not yet strongly convert that prior knowledge into:

- stateful routing
- prompt compression
- tool subset narrowing

## Optimization Scope

### In Scope

- enrich live Feishu observations with OCR text before routing
- log full dynamic guidance only when it changes
- inject a compact "guidance unchanged" note on repeated turns
- narrow the worker tool prompt for Feishu IM tasks
- add emoji/icon-aware routing rules

### Out Of Scope

- redesigning `AgentS3`
- deleting `feishu_worker`
- adding a full verifier-driven runtime loop back
- solving every Feishu feature branch in one round

## Design

### 1. OCR Enrichment For Live Guidance

`WindowsFeishuACI.build_dynamic_guidance(...)` should first ensure `obs["ocr_text"]` exists.

If missing:

- use existing OCR helpers on the screenshot bytes
- join OCR words into a light `ocr_text`
- write it back into `obs`

Then `detect_feishu_state(...)` can classify:

- `chat_main`
- `chat_search_panel`
- `shell_search`

instead of remaining `unknown`.

### 2. Repeated Guidance Compression

`Worker` should keep the last dynamic guidance block.

If the new block is identical to the previous one:

- do not log the full block again
- do not inject the full block again
- inject only a short note such as:
  - `Feishu tool guidance unchanged from previous step; keep following the same preferred tools unless the screen contradicts it.`

This reduces both log noise and per-turn token load.

### 3. Initial Tool Subset Narrowing

For `feishu_agent` IM instructions, the worker system prompt should expose a smaller initial tool surface.

Keep:

- `open`
- `feishu_focus`
- `feishu_click`
- `feishu_type`
- `click`
- `type`
- `hotkey`
- `wait`
- `done`
- `fail`

Skip for this IM path:

- `feishu_doc_click`
- `feishu_doc_type`
- `set_cell_values`
- `drag_and_drop`
- `highlight_text_span`
- `call_code_agent`
- `save_to_knowledge`

This is the first real "tool narrowing" piece, instead of only text hints.

### 4. Emoji / Icon Control Routing

For IM composer icon-only controls such as:

- emoji
- plus
- image
- at-mention launcher

the router should prefer:

- `agent.click(...)`

and not:

- `agent.feishu_click(...)`

unless the control has known stable visible text.

Reason:

- `feishu_click(...)` is text/UIA-first
- icon-only controls are better handled by grounded spatial click

### 5. Conservative UIA Text Extraction

For `feishu_click(...)` and `feishu_type(..., element_description=...)`:

- preserve exact short visible labels such as `发送`, `确定`, `搜索`, `发送给 bot功能测试`
- preserve quoted text only when the whole description is effectively just that text
- if the description includes relational words like `right of`, `旁边`, `右侧`, `bottom`, `顶部`, `immediately`, or is simply too long, return the original description unchanged

This makes icon-only or contextual descriptions fail safely instead of clicking the wrong visible text.

## Target Files

- `docs/implementation/s3_feishu_agentic_tools_optimization_2026-05-05.md`
- `gui_agents/s3/agents/worker.py`
- `gui_agents/s3/agents/grounding_feishu.py`
- `gui_agents/feishu/tooling/tool_router.py`
- `tests/feishu/tooling/test_tool_router.py`
- `tests/feishu/tooling/test_feishu_target_text_extraction.py`

## Manual Plan

### target files

- `gui_agents/s3/agents/worker.py`
- `gui_agents/s3/agents/grounding_feishu.py`
- `gui_agents/feishu/tooling/tool_router.py`
- `tests/feishu/tooling/test_tool_router.py`
- `tests/feishu/tooling/test_feishu_target_text_extraction.py`

### depends on

- `gui_agents/feishu/detectors/im_state_detector.py`
- `gui_agents/s3/memory/procedural_memory.py`
- existing `WindowsFeishuACI.get_ocr_elements(...)`

### outputs

- live OCR-backed Feishu routing
- reduced repeated guidance logs
- smaller IM task tool surface
- icon-aware emoji guidance
- conservative UIA target-text extraction

### verification

- `python -m unittest tests.test_agent_startup -v`
- `python -m unittest discover -s tests/feishu -t . -v`
- `python -m black --check launcher.py gui_agents tests`

### risks / rollback

1. Risk: OCR enrichment adds runtime overhead.
   Rollback: keep OCR best-effort and fail open to generic guidance if OCR is unavailable.
2. Risk: tool narrowing hides an action needed by some non-IM Feishu branch.
   Rollback: narrow only when the instruction is clearly IM-focused.
3. Risk: icon routing overuses generic clicks.
   Rollback: keep `click(...)` as preferred but not exclusive, so the model can still fall back if the screenshot contradicts the heuristic.
