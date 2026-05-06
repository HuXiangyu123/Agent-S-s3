# VC And M4 Runtime Verification Integration 2026-05-06

## Module Analysis

Current `feishu_agent` runtime has two gaps that block meaningful VC closure from an M4 perspective:

1. `VC` page detection and tool guidance exist, but active runtime reporting does not verify that a VC task actually reached its intended end state.
2. `Track D` artifacts currently treat "model returned `done`" or "Python code executed" as sufficient for success, which is not a valid evaluation signal for M4.

The fix for this round must stay inside the current architecture:

- keep `feishu_agent = AgentS3 + WindowsFeishuACI`
- do not restore deterministic `planner -> workflow -> executor`
- do not introduce fixed step chains for VC
- keep screenshot-derived knowledge semantic-only

This round therefore adds an agentic runtime verification layer:

- derive a lightweight runtime goal from the user instruction
- detect the final Feishu state from the last observation
- verify semantic assertions against that final state
- write product/task/assertion results into Track D artifacts

## Scope

This pass covers:

- VC runtime goal extraction for start/join/invite-oriented instructions
- VC assertion implementation in `AssertionVerifier`
- final-observation verification inside `S3RuntimeRecorder`
- report identity fields needed for M4-style aggregation
- targeted tests for the new runtime verification path

This pass does not cover:

- restoring workflow execution
- batch regression runner
- dashboard/visualization
- full multi-product runtime verification parity

## Responsibilities

### Runtime Goal Extraction

Convert a natural-language instruction into a lightweight semantic goal for reporting:

- `product`
- `task_id`
- `title`
- expected assertions
- expected semantic values such as meeting ID when useful

This is not a deterministic execution plan. It only describes what completion should look like.

### Final-State Verification

At run finalization:

- inspect the last observation
- detect the current Feishu product/page state
- verify the expected assertions
- mark the run as `completed` only if the final assertions pass

### Track D Reporting

Track D artifacts must include enough identity to support M4 aggregation:

- `product`
- `task_id`
- assertion pass/fail details
- verification-driven final status

## Boundaries

- Do not add `workflow.py` back.
- Do not add ordered product step lists for VC.
- Do not make runtime success depend on fixture-only metadata.
- Do not record coordinate-like visual metrics in new metadata.
- Do not make Track D depend on private worker internals beyond current runtime facts and final observation.

## Target Files

New files:

- `gui_agents/feishu/runtime/__init__.py`
- `gui_agents/feishu/runtime/agentic_goal.py`
- `tests/feishu/runtime/__init__.py`
- `tests/feishu/runtime/test_agentic_goal.py`

Updated files:

- `gui_agents/feishu/contracts.py`
- `gui_agents/feishu/verifiers/assertion_verifier.py`
- `gui_agents/feishu/reports/s3_runtime_recorder.py`
- `gui_agents/feishu/reports/report_builder.py`
- `gui_agents/s3/cli_app.py`
- `tests/feishu/reports/test_s3_runtime_recorder.py`
- `tests/feishu/reports/test_report_builder.py`
- `tests/feishu/verifiers/test_assertion_verifier.py`

## Implementation Plan

1. Add an agentic runtime-goal helper that infers semantic completion criteria from the instruction without creating fixed execution steps.
2. Extend `AssertionVerifier` with VC assertions needed for start/join completion.
3. Let `S3RuntimeRecorder.start()` persist runtime identity fields from the agentic goal.
4. Let `S3RuntimeRecorder.finalize()` evaluate the final observation and append verification step results.
5. Let `run_agent()` pass the final observation into recorder finalization.
6. Update `ReportBuilder` to read `product` and `task_id` from runtime context when no deterministic testcase exists.
7. Add focused tests that prove:
   - VC goal extraction works
   - VC assertions work
   - finalization can flip a `done` run into `failed` when final verification fails
   - report artifacts contain product/task/assertion identity

## Verification

Target verification for this pass:

- `python -m unittest tests.feishu.runtime.test_agentic_goal -v`
- `python -m unittest tests.feishu.verifiers.test_assertion_verifier -v`
- `python -m unittest tests.feishu.reports.test_s3_runtime_recorder -v`
- `python -m unittest tests.feishu.reports.test_report_builder -v`
- `python -m unittest tests.feishu.detectors.test_vc_state_detector tests.feishu.tooling.test_tool_router -v`

## Risks

1. Final-state-only verification does not prove every intermediate step was correct.
   Mitigation: treat this as the minimum M4 closure for agentic runtime, not the final regression framework.

2. OCR on runtime screenshots may be weaker than fixture metadata.
   Mitigation: VC assertions should rely first on semantic detector/product-state fields and use OCR only as fallback.

3. Product inference from instruction can be ambiguous.
   Mitigation: keep heuristics conservative and prefer `unknown` over wrong product labeling.

## Rollback

If runtime verification destabilizes Feishu runs:

1. revert `gui_agents/feishu/runtime/`
2. revert the final-observation hook in `gui_agents/s3/cli_app.py`
3. revert recorder/report changes

This rollback should not affect the base AgentS3 action loop.
