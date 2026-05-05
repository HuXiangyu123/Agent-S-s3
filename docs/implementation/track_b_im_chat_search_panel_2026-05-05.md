# Track B IM Chat Search Panel Refinement (2026-05-05)

## Goal

Add minimal Track B support for the Feishu IM in-chat search panel opened from the chat page top-right search action.

## Boundary

This state is distinct from both:

- `im_chat_main`
- `feishu_shell_search`

The new state is:

- still inside IM
- scoped to the current conversation
- used to search message history within the conversation

It should not be modeled as shell/global search.

## Why This Matters

Without this refinement, the current detector can blur three different states:

1. normal chat main page
2. shell/global search overlay
3. in-chat conversation search panel

That makes failure diagnosis worse and increases the chance of routing the locator to the wrong target family.

## Scope

### In Scope

- add an `im_chat_search_panel` page descriptor
- add fixture metadata for the new screenshot
- detect this state as a distinct `page_type`
- add minimal locator support for the search input region
- make existing locator fail safely for chat-main targets on this page

### Out Of Scope

- executing in-chat history search workflow
- extracting actual search results from this panel
- advanced filters such as sender/time/advanced search
- verifier logic for searched message history

## Proposed Contract Surface

- new `page_id`: `im_chat_search_panel`
- new `page_type`: `chat_search_panel`
- new target id: `conversation_search_entry`

This target is local to the in-chat panel and should not be reused for shell/global search.

## Target Files

- `gui_agents/feishu/contracts.py`
- `gui_agents/feishu/pages/im_chat_search_panel.py`
- `gui_agents/feishu/pages/registry.py`
- `gui_agents/feishu/detectors/im_state_detector.py`
- `gui_agents/feishu/locators/vision_locator.py`
- `docs/interfaces/feishu_gui_agent_interfaces.md`
- `tests/fixtures/im/im_message_searchchat_visible.json`
- `tests/fixtures/im/manifest.json`
- `tests/fixtures/im/readme.md`
- `tests/feishu/pages/test_registry.py`
- `tests/feishu/detectors/test_im_state_detector.py`
- `tests/feishu/locators/test_vision_locator.py`

## Verification

- registry exposes `im_chat_search_panel`
- detector returns `page_type="chat_search_panel"` for the new fixture
- locator can locate `conversation_search_entry` on this page
- locator returns structured unsupported failures for `message_input` / `send_button` on this page

## Risks

- current metadata is coarse and region-driven, not pixel-accurate
- fallback OCR detection remains heuristic until runtime OCR is wired in
- later workflow integration may require richer search-result modeling inside the panel
