"""Build structured and human-readable run reports."""

from __future__ import annotations

import datetime as dt
from typing import Any

from gui_agents.feishu.maintenance.artifact_manager import ArtifactManager


def _parse_iso(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    try:
        return dt.datetime.fromisoformat(value)
    except ValueError:
        return None


class ReportBuilder:
    """Build Track D artifacts from testcase and runtime outputs."""

    def __init__(self, artifact_manager: ArtifactManager | None = None) -> None:
        self.artifact_manager = artifact_manager or ArtifactManager()

    def _completed_at(self, runtime_context: dict[str, Any]) -> dt.datetime:
        action_logs = runtime_context.get("action_logs", [])
        if action_logs:
            parsed = _parse_iso(action_logs[-1].get("timestamp"))
            if parsed is not None:
                return parsed
        return dt.datetime.now(dt.timezone.utc).astimezone()

    def _assertion_results(
        self,
        testcase: dict[str, Any] | None,
        runtime_context: dict[str, Any],
    ) -> list[dict[str, Any]]:
        assertions = (testcase or {}).get("assertions", [])
        step_results = runtime_context.get("step_results", [])
        seen: dict[str, dict[str, Any]] = {}
        for step_result in step_results:
            verification = step_result.get("verification_result", {})
            assertion = verification.get("assertion")
            if not assertion or assertion in seen:
                continue
            seen[assertion] = {
                "name": assertion,
                "passed": bool(verification.get("passed")),
                "failure_reason": verification.get("failure_reason"),
            }
        return [
            seen.get(
                assertion,
                {
                    "name": assertion,
                    "passed": False,
                    "failure_reason": "assertion not observed in runtime results",
                },
            )
            for assertion in assertions
        ]

    def build_summary(
        self,
        testcase: dict[str, Any] | None,
        runtime_context: dict[str, Any],
    ) -> dict[str, Any]:
        started_at = _parse_iso(runtime_context.get("started_at"))
        completed_at = self._completed_at(runtime_context)
        duration_sec = 0.0
        if started_at is not None:
            duration_sec = max((completed_at - started_at).total_seconds(), 0.0)

        step_results = runtime_context.get("step_results", [])
        failed_steps = [step for step in step_results if step.get("status") != "passed"]
        passed_steps = len(step_results) - len(failed_steps)

        return {
            "task_id": (testcase or {}).get("id"),
            "product": (testcase or {}).get("product"),
            "workflow": runtime_context.get("workflow"),
            "status": runtime_context.get("status"),
            "steps": len((testcase or {}).get("steps", [])) or len(step_results),
            "passed_steps": passed_steps,
            "failed_steps": len(failed_steps),
            "duration_sec": round(duration_sec, 3),
            "assertions": self._assertion_results(testcase, runtime_context),
            "failure_type": runtime_context.get("failure_type"),
            "failure_reason": runtime_context.get("failure_reason"),
            "run_id": runtime_context.get("run_id"),
            "started_at": runtime_context.get("started_at"),
            "completed_at": completed_at.isoformat(),
        }

    def build_markdown(
        self,
        summary: dict[str, Any],
        runtime_context: dict[str, Any],
        testcase: dict[str, Any] | None = None,
    ) -> str:
        lines = [
            "# Feishu Run Report",
            "",
            "## Summary",
            f"- Run ID: `{summary.get('run_id')}`",
            f"- Task ID: `{summary.get('task_id')}`",
            f"- Product: `{summary.get('product')}`",
            f"- Workflow: `{summary.get('workflow')}`",
            f"- Status: `{summary.get('status')}`",
            f"- Duration (s): `{summary.get('duration_sec')}`",
            f"- Failure Type: `{summary.get('failure_type')}`",
            f"- Failure Reason: `{summary.get('failure_reason')}`",
            "",
            "## Assertions",
        ]
        for assertion in summary.get("assertions", []):
            lines.append(
                f"- `{assertion['name']}`: "
                f"{'passed' if assertion.get('passed') else 'failed'}"
            )
            if assertion.get("failure_reason"):
                lines.append(f"  reason: {assertion['failure_reason']}")

        lines.extend(["", "## Steps"])
        for step_result in runtime_context.get("step_results", []):
            lines.append(
                f"- `{step_result.get('step_id')}` "
                f"`{step_result.get('stage')}` "
                f"`{step_result.get('action')}` "
                f"=> `{step_result.get('status')}`"
            )
            if step_result.get("failure_reason"):
                lines.append(f"  reason: {step_result['failure_reason']}")

        screenshots = runtime_context.get("screenshots", [])
        lines.extend(["", "## Artifacts", f"- Screenshots: `{len(screenshots)}`"])
        for screenshot in screenshots:
            lines.append(f"- `{screenshot}`")

        if testcase is not None:
            lines.extend(
                ["", "## Original Task", f"- Title: `{testcase.get('title')}`"]
            )

        return "\n".join(lines) + "\n"

    def write_runtime_artifacts(
        self,
        testcase: dict[str, Any] | None,
        runtime_context: dict[str, Any],
    ) -> dict[str, str]:
        run_id = runtime_context["run_id"]
        summary = self.build_summary(testcase, runtime_context)
        report_md = self.build_markdown(summary, runtime_context, testcase=testcase)
        run_dir = self.artifact_manager.ensure_run_dirs(run_id)
        summary_path = self.artifact_manager.write_json(run_id, "summary.json", summary)
        report_path = self.artifact_manager.write_text(run_id, "report.md", report_md)
        actions_path = self.artifact_manager.write_actions_jsonl(
            run_id, runtime_context.get("action_logs", [])
        )
        return {
            "run_dir": str(run_dir),
            "summary": summary_path,
            "report": report_path,
            "actions": actions_path,
        }
