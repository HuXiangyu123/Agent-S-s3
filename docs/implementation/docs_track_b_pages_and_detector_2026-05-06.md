# Docs Track B Pages And Detector 2026-05-06

## Goal

Implement the smallest Docs Track B slice from the existing screenshots under `tests/fixtures/docs/`.

This round is page/state recognition only. It prepares Docs for a later Track C `create_doc_and_edit` workflow, but does not add runtime execution, workflow progression, or verification logic.

## Module Responsibilities

### Pages

Docs page descriptors define stable page ids, coarse key regions, text anchors, and supported workflows for the minimum cloud-doc creation path:

- `docs_home`
- `docs_new_dropdown`
- `docs_template_gallery`
- `docs_browser_editor`

Sharing and permission screenshots are kept as fixture evidence but are not part of the first workflow path.

### Detector

`docs_state_detector` converts fixture-backed observations into `FeishuState`:

- `product="docs"`
- page type from fixture metadata
- Docs-specific fields under `product_state`
- no Docs-only fields added to the shared `FeishuState` top level

OCR fallback is intentionally minimal. The stable Track B contract is metadata-backed fixture recognition.

## Boundaries

In scope:

- Add Docs fixture metadata and manifest.
- Add Docs page descriptors and registry entries.
- Add a Docs detector that consumes fixture metadata.
- Add module tests for registry and detector behavior.

Out of scope:

- No `gui_agents/s3/` runtime changes.
- No Docs workflow or verifier.
- No browser helper changes.
- No share/permission workflow.
- No broad OCR/VLM page understanding.

## Target Files

- `tests/fixtures/docs/manifest.json`
- `tests/fixtures/docs/*.json`
- `gui_agents/feishu/pages/docs_home.py`
- `gui_agents/feishu/pages/docs_new_dropdown.py`
- `gui_agents/feishu/pages/docs_template_gallery.py`
- `gui_agents/feishu/pages/docs_browser_editor.py`
- `gui_agents/feishu/pages/registry.py`
- `gui_agents/feishu/detectors/docs_state_detector.py`
- `gui_agents/feishu/detectors/__init__.py`
- `tests/feishu/pages/test_docs_registry.py`
- `tests/feishu/detectors/test_docs_state_detector.py`

## Implementation Plan

1. Register the four Docs page descriptors with coarse `relative_bounds`.
2. Add fixture metadata for all current Docs screenshots, while tests focus on the primary creation path.
3. Implement metadata-first Docs state detection.
4. Add tests for page registry exposure and representative state detection:
   - Docs home.
   - New dropdown.
   - Template gallery with blank document card.
   - Browser editor ready state.
   - Share dialog metadata retained but not supported by the first workflow.

## Verification

Run:

- `python -m unittest tests.test_agent_startup -v`
- `python -m unittest discover -s tests/feishu/pages -t . -v`
- `python -m unittest discover -s tests/feishu/detectors -t . -v`
- `python -m unittest discover -s tests/feishu -t . -v`

## Risks

1. Current Docs screenshots have no sidecar metadata, so this round must manually define semantic facts.
2. Desktop cloud-doc pages and browser editor pages behave differently; keep them separate page ids.
3. Share/permission screenshots are useful but too costly for the first Docs workflow; they remain fixture evidence only.
4. If later OCR-based detection diverges from metadata semantics, metadata remains the Track B regression source of truth.

## Rollback

Remove the Docs page descriptor files, `docs_state_detector.py`, Docs fixture metadata, Docs tests, and registry imports. Existing IM Track A/B/C/D code should remain unaffected.
