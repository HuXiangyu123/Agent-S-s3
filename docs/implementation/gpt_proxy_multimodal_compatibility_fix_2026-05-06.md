# GPT Proxy Multimodal Compatibility Fix

Date: 2026-05-06
Owner: Codex
Scope: `gui_agents/s3/core/mllm.py`, `gui_agents/s3/core/engine.py`, launcher/provider config, related tests

## Problem

Current user report:

- GPT main model is routed through a proxy endpoint.
- Text-only requests still work.
- Once the agent sends screenshot/image content, the interface returns an error and image understanding breaks.

This indicates a compatibility problem between the current OpenAI-style multimodal message payload and the proxy endpoint's accepted schema.

## Current Implementation

- Main GPT provider currently uses an OpenAI-compatible client with `chat.completions.create(...)`.
- `LMMAgent.add_message(...)` serializes screenshots as:
  - content item type: `image_url`
  - payload:
    - `url: data:image/png;base64,...`
    - `detail: high`
- This is generated in `gui_agents/s3/core/mllm.py`.

## Likely Compatibility Risks

The proxy may reject one or more of:

1. `detail` field inside `image_url`
2. `data:` URL base64 images
3. mixed content ordering / content shape
4. `chat.completions` multimodal payload subset differences from official OpenAI endpoint

## Plan

1. Reproduce the proxy failure with a minimal image request against the configured GPT endpoint.
2. Test a small matrix of payload variants:
   - current `image_url + detail + data URI`
   - `image_url + data URI` without `detail`
   - any other minimal OpenAI-compatible variant if needed
3. Based on the passing variant, add a compatibility switch in the local multimodal message builder.
4. Keep the default OpenAI path unchanged where possible; scope the workaround to proxy-compatible OpenAI-style providers.

## Target Files

- `gui_agents/s3/core/mllm.py`
- possibly `gui_agents/s3/core/engine.py`
- tests under `tests/`

## Verification

- Direct proxy smoke test with image message succeeds
- Existing text-only path still succeeds
- Existing local regression suites remain green
