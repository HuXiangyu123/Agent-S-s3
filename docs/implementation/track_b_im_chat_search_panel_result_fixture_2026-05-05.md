# Track B IM Chat Search Panel Result Fixture (2026-05-05)

## Goal

Promote the in-chat search result state from metadata-only support to real fixture-backed support.

## New Evidence

The new screenshot `im_message_searchresult_visible.png` provides a real conversation-search result page with:

- active query text in the search box
- visible result list
- multiple real message result cards
- bottom time-range hint

## Why This Changes The Quality Bar

Before this fixture, `conversation_search_result_item` existed only as a metadata-backed placeholder.
That was sufficient for interface shaping, but not enough for stable regression evidence.

With the new screenshot we can now validate:

- detector recognizes result-list visible state
- detector no longer marks the panel as empty state
- locator can ground a real `conversation_search_result_item`

## Scope

### In Scope

- add metadata for `im_message_searchresult_visible.png`
- update IM fixture manifest/readme
- replace at least one metadata-only result-list test with a real fixture test
- keep metadata-based tests only as fallback coverage for future variant states

### Out Of Scope

- modeling the AI knowledge-answer card as its own target
- result-card click execution workflow
- verifier logic for jump-to-message behavior

## Target Files

- `tests/fixtures/im/im_message_searchresult_visible.json`
- `tests/fixtures/im/manifest.json`
- `tests/fixtures/im/readme.md`
- `tests/feishu/detectors/test_im_state_detector.py`
- `tests/feishu/locators/test_vision_locator.py`

## Verification

- detector returns `local_search_result_list_visible=True`
- detector returns `local_search_empty_hint_visible=False`
- locator can match one real visible result item from the screenshot
- full `tests/feishu` suite still passes
