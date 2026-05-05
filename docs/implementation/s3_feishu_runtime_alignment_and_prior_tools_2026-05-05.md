# S3 Feishu Runtime Alignment And Prior Tools (2026-05-05)

## Goal

Fix the new runtime issues exposed by the latest real launcher log:

- prior knowledge is influencing the plan too early
- runtime guidance is still visible in the terminal before action execution
- live page recognition is still weak
- grounded click coordinates are inconsistent with multi-monitor absolute coordinates
- message-input interaction still relies on free-form natural-language descriptions instead of prior-knowledge tools

This round is about aligning runtime behavior with the intended architecture:

- `AgentS3` remains the planner
- prior knowledge should appear as callable tools and compact hidden routing guidance
- known Feishu surfaces should prefer explicit Feishu tools over long descriptive prompts

## Real Runtime Problems

### 1. Prior knowledge is biasing the first step too early

Latest log:

- `Next-step focus: emoji_icon_or_picker`

This happened on step 1 before the message had even been typed.

Root cause:

- the router reads the full instruction and sees `表情`
- it upgrades emoji-related priority immediately
- it does not account for task progression or current visible draft state

This is wrong for a multi-step instruction.

The first useful prior for this screen is:

- active chat already open
- composer visible
- type the text first

Only after the draft exists should emoji become the next focus.

### 2. Guidance is still printed to the user too early

The current runtime still prints a large `DYNAMIC_TOOL_GUIDANCE` block at the start of the step.

That contradicts the requested behavior:

- prior knowledge should help the model internally
- user-facing output should stay focused on actual tool execution
- guidance should not flood the launcher before tools are chosen

So the guidance must remain in the prompt, but the stdout logging should be removed or heavily minimized.

### 3. Multi-monitor screenshot and click coordinates are not aligned

Latest log:

- grounding response: `<point>525 958</point>`
- executed click: `pyautogui.click(416, 2069, ...)`

This is a sign that the runtime is mixing:

- screenshot bytes captured from one screen path
- absolute click coordinates computed using virtual-screen offsets

Current problem in code:

- `run_agent(...)` captures screenshots with `pyautogui.screenshot()`
- `WindowsFeishuACI.resize_coordinates(...)` applies virtual screen offsets
- `cli_app.py` still initializes `WindowsFeishuACI(width, height)` from `pyautogui.size()`

So screenshot coordinates, scaling dimensions, and absolute click space are not guaranteed to describe the same surface.

This is the highest-risk runtime bug for "定位不准".

### 4. Message input is still handled by long text descriptions

Latest log:

- `agent.feishu_type("hello", "The message input box at the bottom ... placeholder '发送给 bot功能测试'")`

This still asks the model to synthesize a natural-language description and hope the UIA helper can resolve it.

That is exactly the behavior prior knowledge should replace.

For the IM composer, the project already has stable prior:

- page type: `chat_main`
- known region: `message_input_area`
- known semantic target: composer input

So this should be a dedicated tool, not a text-guessing path.

## Required Changes

### 1. Observation capture must align with virtual-screen coordinates

For `WindowsFeishuACI`:

- capture screenshot with `ImageGrab.grab(all_screens=True)`
- use virtual-screen width/height for grounding-agent coordinate scaling
- carry resized screenshot bytes plus resized dimensions in `obs`

This keeps:

- screenshot seen by the model
- coordinates returned by grounding
- actual click positions

inside one consistent coordinate system.

### 2. Prior knowledge should not dominate before the current sub-step is complete

Routing must be stage-aware, not only instruction-aware.

For IM send-message + emoji tasks:

- if no draft is visible yet, focus should stay on the composer
- if draft is visible, emoji can become the next focus
- if emoji panel is already open, choose inside-picker click actions

This is still heuristic, but it must be tied to state, not just the full instruction string.

### 3. Add dedicated prior-knowledge tools for IM composer

New tools should be added to `WindowsFeishuACI`:

- `feishu_click_message_input()`
- `feishu_type_message(text, overwrite=False, enter=False)`
- `feishu_click_send_button()`

These tools should use:

- page descriptor region knowledge
- current screenshot dimensions
- direct absolute coordinate generation

This removes the need for long message-input descriptions and gives the model explicit tool affordances backed by prior knowledge.

### 4. Keep guidance in-prompt but stop printing it to stdout

Runtime guidance should still be injected into the model context.

But launcher output should show:

- planning
- actual tool execution
- grounding traces when relevant

not the full hidden guidance block each turn.

## Target Files

- `docs/implementation/s3_feishu_runtime_alignment_and_prior_tools_2026-05-05.md`
- `gui_agents/s3/cli_app.py`
- `gui_agents/s3/agents/worker.py`
- `gui_agents/s3/agents/grounding_feishu.py`
- `gui_agents/feishu/tooling/tool_registry.py`
- `gui_agents/feishu/tooling/tool_router.py`
- `tests/feishu/tooling/test_tool_router.py`
- `tests/feishu/tooling/test_feishu_runtime_prior_tools.py`

## Manual Plan

### target files

- `gui_agents/s3/cli_app.py`
- `gui_agents/s3/agents/worker.py`
- `gui_agents/s3/agents/grounding_feishu.py`
- `gui_agents/feishu/tooling/tool_registry.py`
- `gui_agents/feishu/tooling/tool_router.py`
- `tests/feishu/tooling/test_tool_router.py`
- `tests/feishu/tooling/test_feishu_runtime_prior_tools.py`

### depends on

- `gui_agents/feishu/pages/im_chat_main.py`
- `gui_agents/feishu/detectors/im_state_detector.py`
- `gui_agents/feishu/locators/vision_locator.py`
- `gui_agents/feishu/observation.py`

### outputs

- virtual-screen-aligned screenshot capture for `feishu_agent`
- hidden guidance instead of noisy stdout guidance
- stage-aware IM routing
- dedicated IM composer prior tools

### verification

- `python -m unittest tests.test_agent_startup -v`
- `python -m unittest discover -s tests/feishu -t . -v`
- `python -m black --check launcher.py gui_agents tests`

### risks / rollback

1. Risk: all-screens capture changes grounding behavior on single-monitor setups.
   Rollback: keep the capture path behind `WindowsFeishuACI.capture_observation(...)` only.
2. Risk: new IM-only tools bias non-IM Feishu tasks.
   Rollback: recommend them only in `chat_main` IM routing.
3. Risk: removing guidance stdout makes debugging harder.
   Rollback: keep guidance in `execution-trace.log`, not in normal stdout.
