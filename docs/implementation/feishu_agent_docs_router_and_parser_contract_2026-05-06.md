# Feishu Agent Docs Router And Parser Contract Fix (2026-05-06)

## Module Responsibility

The active Feishu runtime is `AgentS3 + WindowsFeishuACI`. Product-specific modules under `gui_agents/feishu/` provide semantic priors, state detection, tool guidance, verification, and reporting. They must not reintroduce deterministic product workflow execution.

## Problems

1. `Docs` has page descriptors, detector coverage, and verifier branches, but `tool_router.route_feishu_tools()` does not select `detect_docs_state()` and has no Docs-specific branch.
2. `nl_parser.parse_instruction()` returns ordered `TestCase.steps` for IM and Docs. These are not active runtime workflow steps, but the contract does not make that clear. Base/VC should remain guidance-only when parsed.
3. Product guidance should remain agentic: guidance may suggest visible next focus and preferred tools, but the screenshot remains the source of action choice.

## Boundary

In scope:

- Add Docs-specific state selection and routing guidance to `tool_router.py`.
- Add tests that Docs guidance is agent-guided, not fixed workflow execution.
- Mark parser-generated IM/Docs `TestCase` objects as semantic validation scaffolds via `artifacts`.
- Keep parser-generated Base/VC cases as guidance-only testcases with empty steps.
- Restore page registry compatibility defaults required by the startup gate without changing Base/Calendar/VC into fixed-coordinate workflows.

Out of scope:

- Do not restore `FeishuWorker`.
- Do not add `planner -> workflow` execution.
- Do not change `AgentS3` loop behavior.
- Do not remove existing parser tests that validate legacy structured testcase output.

## Target Files

- `gui_agents/feishu/tooling/tool_router.py`
- `gui_agents/feishu/testcases/nl_parser.py`
- `gui_agents/feishu/pages/registry.py`
- `gui_agents/feishu/locators/vision_locator.py`
- `tests/feishu/tooling/test_tool_router.py`
- `tests/feishu/testcases/test_nl_parser.py`
- `docs/implementation/feishu_agent_docs_router_and_parser_contract_2026-05-06.md`

## Plan

1. Import and use `detect_docs_state()` in `route_feishu_tools()` when instruction text indicates Docs.
2. Add a Docs branch that maps `docs_home`, `docs_new_dropdown`, `docs_template_gallery`, and `docs_browser_editor` to product-specific `next_step_focus`, preferred tools, and hints.
3. Prefer Docs/browser-aware tools such as `feishu_doc_click`, `feishu_doc_type`, `click`, `type`, `hotkey`, and `wait` while preserving screenshot-first guidance.
4. Add parser artifacts indicating `runtime_contract=semantic_validation_only` and `active_executor=feishu_agent`.
5. Add registry compatibility defaults for `supported_workflows` labels and legacy IM/search prior bounds that existing helper tests require.
6. Keep `vision_locator` runtime-region first, with descriptor fallback only when an explicit region bound exists.
7. Add tests for Docs router behavior and parser semantic contract.

## Verification

- `python -m unittest tests.feishu.tooling.test_tool_router -v`
- `python -m unittest tests.feishu.testcases.test_nl_parser -v`
- `python -m unittest tests.test_agent_startup -v`

## Risks

- Docs instructions containing generic "文档" may now select the Docs detector earlier. This is intended for Docs tasks, but unknown mixed instructions still need screenshot-based fallback.
- Parser artifacts clarify intent but do not remove ordered steps yet; removing steps would be a larger contract migration affecting tests and reports.
- IM/search legacy prior bounds remain a runtime helper compatibility layer. New Base/Calendar/VC descriptors continue to avoid fixed coordinates.

## Rollback

Revert the Docs branch and parser artifact additions. Existing IM/Calendar/Base/VC routing should remain unaffected.
