# Track B Closeout And Track C Entry (2026-05-05)

## Goal

Close the remaining IM fixture gap in Track B, then enter Track C with the smallest executable `send_message` runtime layer.

This round has two linked objectives:

1. finish the last useful IM in-chat search state already evidenced by a real screenshot
2. build the minimal workflow/verifier layer that consumes Track A planner output and Track B state/locator contracts

## Current Understanding

Track A is already able to produce:

- `TestCase`
- `WorkflowPlan`

Track B is already able to provide:

- page descriptors
- fixture-backed state detection
- coarse target grounding

The remaining screenshot `tests/fixtures/im/im_chat_search_result_context_jump.png` is not a new page type.
It is still the `im_chat_search_panel` page, but in a richer state:

- the conversation-local search panel is still open
- a query is active
- result list is visible
- one result has been selected
- the main chat history has jumped to the corresponding message context

That means the correct boundary is:

- do not create a new page descriptor
- do not model this as workflow execution yet
- keep it under `product_state` for `im_chat_search_panel`

## Why This Matters

Without this closeout state, Track B can tell that local search results exist, but cannot distinguish:

- result list merely visible
- result selected and context jump visible

This matters for later runtime safety because Track C and later integration need to know whether the chat body is still blocked by an overlay-like state, and whether the worker is still operating inside a search-context branch rather than the normal composer path.

## Scope

### In Scope

- add metadata for `im_chat_search_result_context_jump.png`
- expose a stable `product_state` signal for selected-result context jump
- add detector and locator regression tests for this state
- create `gui_agents/feishu/workflows/`
- create `gui_agents/feishu/verifiers/`
- implement the smallest explicit `send_message` workflow progression for Track C
- implement minimal assertion verification for:
  - `chat_title_matched`
  - `message_input_contains_text`
  - `message_sent`

### Out Of Scope

- real GUI action execution
- worker orchestration in `gui_agents/feishu/agents/feishu_worker.py`
- retries, fallback branches, recovery policies
- non-IM products
- advanced in-chat search interactions such as filters, knowledge-answer cards, or multi-result navigation

## Module Boundaries

### Track B Closeout

Responsibilities:

- describe the new fixture semantically
- detect the page state from fixture metadata
- keep locator behavior deterministic on that page

Non-responsibilities:

- deciding what to click next
- deciding whether the runtime should exit the search panel
- executing result-card navigation

### Track C Entry

Responsibilities:

- translate a `WorkflowPlan(workflow="send_message")` into an explicit ordered runtime step sequence
- define stage-level success gates
- verify the three shared assertions against `FeishuState` plus fixture-backed observation metadata

Non-responsibilities:

- planner logic
- OCR implementation
- low-level click/type/hotkey primitives
- report generation

## Proposed Contract Usage

No new shared ids are required for this round.

Track C should reuse the already frozen ids:

- `ActionId`: `open_chat`, `focus_message_input`, `type_message`, `send_message`
- `TargetId`: `conversation_list_item`, `message_input`, `send_button`
- `AssertionId`: `chat_title_matched`, `message_input_contains_text`, `message_sent`

The only semantic extension is under `FeishuState.product_state` for the search-panel fixture:

- `selected_conversation_search_result_text: str | None`
- `search_result_context_in_chat_visible: bool`

These are page-local runtime hints, not shared id contracts.

## Target Files

### Track B Closeout

- `tests/fixtures/im/im_chat_search_result_context_jump.json`
- `tests/fixtures/im/manifest.json`
- `tests/fixtures/im/readme.md`
- `gui_agents/feishu/detectors/im_state_detector.py`
- `tests/feishu/detectors/test_im_state_detector.py`
- `tests/feishu/locators/test_vision_locator.py`
- `docs/interfaces/feishu_gui_agent_interfaces.md`

### Track C Entry

- `gui_agents/feishu/workflows/__init__.py`
- `gui_agents/feishu/workflows/send_message_workflow.py`
- `gui_agents/feishu/verifiers/__init__.py`
- `gui_agents/feishu/verifiers/assertion_verifier.py`
- `tests/feishu/workflows/test_send_message_workflow.py`
- `tests/feishu/verifiers/test_assertion_verifier.py`

## Implementation Plan

1. add the new fixture metadata and mark it as `page_id=im_chat_search_panel`
2. expose the selected-result context-jump state through metadata-backed `product_state`
3. add tests proving this state does not collapse into plain empty-state or plain result-list state
4. create a minimal stage-driven workflow for `send_message`
5. create a minimal assertion verifier that works from existing fixture metadata
6. keep all runtime output structures explicit and small, without introducing worker-level coupling

## Verification

### Track B

- detector returns `page_type=chat_search_panel`
- detector returns `local_search_result_list_visible=True`
- detector returns `search_result_context_in_chat_visible=True`
- detector returns the selected result text when present
- locator still grounds `conversation_search_result_item` on this state

### Track C

- workflow builds a deterministic ordered step list for `send_message`
- workflow exposes the expected stage transitions and success gates
- verifier passes for:
  - chat title match on IM chat main fixture
  - draft text present on draft fixture
  - sent message visible on sent fixture
- verifier returns structured failure on mismatches

### Test Commands

- `python -m unittest discover -s tests/feishu/detectors -t . -v`
- `python -m unittest discover -s tests/feishu/locators -t . -v`
- `python -m unittest discover -s tests/feishu/workflows -t . -v`
- `python -m unittest discover -s tests/feishu/verifiers -t . -v`
- `python -m unittest discover -s tests/feishu -t . -v`
- `python -m black --check gui_agents tests/feishu`

## Risks

1. The selected-result context state is currently metadata-driven rather than OCR-derived; this is acceptable for fixture-backed Track B regression, but not enough for production recognition.
2. Track C can easily overreach into worker orchestration if stage outputs become too runtime-specific; keep the surface limited to ordered steps plus success gates.
3. The repository currently contains unrelated modified files; this round must avoid reverting or entangling with those edits.

## Rollback

1. Keep the new fixture metadata even if Track C needs redesign; it is still valid regression evidence.
2. If the first Track C API shape proves wrong, revert only `workflows/` and `verifiers/` while preserving Track A/B contracts and tests.
