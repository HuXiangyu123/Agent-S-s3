"""Track D recorder for the LLM-driven Feishu AgentS3 route."""

from __future__ import annotations

import datetime as dt
import hashlib
from typing import Any

from gui_agents.feishu.detectors.base_state_detector import detect_base_state
from gui_agents.feishu.detectors.calendar_state_detector import detect_calendar_state
from gui_agents.feishu.detectors.docs_state_detector import detect_docs_state
from gui_agents.feishu.detectors.im_state_detector import detect_feishu_state
from gui_agents.feishu.detectors.vc_state_detector import detect_vc_state
from gui_agents.feishu.maintenance.artifact_manager import ArtifactManager
from gui_agents.feishu.reports.report_builder import ReportBuilder
from gui_agents.feishu.runtime import build_agentic_run_goal
from gui_agents.feishu.verifiers.assertion_verifier import AssertionVerifier


def _now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat()


def _run_id(instruction: str) -> str:
    now = dt.datetime.now(dt.timezone.utc).astimezone().strftime("%Y%m%d_%H%M%S")
    digest = hashlib.sha1(instruction.encode("utf-8")).hexdigest()[:8]
    return f"s3_feishu_{now}_{digest}"


def _action_name(exec_code: str) -> str:
    lowered = exec_code.lower()
    if "click" in lowered:
        return "click"
    if "hotkey" in lowered or "press" in lowered:
        return "keyboard"
    if "type" in lowered or "pyperclip.copy" in lowered:
        return "type"
    if "wait" in lowered or "sleep" in lowered:
        return "wait"
    if "done" in lowered:
        return "done"
    if "fail" in lowered:
        return "fail"
    return "exec"


