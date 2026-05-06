"""Filesystem helpers for Feishu runtime artifacts."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def _safe_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return cleaned.strip("._") or "artifact"


class ArtifactManager:
    """Create and write stable Track D run artifacts."""

    def __init__(self, root_dir: str | Path | None = None) -> None:
        base = Path(root_dir) if root_dir is not None else Path("artifacts/test_runs")
        self.root_dir = base

    def run_dir(self, run_id: str) -> Path:
        return self.root_dir / _safe_name(run_id)

    def screenshots_dir(self, run_id: str) -> Path:
        return self.run_dir(run_id) / "screenshots"

    def ensure_run_dirs(self, run_id: str) -> Path:
        run_dir = self.run_dir(run_id)
        self.screenshots_dir(run_id).mkdir(parents=True, exist_ok=True)
        return run_dir

    def write_json(self, run_id: str, filename: str, payload: Any) -> str:
        run_dir = self.ensure_run_dirs(run_id)
        path = run_dir / _safe_name(filename)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return str(path)

    def write_text(self, run_id: str, filename: str, content: str) -> str:
        run_dir = self.ensure_run_dirs(run_id)
        path = run_dir / _safe_name(filename)
        path.write_text(content, encoding="utf-8")
        return str(path)

    def write_actions_jsonl(
        self, run_id: str, action_logs: list[dict[str, Any]]
    ) -> str:
        run_dir = self.ensure_run_dirs(run_id)
        path = run_dir / "actions.jsonl"
        lines = [
            json.dumps(action_log, ensure_ascii=False, sort_keys=True)
            for action_log in action_logs
        ]
        path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        return str(path)

    def write_screenshot(self, run_id: str, label: str, png_bytes: bytes) -> str:
        screenshots_dir = self.screenshots_dir(run_id)
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        path = screenshots_dir / f"{_safe_name(label)}.png"
        path.write_bytes(png_bytes)
        return str(path)
