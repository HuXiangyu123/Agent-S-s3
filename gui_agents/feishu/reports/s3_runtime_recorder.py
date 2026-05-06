"""Track D recorder for the LLM-driven Feishu AgentS3 route."""

from __future__ import annotations

import datetime as dt
import hashlib
from typing import Any

from gui_agents.feishu.maintenance.artifact_manager import ArtifactManager
from gui_agents.feishu.reports.report_builder import ReportBuilder


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
        self.runtime: dict[str, Any] | None = None
        self.instruction: str | None = None

    def start(self, instruction: str) -> dict[str, Any]:
        self.instruction = instruction
        self.runtime = {
            "run_id": _run_id(instruction),
            "status": "running",
            "workflow": "agent_s3_feishu",
            "workflow_params": {"instruction": instruction},
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

    def finalize(
        self,
        status: str | None = None,
        failure_reason: str | None = None,
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

        try:
            return self.report_builder.write_runtime_artifacts(None, self.runtime)
        except Exception as exc:
            print(f"FEISHU_TRACK_D_WARNING: artifact generation failed: {exc!r}")
            return None