class S3RuntimeRecorder:
    """Record AgentS3 runtime facts without controlling the agent."""

    def __init__(self, artifact_root: str | None = None) -> None:
        self.artifact_manager = ArtifactManager(root_dir=artifact_root)
        self.report_builder = ReportBuilder(self.artifact_manager)
        self.assertion_verifier = AssertionVerifier()
        self.runtime: dict[str, Any] | None = None
        self.instruction: str | None = None

    def start(self, instruction: str) -> dict[str, Any]:
        self.instruction = instruction
        goal = build_agentic_run_goal(instruction)
        self.runtime = {
            "run_id": _run_id(instruction),
            "status": "running",
            "intent": "agent_s3_feishu",
            "params": {"instruction": instruction},
            "product": goal["product"],
            "task_id": goal["task_id"],
            "task_title": goal["title"],
            "assertion_plan": goal["assertions"],
            "page_id": None,
            "precondition_results": [],
            "action_logs": [],
            "screenshots": [],
            "step_results": [],
            "failure_type": None,
            "failure_reason": None,
            "started_at": _now_iso(),
        }
        return self.runtime

    def record_observation(self, step_index: int, observation: dict[str, Any]) -> None:
        if self.runtime is None:
            return
        screenshot = observation.get("screenshot")
        if not isinstance(screenshot, bytes):
            return
        try:
            path = self.artifact_manager.write_screenshot(
                self.runtime["run_id"],
                f"s3_step_{step_index:03d}_observation",
                screenshot,
            )
            self.runtime["screenshots"].append(path)
        except Exception as exc:
            print(f"FEISHU_TRACK_D_WARNING: screenshot persistence failed: {exc!r}")

    def record_action(
        self,
        step_index: int,
        exec_code: str,
        status: str,
        failure_reason: str | None = None,
    ) -> None:
        if self.runtime is None:
            return
        step_id = f"s3_step_{step_index:03d}"
        action = _action_name(exec_code)
        self.runtime["action_logs"].append(
            {
                "timestamp": _now_iso(),
                "step_id": step_id,
                "stage": "AGENT_S3_STEP",
                "action": action,
                "target": None,
                "params": {"code": exec_code},
                "status": status,
            }
        )
        failed = bool(failure_reason) or status == "failed"
        self.runtime["step_results"].append(
            {
                "step_id": step_id,
                "stage": "AGENT_S3_STEP",
                "action": action,
                "target": None,
                "status": "failed" if failed else "passed",
                "locator_result": {
                    "matched": not failed,
                    "page_id": None,
                    "strategy": "agent_s3_runtime",
                },
                "verification_result": {
                    "passed": not failed,
                    "assertion": None,
                    "evidence": [],
                    "failure_reason": failure_reason,
                },
                "failure_type": "runtime" if failed else None,
                "failure_reason": failure_reason,
            }
        )
        if failed:
            self.runtime["status"] = "failed"
            self.runtime["failure_type"] = "runtime"
            self.runtime["failure_reason"] = failure_reason or status

    def _detect_state_for_product(
        self,
        product: str,
        observation: dict[str, Any],
    ) -> dict[str, Any]:
        if product == "vc":
            return detect_vc_state(observation)
        if product == "docs":
            return detect_docs_state(observation)
        if product == "base":
            return detect_base_state(observation)
        if product == "calendar":
            return detect_calendar_state(observation)
        return detect_feishu_state(observation)

    def _build_runtime_vc_hint_state(
        self,
        detected_state: dict[str, Any],
    ) -> tuple[dict[str, Any] | None, str]:
        if self.runtime is None:
            return None, "state_detector"
        if self.runtime.get("product") != "vc":
            return None, "state_detector"
        if detected_state.get("page_type") != "unknown":
            return None, "state_detector"
        if self.runtime.get("status") != "completed":
            return None, "state_detector"

        action_logs = self.runtime.get("action_logs", [])
        if not action_logs:
            return None, "state_detector"

        last_action = action_logs[-1]
        if last_action.get("action") != "done" or last_action.get("status") != "done":
            return None, "state_detector"

        task_id = self.runtime.get("task_id")
        if task_id in {"agentic_vc_start_meeting", "agentic_vc_join_meeting"}:
            return (
                {
                    "page_type": "vc_meeting_active",
                    "product": "vc",
                    "chat_name": None,
                    "message_input_visible": False,
                    "send_button_visible": False,
                    "search_box_visible": False,
                    "modal_type": None,
                    "last_error_banner": None,
                    "product_state": {
                        "meeting_active": True,
                        "runtime_semantic_hint": "agent_done_terminal_state",
                    },
                },
                "runtime_semantic_hint",
            )

        if task_id == "agentic_vc_open_invite_dialog":
            return (
                {
                    "page_type": "vc_invite_dialog",
                    "product": "vc",
                    "chat_name": None,
                    "message_input_visible": False,
                    "send_button_visible": False,
                    "search_box_visible": True,
                    "modal_type": "vc_invite_dialog",
                    "last_error_banner": None,
                    "product_state": {
                        "invite_dialog_visible": True,
                        "share_button_visible": True,
                        "runtime_semantic_hint": "agent_done_terminal_state",
                    },
                },
                "runtime_semantic_hint",
            )

        return None, "state_detector"

    def _record_final_assertions(self, final_observation: dict[str, Any]) -> None:
        if self.runtime is None or self.runtime.get("_final_assertions_recorded"):
            return

        assertion_plan = self.runtime.get("assertion_plan", [])
        if not assertion_plan:
            return

        product = self.runtime.get("product", "unknown")
        detected_state = self._detect_state_for_product(product, final_observation)
        runtime_hint_state, state_strategy = self._build_runtime_vc_hint_state(
            detected_state
        )
        state = runtime_hint_state or detected_state
        self.runtime["page_id"] = state.get("page_type")
        self.runtime["final_state_source"] = state_strategy

        failures: list[dict[str, Any]] = []
        for index, goal in enumerate(assertion_plan, start=1):
            verification = self.assertion_verifier.verify_assertion(
                goal.get("assertion"),
                state,
                final_observation,
                expected=goal.get("expected") or {},
                runtime_context=self.runtime,
            )
            passed = bool(verification.get("passed"))
            self.runtime["step_results"].append(
                {
                    "step_id": f"final_assertion_{index}",
                    "stage": "FINAL_ASSERTION",
                    "action": "verify_assertion",
                    "target": state.get("page_type"),
                    "status": "passed" if passed else "failed",
                    "locator_result": {
                        "matched": state.get("page_type") != "unknown",
                        "page_id": state.get("page_type"),
                        "strategy": state_strategy,
                    },
                    "verification_result": verification,
                    "failure_type": verification.get("failure_type"),
                    "failure_reason": verification.get("failure_reason"),
                }
            )
            if not passed:
                failures.append(verification)

        self.runtime["_final_assertions_recorded"] = True
        if failures:
            self.runtime["status"] = "failed"
            self.runtime["failure_type"] = "verification"
            self.runtime["failure_reason"] = failures[0].get("failure_reason")
        elif self.runtime.get("status") == "running":
            self.runtime["status"] = "completed"

    def finalize(
        self,
        status: str | None = None,
        failure_reason: str | None = None,
        final_observation: dict[str, Any] | None = None,
    ) -> dict[str, str] | None:
        if self.runtime is None:
            return None
        if failure_reason:
            self.runtime["status"] = "failed"
            self.runtime["failure_type"] = "runtime"
            self.runtime["failure_reason"] = failure_reason
        elif status:
            self.runtime["status"] = status
        elif self.runtime.get("status") == "running":
            self.runtime["status"] = "completed"

        if (
            final_observation
            and not failure_reason
            and self.runtime.get("status") != "failed"
        ):
            self._record_final_assertions(final_observation)

        try:
            return self.report_builder.write_runtime_artifacts(None, self.runtime)
        except Exception as exc:
            print(f"FEISHU_TRACK_D_WARNING: artifact generation failed: {exc!r}")
            return None
