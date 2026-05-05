# Feishu Grounding Coordinate Regression And API Path

Date: 2026-05-06
Owner: Codex
Scope: `gui_agents/s3/cli_app.py`, `gui_agents/s3/agents/grounding_feishu.py`, `gui_agents/s3/core/engine.py`, related tests

## Problem Record

Current launcher log shows a grounded click coordinate regression:

- Grounding model output: `<point>523 957</point>`
- Executed click: `pyautogui.click(2008, 2067, ...)`

This is not a normal local miss. It indicates the screenshot coordinate space and the execution coordinate space are inconsistent.

## Root Cause

Current product assumption has changed: virtual-screen support has been removed, so Feishu runtime must stay in a single-screen coordinate system.

Under that assumption, the regression is:

1. `grounding_feishu.py:capture_observation()` uses primary-screen `ImageGrab.grab()`.
2. `cli_app.py` still initializes Feishu runtime dimensions from a different source.
3. On some Windows setups, that source can disagree with the actual captured image size.
4. `resize_coordinates()` then scales model coordinates using a width/height pair that does not match the screenshot seen by the grounding model.
5. Result: a point predicted on the captured screen is stretched into the wrong click range, causing large offsets.

## Fix Direction

Use one consistent single-screen coordinate space throughout the Feishu runtime:

1. Feishu agent screen size should come from the same primary-screen capture method used at runtime.
2. `capture_observation()` should stay on `ImageGrab.grab()` for the primary screen.
3. `resize_coordinates()` should scale only within that same primary-screen width/height.
4. Tests must lock:
   - primary-screen size helper
   - normalized coordinate resize on the primary screen
   - `capture_observation()` returning primary-screen source dimensions

## Model API Path Check

Current project status:

- Main model path in `gui_agents/s3/core/engine.py` uses `OpenAI(...).chat.completions.create(...)`
- Grounding model path in the same file also uses `chat.completions.create(...)`
- Launcher connectivity check in `launcher.py` also uses `client.chat.completions.create(...)`
- There is no active `client.responses.create(...)` path in the current S3 runtime

So today the project is still on Chat Completions API, not Responses API.

## Target Files

- `gui_agents/s3/cli_app.py`
- `gui_agents/s3/agents/grounding_feishu.py`
- `tests/feishu/tooling/` or adjacent runtime tests

## Verification

- Unit test: normalized `1000`-space point scales into primary-screen coordinates correctly
- Unit test: Feishu startup screen size uses the same primary-screen capture path as runtime observation
- Existing regression suites:
  - `python -m unittest discover -s tests/feishu -t . -v`
  - `python -m unittest tests.test_agent_startup -v`
  - `python -m black --check launcher.py gui_agents tests`
