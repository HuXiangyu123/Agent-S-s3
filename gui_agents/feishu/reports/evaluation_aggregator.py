"""Offline aggregation for Feishu run evaluation artifacts."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any


def _now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat()


def _safe_number(value: Any) -> float:
    if isinstance(value, bool):
        return 0.0
    if isinstance(value, int | float):
        return float(value)
    return 0.0


def _percent(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 4)


def discover_run_summaries(artifact_root: str | Path) -> list[dict[str, Any]]:
    """Load `summary.json` files from immediate run directories."""

    root = Path(artifact_root)
    if not root.exists():
        return []

    summaries: list[dict[str, Any]] = []
    for summary_path in sorted(root.glob("*/summary.json")):
        try:
            payload = json.loads(summary_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            payload = dict(payload)
            payload["_summary_path"] = str(summary_path)
            summaries.append(payload)
    return summaries


def _count_by_field(summaries: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for summary in summaries:
        value = summary.get(field) or "unknown"
        key = str(value)
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _success_by_field(
    summaries: list[dict[str, Any]],
    field: str,
) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for summary in summaries:
        key = str(summary.get(field) or "unknown")
        grouped.setdefault(key, []).append(summary)

    output: dict[str, dict[str, Any]] = {}
    for key, items in sorted(grouped.items()):
        completed = sum(1 for item in items if item.get("status") == "completed")
        output[key] = {
            "runs": len(items),
            "completed": completed,
            "failed": len(items) - completed,
            "success_rate": _percent(completed, len(items)),
        }
    return output


def build_evaluation_summary(
    summaries: list[dict[str, Any]],
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build aggregate evaluation facts from per-run summaries."""

    total_runs = len(summaries)
    completed_runs = sum(
        1 for summary in summaries if summary.get("status") == "completed"
    )
    failed_runs = total_runs - completed_runs
    durations = [_safe_number(summary.get("duration_sec")) for summary in summaries]
    steps = [_safe_number(summary.get("steps")) for summary in summaries]
    passed_steps = sum(
        int(_safe_number(summary.get("passed_steps"))) for summary in summaries
    )
    failed_steps = sum(
        int(_safe_number(summary.get("failed_steps"))) for summary in summaries
    )

    return {
        "generated_at": generated_at or _now_iso(),
        "total_runs": total_runs,
        "completed_runs": completed_runs,
        "failed_runs": failed_runs,
        "success_rate": _percent(completed_runs, total_runs),
        "average_duration_sec": (
            round(sum(durations) / total_runs, 3) if total_runs else 0.0
        ),
        "average_steps": round(sum(steps) / total_runs, 3) if total_runs else 0.0,
        "passed_steps": passed_steps,
        "failed_steps": failed_steps,
        "by_product": _success_by_field(summaries, "product"),
        "by_task": _success_by_field(summaries, "task_id"),
        "by_failure_type": _count_by_field(
            [summary for summary in summaries if summary.get("status") != "completed"],
            "failure_type",
        ),
        "runs": [
            {
                "run_id": summary.get("run_id"),
                "task_id": summary.get("task_id"),
                "product": summary.get("product"),
                "status": summary.get("status"),
                "failure_type": summary.get("failure_type"),
                "duration_sec": summary.get("duration_sec"),
                "summary_path": summary.get("_summary_path"),
            }
            for summary in summaries
        ],
    }


def build_evaluation_markdown(evaluation: dict[str, Any]) -> str:
    """Build a human-readable batch evaluation report."""

    lines = [
        "# Feishu Batch Evaluation",
        "",
        "## Summary",
        f"- Generated At: `{evaluation.get('generated_at')}`",
        f"- Total Runs: `{evaluation.get('total_runs')}`",
        f"- Completed Runs: `{evaluation.get('completed_runs')}`",
        f"- Failed Runs: `{evaluation.get('failed_runs')}`",
        f"- Success Rate: `{evaluation.get('success_rate')}`",
        f"- Average Duration (s): `{evaluation.get('average_duration_sec')}`",
        f"- Average Steps: `{evaluation.get('average_steps')}`",
        f"- Passed Steps: `{evaluation.get('passed_steps')}`",
        f"- Failed Steps: `{evaluation.get('failed_steps')}`",
        "",
        "## By Product",
    ]

    for product, item in evaluation.get("by_product", {}).items():
        lines.append(
            f"- `{product}`: runs `{item['runs']}`, completed `{item['completed']}`, "
            f"failed `{item['failed']}`, success_rate `{item['success_rate']}`"
        )

    lines.extend(["", "## By Failure Type"])
    failure_types = evaluation.get("by_failure_type", {})
    if failure_types:
        for failure_type, count in failure_types.items():
            lines.append(f"- `{failure_type}`: `{count}`")
    else:
        lines.append("- none")

    lines.extend(["", "## Runs"])
    for run in evaluation.get("runs", []):
        lines.append(
            f"- `{run.get('run_id')}` `{run.get('product')}` `{run.get('task_id')}` "
            f"=> `{run.get('status')}`"
        )
    return "\n".join(lines) + "\n"


def write_evaluation_report(
    artifact_root: str | Path,
    output_dir: str | Path,
) -> dict[str, str]:
    """Aggregate run summaries and write evaluation artifacts."""

    summaries = discover_run_summaries(artifact_root)
    evaluation = build_evaluation_summary(summaries)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    summary_path = output_path / "evaluation_summary.json"
    report_path = output_path / "evaluation_report.md"
    summary_path.write_text(
        json.dumps(evaluation, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    report_path.write_text(build_evaluation_markdown(evaluation), encoding="utf-8")
    return {
        "evaluation_summary": str(summary_path),
        "evaluation_report": str(report_path),
    }
