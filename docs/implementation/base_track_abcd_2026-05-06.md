# Base Track ABCD 2026-05-06

## Scope

Implement the Feishu Base knowledge layer for the current screenshot set in `tests/fixtures/base`.

This does not introduce a new runtime mode. The active runtime remains:

- `classic_s3`: `AgentS3 + OSWorldACI`
- `feishu_agent`: `AgentS3 + WindowsFeishuACI`

Base development follows the active Feishu agent principles:

- screenshot-derived metadata is semantic only
- no coordinates, relative bounds, bbox, confidence, score, or resolution
- no deterministic Base workflow route
- Base knowledge must enhance `feishu_agent = AgentS3 + WindowsFeishuACI`

## Module Responsibilities

Track A:

- do not parse Base instructions into a fixed ordered `TestCase`
- leave Base user instructions to the S3 LLM route

Track B:

- describe Base pages visible in the screenshots
- detect Base state from fixture metadata and lightweight OCR text
- expose semantic page context for tool guidance

Track C:

- no Base workflow in this milestone

Track D:

- keep using generic `ReportBuilder`
- keep runtime artifacts product/workflow agnostic

## Screenshot Coverage

Primary semantic states:

- Base home: `多维表格主页-不带弹窗.png`
- Base new menu: `点击新建.png`
- Base template gallery: `点击新建后.png`
- Base browser table editor: `新建多维表格后浏览器界面-带弹窗.png`

Secondary semantic states:

- share panel, more menu, dashboard, workflow, automation, app marketplace, all-base list
- these are classified for page context but not executable workflows

## Target Files

Contracts and Track A:

- `gui_agents/feishu/testcases/nl_parser.py`

Track B:

- `gui_agents/feishu/pages/base_*.py`
- `gui_agents/feishu/pages/registry.py`
- `gui_agents/feishu/detectors/base_state_detector.py`
- `gui_agents/feishu/detectors/__init__.py`
- `tests/fixtures/base/*.json`

Tests:

- `tests/feishu/testcases/test_nl_parser.py`
- `tests/feishu/pages/test_base_registry.py`
- `tests/feishu/detectors/test_base_state_detector.py`
- `tests/test_agent_startup.py`

## Manual Plan

Target files:

- Base page descriptors, detector, semantic fixture metadata, tool guidance, and tests listed above.
- Explicitly remove Base fixed workflow leftovers from parser/planner/workflow imports and startup tests.

Depends on:

- existing `PageDescriptor`, `FeishuState`, and Feishu tool guidance
- existing Docs ABCD shape
- Base screenshots under `tests/fixtures/base`

Outputs:

- `product=base` semantic state detection
- Base page descriptors with semantic regions only
- Base metadata-backed detector coverage
- Base tool guidance that prefers visual/browser-safe S3 actions over text-only UIA helpers
- Base instructions are rejected by the fixed `TestCase -> WorkflowPlan` parser and left to `feishu_agent`

Verification:

- `python -m unittest tests.feishu.detectors.test_base_state_detector -v`
- `python -m unittest tests.feishu.pages.test_base_registry -v`
- `python -m unittest tests.test_agent_startup -v`
- `python scripts/run_ci_checks.py`

Risks / rollback:

1. Base screenshots cover many secondary surfaces, but not all are executable MVP paths.
   Mitigation: classify secondary states semantically and leave execution to the LLM route.

2. Browser Base layout varies by browser chrome and window size.
   Mitigation: do not encode coordinate or relative-bound priors.

3. LLM runtime may still use generic browser clicks for Base.
   Mitigation: this round supplies page knowledge and tool guidance; it does not force deterministic execution.

## Correction 2026-05-06

The first Base implementation still leaked old workflow assumptions:

- `create_base_table` appeared in page descriptors and fixture metadata.
- Base instructions were parsed into fixed ordered test steps.
- Base targets were locatable through `relative_bounds`.

This correction enforces the active development constraints:

- Base screenshots and derived metadata are semantic-only.
- Base page descriptors do not carry relative bounds or supported workflow IDs.
- Base locators do not convert Base semantic regions into coordinates.
- Runtime remains `AgentS3 + WindowsFeishuACI`; Base knowledge is consumed as prior/tool guidance only.
