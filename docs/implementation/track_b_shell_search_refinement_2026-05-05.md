# Track B Shell Search Boundary Refinement (2026-05-05)

## Reason

Track B initially treated the Feishu global search overlay as part of `im_chat_main`.
That boundary is wrong for the real desktop UI:

- `im_chat_main` = already inside an IM conversation
- `feishu_shell_search` = top-level Feishu shell overlay used to find a conversation before entering it

If we keep search inside the IM page model, `open_chat` will blur two different states:

1. selecting a visible conversation from the left sidebar
2. opening the global search overlay and choosing a result

## Scope Of This Refinement

- Keep `im_chat_main` focused on in-chat states only
- Add a separate page descriptor for global search
- Replace the temporary `chat_search_box` target with `global_search_entry`
- Split chat selection into:
  - `conversation_list_item`
  - `search_result_item`
- Keep a compatibility alias in the locator for the old experimental names used during early Track B tests

## Target Files

- `gui_agents/feishu/contracts.py`
- `gui_agents/feishu/pages/im_chat_main.py`
- `gui_agents/feishu/pages/feishu_shell_search.py`
- `gui_agents/feishu/pages/registry.py`
- `gui_agents/feishu/detectors/im_state_detector.py`
- `gui_agents/feishu/locators/vision_locator.py`
- `tests/fixtures/im/`
- `tests/fixtures/feishu_shell/`
- `tests/feishu/pages/`
- `tests/feishu/detectors/`
- `tests/feishu/locators/`

## Verification

- Registry exposes both `im_chat_main` and `feishu_shell_search`
- Detector identifies IM chat fixtures and shell search fixtures as different page types
- Locator can return structured matches for:
  - `conversation_list_item`
  - `global_search_entry`
  - `search_result_item`
  - `message_input`
  - `send_button`
- Legacy alias inputs still fail safely or resolve to the new canonical targets

## Risks

- Search result item bounds are still coarse metadata, not per-pixel annotations
- Fallback OCR detection remains heuristic until runtime OCR is wired in
- `search_box_visible` is currently a shared boolean across page types; later contracts may split it into more explicit shell-vs-product state
