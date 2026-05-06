# Technical Debt And Dead Code Cleanup 2026-05-06

## Module Analysis

This cleanup addresses technical debt that conflicts with the active
`feishu_agent = AgentS3 + WindowsFeishuACI` route and the semantic-only fixture
principle in `AGENTS.md`.

## Responsibilities

- Static page descriptors and fixture metadata are semantic knowledge only.
- Runtime click coordinates may exist only as immediate locator / grounding
  results, not as persisted product-domain metadata.
- Base and VC instructions should be represented as semantic guidance instead
  of failing out of the parser because no deterministic workflow exists.
- Deprecated workflow fields should not be present in page descriptors or
  screenshot fixture metadata; the shared contract keeps only optional backward
  compatibility typing.

## Boundaries

- This pass does not introduce product `workflow` modules or fixed fallback
  click sequences.
- Legacy Agent-S framework files outside the Feishu domain are not refactored.
- Existing IM locator fixture tests are adjusted to validate semantic-only
  behavior rather than static-coordinate success.

## Target Files

- `gui_agents/feishu/contracts.py`
- `gui_agents/feishu/observation.py`
- `gui_agents/feishu/locators/vision_locator.py`
- `gui_agents/feishu/pages/*.py`
- `tests/fixtures/**/*.json`
- `gui_agents/feishu/testcases/nl_parser.py`
- `gui_agents/feishu/tooling/tool_contracts.py`
- `gui_agents/feishu/tooling/tool_router.py`
- `gui_agents/s3/agents/_feishu_exec.py`
- `gui_agents/feishu/reports/*.py`
- `tests/feishu/**`
- `scripts/check_constraints.py`

## Manual Plan

- Remove `relative_bounds` from static page descriptors and fixture JSON, and
  stop using fixture metadata as coordinate fallback.
- Remove `supported_workflows` / `workflow_support` from static metadata so
  fixtures cannot imply a fixed workflow runtime.
- Convert `PageDescriptor.supported_workflows` to optional compatibility data.
- Replace parser hard failures for Base/VC with semantic guidance output.
- Remove docs toolbar pixel-offset helper behavior and make it explicit
  semantic guidance instead of magic coordinates.
- Add tests for descriptor cleanliness, parser guidance, Docs routing, verifier
  product coverage, and constraints.

## Verification

- Targeted Feishu tests for locators, parser, routing, registry, verifier, and
  reports.
- `python -m unittest tests.test_agent_startup -v`
- `python scripts/run_ci_checks.py`

## Risks / Rollback

- Removing static coordinate fallback means some old IM locator tests no longer
  assert coordinate success from fixture metadata. Runtime still gets coordinates
  through AgentS3 grounding / execution tools.
- If a downstream consumer still requires `workflow` fields, keep optional
  compatibility reads but prefer `intent` / `params` in reports and new tests.
