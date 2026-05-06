# Launcher Frontend Layout Alignment (2026-05-06)

## Module Responsibility

`launcher.py` is the desktop entry point for starting the Agent S3 / Feishu Agent runtime. It owns local configuration editing, runtime mode selection, command history input, process start/stop control, connectivity testing, SOP shortcuts, and runtime log display.

## Boundary

This change is frontend-only:

- Preserve launcher command construction, provider routing, environment defaults, config persistence, execution mode handling, SOP execution, and command history semantics.
- Do not import or require the beautified launcher's optional theme dependencies.
- Do not replace default launcher logic with the beautified file because that file is missing current `execution_mode` wiring and changes query history behavior.
- Use `launcher前端美化版.py` only as visual reference for spacing, color, card layout, header actions, right-side dashboard, and input/log composition.

## Key Interactions

- `load_config()` / `save_config()` keep the persisted launcher contract.
- `_start_agent()` maps current UI state to `gui_agents/s3/cli_app.py` arguments, including `--execution_mode`.
- `_send_query()` and `_add_to_history()` rely on `self.cb_query` being a `ttk.Combobox` with `values`.
- `_set_stopped()` / `_handle_line()` enable and disable `btn_start`, `btn_stop`, `btn_send`, and `cb_query`.
- `_reload_sops()` and `_make_sop_card()` populate SOP UI after the SOP tab is built.

## Target Files

- `launcher.py`
- `docs/implementation/launcher_frontend_layout_alignment_2026-05-06.md`

No automated test changes are planned because this is a launcher UI-only update and existing launcher behavior tests already cover env/config routing.

## Implementation Plan

1. Add neutral light design tokens to `launcher.py` while keeping the existing `self.colors` keys.
2. Rework `_build_ui()` into the beautified structure: top header, segmented Agent/SOP switch, left configuration card, right runtime/log/input pane, footer status detail.
3. Keep the default launcher's functional widgets and variables, especially `v_execution_mode`, `cb_query` as a combobox, and all button commands.
4. Add a `_build_right_pane()` helper for the runtime summary, controls, log, and task input layout.
5. Adjust `_build_agent_tab()` and `_build_sop_tab()` styling/layout only; do not alter callbacks or data flow.
6. Keep `_start_agent()`, `_persist_current_forms()`, `_execution_mode_key_from_label()`, and command history logic unchanged.

## Verification

- `python -m py_compile launcher.py`
- `python -m unittest tests.test_launcher_env_config -v`
- `python -m unittest tests.test_agent_startup -v`

Manual visual verification remains recommended because Tkinter layout quality cannot be fully asserted in headless unit tests.

## Risks

- Tkinter native `ttk` rendering differs by Windows theme; use simple `tk.Frame` cards and existing ttk widgets where behavior matters.
- Moving `btn_start` from the config card to the header is safe only if the same attribute name and command are retained.
- Changing `cb_query` from combobox to entry would break command history behavior, so it must remain a combobox.

## Rollback

Revert only the layout/style changes in `launcher.py`. The implementation document can remain as record of the visual-alignment attempt.
