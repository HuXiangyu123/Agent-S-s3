"""Tests for offline Feishu batch evaluation aggregation."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from gui_agents.feishu.reports.evaluation_aggregator import (
    build_evaluation_markdown,
    build_evaluation_summary,
    discover_run_summaries,
    write_evaluation_report,
)


def _write_summary(root: Path, run_id: str, payload: dict[str, object]) -> None:
    run_dir = root / run_id
    run_dir.mkdir(parents=True)
    data = {
        "run_id": run_id,
        "task_id": "agentic_im_send_message",
        "product": "im",
        "status": "completed",
        "steps": 2,
        "passed_steps": 2,
        "failed_steps": 0,
        "duration_sec": 1.25,
        "failure_type": None,
        "failure_reason": None,
    }
    data.update(payload)
    (run_dir / "summary.json").write_text(
        json.dumps(data, ensure_ascii=False),
        encoding="utf-8",
    )


class TestEvaluationAggregator(unittest.TestCase):
    def test_discovers_run_summaries(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _write_summary(root, "run-a", {})
            _write_summary(root, "run-b", {"status": "failed"})
            (root / "not-a-run").mkdir()

            summaries = discover_run_summaries(root)

        self.assertEqual([item["run_id"] for item in summaries], ["run-a", "run-b"])
        self.assertTrue(all("_summary_path" in item for item in summaries))

    def test_builds_success_and_failure_aggregates(self) -> None:
        summaries = [
            {
                "run_id": "run-a",
                "task_id": "agentic_im_send_message",
                "product": "im",
                "status": "completed",
                "steps": 2,
                "passed_steps": 2,
                "failed_steps": 0,
                "duration_sec": 1.0,
                "failure_type": None,
            },
            {
                "run_id": "run-b",
                "task_id": "agentic_docs_create_doc",
                "product": "docs",
                "status": "failed",
                "steps": 3,
                "passed_steps": 1,
                "failed_steps": 2,
                "duration_sec": 5.0,
                "failure_type": "verification",
            },
        ]

        evaluation = build_evaluation_summary(
            summaries,
            generated_at="2026-05-06T00:00:00+08:00",
        )

        self.assertEqual(evaluation["total_runs"], 2)
        self.assertEqual(evaluation["completed_runs"], 1)
        self.assertEqual(evaluation["failed_runs"], 1)
        self.assertEqual(evaluation["success_rate"], 0.5)
        self.assertEqual(evaluation["average_duration_sec"], 3.0)
        self.assertEqual(evaluation["average_steps"], 2.5)
        self.assertEqual(evaluation["passed_steps"], 3)
        self.assertEqual(evaluation["failed_steps"], 2)
        self.assertEqual(evaluation["by_product"]["im"]["success_rate"], 1.0)
        self.assertEqual(evaluation["by_product"]["docs"]["success_rate"], 0.0)
        self.assertEqual(evaluation["by_failure_type"], {"verification": 1})

    def test_writes_evaluation_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "runs"
            output = Path(tmpdir) / "evaluation"
            _write_summary(root, "run-a", {})

            paths = write_evaluation_report(root, output)
            summary = json.loads(
                Path(paths["evaluation_summary"]).read_text(encoding="utf-8")
            )
            report = Path(paths["evaluation_report"]).read_text(encoding="utf-8")

        self.assertEqual(summary["total_runs"], 1)
        self.assertIn("# Feishu Batch Evaluation", report)
        self.assertIn("Success Rate", report)

    def test_markdown_handles_no_failures(self) -> None:
        markdown = build_evaluation_markdown(
            {
                "generated_at": "2026-05-06T00:00:00+08:00",
                "total_runs": 0,
                "completed_runs": 0,
                "failed_runs": 0,
                "success_rate": 0.0,
                "average_duration_sec": 0.0,
                "average_steps": 0.0,
                "passed_steps": 0,
                "failed_steps": 0,
                "by_product": {},
                "by_failure_type": {},
                "runs": [],
            }
        )

        self.assertIn("- none", markdown)

    def test_cli_writes_report_from_repo_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "runs"
            output = Path(tmpdir) / "evaluation"
            _write_summary(root, "run-a", {})

            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/build_feishu_eval_report.py",
                    "--artifact-root",
                    str(root),
                    "--output-dir",
                    str(output),
                ],
                cwd=Path(__file__).resolve().parents[3],
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("FEISHU_EVALUATION_SUMMARY:", completed.stdout)


if __name__ == "__main__":
    unittest.main()
