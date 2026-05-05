# CI Black Fix Plan (2026-05-05)

## Scope

Fix the current formatting-related CI failure reported by `black --check gui_agents`.

## Observed Failure

CI reported:

- `nl_parser.py` would be reformatted
- `scenario_schema.py` would be reformatted
- `grounding_feishu.py` would be reformatted
- `cli_app.py` failed to parse near `def _settle_delay(...)`

## Local Findings

- Local `python -m py_compile gui_agents/s3/cli_app.py` succeeds
- Local `python -m black --check gui_agents` currently only reports:
  - `gui_agents/feishu/detectors/im_state_detector.py` would be reformatted
- The earlier parse failure is not reproducible in the current workspace state

## Target Files

- `gui_agents/feishu/detectors/im_state_detector.py`
- Optional verification target:
  - `gui_agents/s3/cli_app.py`

## Fix Strategy

1. Record the CI discrepancy and current local reproduction result
2. Apply `black` formatting to the file that still fails locally
3. Re-run:
   - `python -m black --check gui_agents`
   - focused Feishu tests

## Verification

- `python -m black --check gui_agents`
- `python -m unittest discover -s tests/feishu/detectors -t . -v`
- `python -m unittest discover -s tests/feishu -t . -v`

## Risk

- If CI still reports `cli_app.py` parse failure after this change, then the issue is likely due to:
  - line-ending or encoding differences in the pushed commit
  - CI running against an older commit than the current local workspace
