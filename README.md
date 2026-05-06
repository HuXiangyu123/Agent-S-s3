# Feishu GUI Agent

Windows-first Feishu desktop GUI agent built on top of Agent-S.

This project focuses on operating the Feishu desktop client like a user:
understanding screenshots, selecting GUI actions, verifying product state, and
writing run artifacts for review. It is not a Feishu Open Platform bot, not an
API-first integration, and not a fixed workflow executor.

Upstream foundation: [simular-ai/Agent-S](https://github.com/simular-ai/Agent-S).

## What It Does

- Drives Feishu desktop through `AgentS3 + WindowsFeishuACI`.
- Supports semantic priors for IM, Docs, Calendar, Base, and VC.
- Uses page descriptors, state detectors, tool guidance, and verifiers to help
  the Agent-S loop make GUI decisions.
- Produces auditable artifacts under `artifacts/test_runs/`, including
  `summary.json`, `report.md`, `actions.jsonl`, and screenshots.
- Provides a Windows launcher for model configuration, task input, execution
  mode selection, and runtime logs.

Current best-supported path is IM text messaging. Docs/Base/VC/Calendar have
semantic and unit-test coverage, but some live desktop flows still need more
validation.

## Architecture

```text
User instruction
  -> launcher.py or gui_agents/s3/cli_app.py
  -> AgentS3 LLM loop
  -> WindowsFeishuACI
  -> Feishu semantic priors
       pages/
       detectors/
       tooling/
       verifiers/
       reports/
  -> runtime artifacts
       summary.json
       report.md
       actions.jsonl
       screenshots/
```

Key points:

- `feishu_agent` is the active Feishu-specific route.
- `classic_s3` remains available for the original generic Agent-S route.
- Feishu product logic should live under `gui_agents/feishu/` where possible.
- Product execution must stay agentic: guidance informs the LLM loop, but does
  not replace it with deterministic product workflows.
- Screenshot-derived metadata is semantic-only. Do not add static coordinates,
  bounding boxes, confidence scores, image dimensions, or fixed step scripts to
  page/fixture metadata.

## Repository Layout

```text
launcher.py                         Windows GUI launcher
gui_agents/s3/                      Agent-S3 runtime and CLI integration
gui_agents/feishu/                  Feishu domain layer
  pages/                            semantic page descriptors
  detectors/                        observation -> FeishuState
  tooling/                          tool registry, routing, helper contracts
  verifiers/                        assertion verification
  reports/                          runtime and evaluation reports
  runtime/                          agentic goal extraction
scripts/check_constraints.py        architecture guardrail checks
scripts/run_ci_checks.py            local CI parity entry
scripts/build_feishu_eval_report.py aggregate evaluation report builder
tests/                              unit and integration tests
docs/                               requirements, specs, process, implementation notes
```

## Requirements

- Windows 10/11 recommended.
- Python 3.10 to 3.12 recommended.
- Feishu desktop client installed and logged in.
- Single primary monitor recommended.
- API access for:
  - main model: Doubao/Volcano ARK by default
  - grounding/vision model: Doubao vision or another compatible endpoint

The agent controls mouse and keyboard. Do not use the machine for other work
while a run is active.

## Installation

### Option 1: Launcher Script

Run:

```powershell
.\启动.bat
```

The script checks Python, installs required runtime dependencies, sets
`PYTHONPATH`, and starts `launcher.py`.

### Option 2: Manual Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -e .
python launcher.py
```

If your environment blocks editable installs, you can still launch from the
repository root with:

```powershell
$env:PYTHONPATH=(Get-Location).Path
python launcher.py
```

## Model Configuration

The launcher stores configuration in `config.json`. Secrets can also be provided
through `env.txt`; copy `env.txt.example` to `env.txt` and fill in real values.
`env.txt` is ignored by git.

### Main Model: Doubao / Volcano ARK

The launcher defaults to the Doubao/Volcano main provider.

Common fields:

```text
VOLCANO_ENDPOINT_ID: ep-xxxxxxxxxxxxx-xxxxx
VOLCANO_API_KEY: ark-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

Legacy aliases are also supported:

```text
ep-id: ep-xxxxxxxxxxxxx-xxxxx
api-key: ark-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

### Grounding Model

Default grounding provider is Doubao ARK vision.

```text
ARK_API_KEY: ark-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

If the grounding key differs from the main model key:

```text
GROUND_API_KEY: ark-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

### Optional OpenAI-Compatible Main Model

OpenAI-compatible settings can be stored, but they do not override the default
Doubao main provider unless explicitly selected in the launcher.

```text
oai_base_url: https://example.com/v1
oai_api: sk-xxxxxxxx
oai_model: gpt-5.4
model_reasoning_effort: medium
```

## Running

### GUI Launcher

```powershell
python launcher.py
```

Recommended launcher settings:

- Execution mode: `feishu_agent`
- Main provider: Doubao / Volcano
- Grounding provider: Doubao ARK or another configured vision endpoint
- Reflection mode: `on_failure`

After the status shows the agent is ready, enter a task instruction such as:

```text
打开消息中的 bot 功能测试群聊，发送“Hello World”，并确认消息已发送
```

Other launcher examples cover Docs, Calendar, Base, and VC. Some examples are
semantic/runtime probes and may require live UI stabilization before they become
reliable acceptance cases.

### CLI

The launcher wraps `gui_agents/s3/cli_app.py`. Direct CLI use is mainly for
debugging:

```powershell
python gui_agents/s3/cli_app.py `
  --execution_mode feishu_agent `
  --provider openai `
  --model <MAIN_MODEL_OR_ENDPOINT_ID> `
  --model_url <MAIN_MODEL_BASE_URL> `
  --model_api_key <MAIN_MODEL_API_KEY> `
  --ground_provider openai `
  --ground_url <GROUNDING_BASE_URL> `
  --ground_api_key <GROUNDING_API_KEY> `
  --ground_model <GROUNDING_MODEL> `
  --grounding_width 1000 `
  --grounding_height 1000 `
  --ground_coord_scale 1000
```

Use the launcher for normal local runs because it manages provider config,
screen settings, process lifecycle, and logs.

## Evaluation Artifacts

Each Feishu run can write artifacts under:

```text
artifacts/test_runs/<run_id>/
  summary.json
  report.md
  actions.jsonl
  screenshots/
```

Aggregate existing run summaries:

```powershell
python scripts/build_feishu_eval_report.py --artifact-root artifacts/test_runs --output-dir artifacts/evaluation
```

Outputs:

```text
artifacts/evaluation/evaluation_summary.json
artifacts/evaluation/evaluation_report.md
```

## Development Checks

Every coding session should start with:

```powershell
python -m unittest tests.test_agent_startup -v
```

Common local checks:

```powershell
python scripts/check_constraints.py
python -m unittest tests.test_launcher_env_config -v
python -m unittest discover tests/feishu -v
python scripts/run_ci_checks.py
```

`scripts/check_constraints.py` enforces the current architecture guardrails,
including no FeishuWorker runtime, no deterministic product workflow executor,
and semantic-only static Feishu metadata.

## Project Docs

Start here for current project state and contracts:

- `docs/process/project_state.md`
- `docs/process/requirements_coverage_audit_2026-05-06.md`
- `docs/feishu_gui_agent_master_plan.md`
- `docs/spec/feishu_gui_agent_technical_spec.md`
- `docs/interfaces/feishu_gui_agent_interfaces.md`
- `AGENTS.md`

Implementation records live under `docs/implementation/`. Some older documents
describe workflow-era designs and should be treated as history, not active
runtime contracts.

## Upstream Attribution

This repository is based on Agent-S and keeps the Agent-S3 loop as the core
agent runtime. For the original general-purpose computer-use framework,
benchmarks, papers, SDK documentation, and citations, see:

- Repository: <https://github.com/simular-ai/Agent-S>
- Project page: <https://www.simular.ai/agent-s>

## License

See `LICENSE`.
