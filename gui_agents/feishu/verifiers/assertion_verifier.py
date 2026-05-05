"""Minimal assertion verifier for Track C send_message."""

from __future__ import annotations

from typing import Any

from gui_agents.feishu.contracts import FeishuState, RuntimeContext, TestCase
from gui_agents.feishu.observation import normalize_observation


def _success(assertion: str, evidence: list[str]) -> dict[str, Any]:
    return {
        "passed": True,
        "assertion": assertion,
        "evidence": evidence,
        "failure_type": None,
        "failure_reason": None,
    }


def _failure(assertion: str, reason: str) -> dict[str, Any]:
    return {
        "passed": False,
        "assertion": assertion,
        "evidence": [],
        "failure_type": "verification",
        "failure_reason": reason,
    }


class AssertionVerifier:
    def verify_assertion(
        self,
        assertion: str,
        state: FeishuState,
        observation: dict[str, Any],
        expected: dict[str, Any] | None = None,
        runtime_context: RuntimeContext | dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        del runtime_context

        expected = expected or {}
        metadata = normalize_observation(observation)
        product_state = state.get("product_state", {})
        ocr_text = observation.get("ocr_text", "") or metadata.get(
            "text_anchors_text", ""
        )

        if assertion == "chat_title_matched":
            expected_chat_name = (
                expected.get("chat_name")
                or expected.get("target")
                or (expected.get("params") or {}).get("chat_name")
                or metadata.get("chat_name")
            )
            actual_chat_name = state.get("chat_name")
            if expected_chat_name and actual_chat_name == expected_chat_name:
                return _success(
                    assertion,
                    [f"chat_name={actual_chat_name}", "page_type=chat_main"],
                )
            if expected_chat_name and expected_chat_name in ocr_text:
                return _success(
                    assertion,
                    [f"ocr_contains={expected_chat_name}", "source=ocr_fallback"],
                )
            return _failure(
                assertion,
                f"chat title mismatch: expected={expected_chat_name!r}, actual={actual_chat_name!r}",
            )

        if assertion == "message_input_contains_text":
            expected_text = (
                expected.get("message_text")
                or expected.get("text")
                or (expected.get("params") or {}).get("text")
                or (expected.get("payload") or {}).get("text")
            )
            draft_text = product_state.get("draft_text")
            if expected_text and draft_text == expected_text:
                return _success(
                    assertion,
                    [f"draft_text={draft_text}", "draft_present=True"],
                )
            if expected_text and expected_text in ocr_text:
                return _success(
                    assertion,
                    [f"ocr_contains={expected_text}", "source=ocr_fallback"],
                )
            return _failure(
                assertion,
                f"message input text mismatch: expected={expected_text!r}, actual={draft_text!r}",
            )

        if assertion == "message_sent":
            expected_text = (
                expected.get("message_text")
                or expected.get("text")
                or (expected.get("params") or {}).get("text")
                or (expected.get("payload") or {}).get("text")
            )
            sent_visible = bool(product_state.get("message_sent_visible"))
            sent_text = product_state.get("sent_message_text")
            if sent_visible and (not expected_text or sent_text == expected_text):
                evidence = ["message_sent_visible=True"]
                if sent_text:
                    evidence.append(f"sent_message_text={sent_text}")
                return _success(assertion, evidence)
            if expected_text and expected_text in ocr_text:
                return _success(
                    assertion,
                    [f"ocr_contains={expected_text}", "source=ocr_fallback"],
                )
            return _failure(
                assertion,
                f"sent message mismatch: expected={expected_text!r}, actual={sent_text!r}",
            )

        return _failure(assertion, f"unsupported assertion: {assertion}")

    def verify_step(
        self,
        expected: dict[str, Any],
        state: FeishuState,
        observation: dict[str, Any],
        runtime_context: RuntimeContext | dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        assertion = expected.get("assertion")
        if not assertion:
            return {
                "passed": True,
                "step_id": expected.get("step_id"),
                "assertion": None,
                "evidence": [],
                "failure_type": None,
                "failure_reason": None,
            }

        result = self.verify_assertion(
            assertion,
            state,
            observation,
            expected=expected,
            runtime_context=runtime_context,
        )
        result["step_id"] = expected.get("step_id")
        return result

    def verify_case(
        self,
        testcase: TestCase,
        runtime_context: RuntimeContext | dict[str, Any],
    ) -> dict[str, Any]:
        step_results = runtime_context.get("step_results", [])
        failed_steps = [
            result
            for result in step_results
            if result.get("verification_result", {}).get("passed") is False
        ]
        return {
            "passed": not failed_steps,
            "total_steps": len(testcase.get("steps", [])),
            "passed_steps": len(step_results) - len(failed_steps),
            "failed_steps": len(failed_steps),
            "failure_type": "verification" if failed_steps else None,
            "failure_reason": (
                failed_steps[0].get("verification_result", {}).get("failure_reason")
                if failed_steps
                else None
            ),
        }
