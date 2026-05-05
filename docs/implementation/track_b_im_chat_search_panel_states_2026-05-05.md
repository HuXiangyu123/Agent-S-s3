# Track B IM Chat Search Panel State Refinement (2026-05-05)

## Goal

Refine the already-added `im_chat_search_panel` so Track B can reason about:

- empty-state search panel
- panel close affordance

using the real screenshot currently available.

## Why This Is The Next Useful Step

The current model can tell that the in-chat search panel exists and can locate the search input.
That is not enough for stable runtime handling, because the worker will also need to know:

1. whether the panel is empty vs. already showing results
2. how to close the panel safely when it blocks other chat-main actions

Both of these are visible in the current screenshot and do not require speculative UI modeling.

## Scope

### In Scope

- add `conversation_search_close_button` target
- expose empty-state hint visibility in `product_state`
- expose local panel result-list visibility in `product_state`
- add coarse locator support for the close button
- add metadata-only test coverage for a future result-list state without requiring a new screenshot

### Out Of Scope

- full search-result workflow execution
- search result verification semantics
- advanced filter interactions
- jumping to a matched message record

## Proposed Contract Additions

- new target id: `conversation_search_close_button`
- new `product_state` fields:
  - `local_search_empty_hint_visible: bool`
  - `local_search_result_list_visible: bool`
  - `visible_conversation_search_results: list[str]`

## Target Files

- `gui_agents/feishu/contracts.py`
- `gui_agents/feishu/pages/im_chat_search_panel.py`
- `gui_agents/feishu/detectors/im_state_detector.py`
- `gui_agents/feishu/locators/vision_locator.py`
- `docs/interfaces/feishu_gui_agent_interfaces.md`
- `tests/fixtures/im/im_message_searchchat_visible.json`
- `tests/feishu/detectors/test_im_state_detector.py`
- `tests/feishu/locators/test_vision_locator.py`

## Verification

- detector marks the current screenshot as empty-state search panel
- locator can return `conversation_search_close_button`
- locator returns structured failure for `conversation_search_result_item` when no result list is visible
- metadata-only synthetic observation can represent a future result-list state for tests

## Risk

- result-list item support will remain metadata-driven until a real screenshot with visible results is provided
