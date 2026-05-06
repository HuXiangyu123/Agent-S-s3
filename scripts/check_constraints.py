"""
Project-wide constraint checker.

Verifies that no deterministic workflow execution path (FeishuWorker /
feishu_workflow) has crept back into code or active documentation.

Run: python scripts/check_constraints.py
Part of CI parity: invoked by run_ci_checks.py.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
# Common lists
# ---------------------------------------------------------------------------

FORBIDDEN_PATTERNS: list[tuple[str, str]] = [
    # (pattern, human-readable description)
    (r'execution_mode\s*[=:"]\s*["\']feishu_workflow["\']', "execution_mode = 'feishu_workflow' in code"),
    (r'choices\s*=\s*\[.*["\']feishu_workflow["\']', "feishu_workflow in argparse choices"),
]

FORBIDDEN_DOC_PATTERNS: list[tuple[str, str]] = [
    # (regex, description) -- matched against each non-archive doc line
    (r'feishu_worker\.py', "references feishu_worker.py as active file"),
]

# Docs that are historical / archive, exempt from doc checks
DOC_EXEMPT_DIRS: set[str] = {"archive"}

# Docs that are known refactoring records — they describe what was removed,
# not what should be built. Exempt from target-file checks.
DOC_EXEMPT_FILES: set[str] = {
    "s3_feishu_agentic_tools_refactor_2026-05-05.md",
    "feishu_agent_migration_remove_workflows_2026-05-06.md",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _iter_py_files(root: Path):
    for p in root.rglob("*.py"):
        if "__pycache__" in str(p):
            continue
        yield p


def _iter_doc_files(root: Path, exempt_dirs: set[str]):
    for p in sorted(root.rglob("*.md")):
        if any(ex in p.parts for ex in exempt_dirs):
            continue
        yield p


def _read(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


# ---------------------------------------------------------------------------
# Code checks
# ---------------------------------------------------------------------------

def check_no_feishu_worker_file() -> list[str]:
    """feishu_worker.py must not exist."""
    path = REPO_ROOT / "gui_agents" / "feishu" / "agents" / "feishu_worker.py"
    if path.exists():
        return [f"FORBIDDEN FILE: {path.relative_to(REPO_ROOT)} exists (must be deleted)"]
    return []


def check_no_feishu_worker_import() -> list[str]:
    """No Python file should import FeishuWorker from feishu.agents."""
    errors = []
    import_re = re.compile(r"(from\s+gui_agents\.feishu\.agents\s+import\s+FeishuWorker|"
                           r"from\s+gui_agents\.feishu\.agents\.feishu_worker\s+import)")
    for py_file in _iter_py_files(REPO_ROOT / "gui_agents"):
        for lineno, line in enumerate(_read(py_file), 1):
            if import_re.search(line):
                errors.append(f"{py_file.relative_to(REPO_ROOT)}:{lineno}: imports FeishuWorker")
    return errors


def check_no_feishu_worker_all() -> list[str]:
    """gui_agents/feishu/agents/__init__.py must not export FeishuWorker."""
    init = REPO_ROOT / "gui_agents" / "feishu" / "agents" / "__init__.py"
    if init.exists():
        text = init.read_text(encoding="utf-8")
        if re.search(r"FeishuWorker", text):
            return [f"{init.relative_to(REPO_ROOT)}: exports FeishuWorker in __all__ or imports"]
    return []


def check_execution_modes() -> list[str]:
    """cli_app.py choices and launcher.py EXECUTION_MODES must be clean."""
    errors = []
    # cli_app.py argparse choices
    cli = REPO_ROOT / "gui_agents" / "s3" / "cli_app.py"
    if cli.exists():
        text = cli.read_text(encoding="utf-8")
        if '"feishu_workflow"' in text:
            errors.append(f"{cli.relative_to(REPO_ROOT)}: feishu_workflow in argparse choices")
        # Must include feishu_agent
        if 'choices=["classic_s3", "feishu_agent"]' not in text:
            errors.append(f"{cli.relative_to(REPO_ROOT)}: execution_mode choices changed from expected values")

    # launcher.py EXECUTION_MODES
    launcher = REPO_ROOT / "launcher.py"
    if launcher.exists():
        for lineno, line in enumerate(_read(launcher), 1):
            if re.search(r"feishu_workflow", line):
                errors.append(f"launcher.py:{lineno}: feishu_workflow in EXECUTION_MODES")

    return errors


def check_no_forbidden_code_patterns() -> list[str]:
    """Scan all Python files for forbidden execution patterns."""
    errors = []
    for py_file in _iter_py_files(REPO_ROOT / "gui_agents"):
        text = py_file.read_text(encoding="utf-8")
        for pattern, desc in FORBIDDEN_PATTERNS:
            if re.search(pattern, text):
                errors.append(f"{py_file.relative_to(REPO_ROOT)}: {desc}")
    return errors


def check_no_deterministic_executor() -> list[str]:
    """Check feishu/ directory for deterministic run_testcase/run_instruction methods."""
    errors = []
    feishu_dir = REPO_ROOT / "gui_agents" / "feishu"
    if not feishu_dir.exists():
        return errors
    for py_file in _iter_py_files(feishu_dir):
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name in ("run_testcase", "run_instruction"):
                    # Check if this is in a class that looks like a deterministic executor
                    for parent in ast.iter_child_nodes(tree):
                        if isinstance(parent, ast.ClassDef):
                            for child in ast.walk(parent):
                                if child is node:
                                    if node.name in ("run_testcase", "run_instruction"):
                                        errors.append(
                                            f"{py_file.relative_to(REPO_ROOT)}:{node.lineno}: "
                                            f"deterministic {node.name}() in class {parent.name}"
                                        )
    return errors


def check_no_deterministic_planner_or_workflows() -> list[str]:
    """Planner selectors and concrete workflow modules must not exist."""
    forbidden_paths = [
        REPO_ROOT / "gui_agents" / "feishu" / "planner" / "task_planner.py",
        REPO_ROOT / "gui_agents" / "feishu" / "planner" / "workflow_selector.py",
        REPO_ROOT / "tests" / "feishu" / "planner" / "test_task_planner.py",
    ]
    errors = [
        f"FORBIDDEN FILE: {path.relative_to(REPO_ROOT)} exists"
        for path in forbidden_paths
        if path.exists()
    ]

    workflow_dir = REPO_ROOT / "gui_agents" / "feishu" / "workflows"
    if workflow_dir.exists():
        for path in workflow_dir.glob("*_workflow.py"):
            errors.append(f"FORBIDDEN FILE: {path.relative_to(REPO_ROOT)} exists")

    workflow_test_dir = REPO_ROOT / "tests" / "feishu" / "workflows"
    if workflow_test_dir.exists():
        for path in workflow_test_dir.glob("test_*workflow*.py"):
            errors.append(f"FORBIDDEN FILE: {path.relative_to(REPO_ROOT)} exists")

    return errors


def check_semantic_static_feishu_metadata() -> list[str]:
    """Static Feishu descriptors/fixtures must not carry workflow or click priors."""
    errors = []
    forbidden = (
        "relative_bounds",
        '"bbox"',
        '"confidence"',
        "supported_workflows",
        "workflow_support",
    )
    checks = [
        (REPO_ROOT / "gui_agents" / "feishu" / "pages", "*.py"),
        (REPO_ROOT / "tests" / "fixtures", "*.json"),
    ]
    for root, pattern in checks:
        for path in root.rglob(pattern):
            text = path.read_text(encoding="utf-8-sig")
            for token in forbidden:
                if token in text:
                    errors.append(
                        f"{path.relative_to(REPO_ROOT)}: static metadata contains {token}"
                    )
    return errors


def check_no_static_relative_locator_path() -> list[str]:
    """Feishu locators and runtime priors must not read static relative bounds."""
    errors = []
    forbidden_patterns = [
        (re.compile(r"region\.get\([\"']relative_bounds[\"']\)"), "reads region relative_bounds"),
        (re.compile(r"_relative_bounds_center"), "relative bounds center helper"),
        (re.compile(r"_relative_region_click_code"), "relative region click helper"),
        (re.compile(r"\bOFFSETS\s*="), "hard-coded toolbar offsets"),
    ]
    roots = [
        REPO_ROOT / "gui_agents" / "feishu",
        REPO_ROOT / "gui_agents" / "s3" / "agents",
    ]
    for root in roots:
        for py_file in _iter_py_files(root):
            text = py_file.read_text(encoding="utf-8")
            for pattern, desc in forbidden_patterns:
                if pattern.search(text):
                    errors.append(f"{py_file.relative_to(REPO_ROOT)}: {desc}")
    return errors


# ---------------------------------------------------------------------------
# Doc checks
# ---------------------------------------------------------------------------

def check_docs_no_target_file() -> list[str]:
    """Implementation docs must not list feishu_worker.py as a target file."""
    errors = []
    target_re = re.compile(r"`gui_agents/feishu/agents/feishu_worker\.py`")
    for doc in _iter_doc_files(REPO_ROOT / "docs" / "implementation", DOC_EXEMPT_DIRS):
        if doc.name in DOC_EXEMPT_FILES:
            continue
        for lineno, line in enumerate(_read(doc), 1):
            if target_re.search(line):
                # Allow lines that explicitly say "do not", "remove", or are in a rollback/revert context
                lower = line.lower()
                if any(kw in lower for kw in ("do not", "remove", "revert", "rollback", "deleted", "superseded")):
                    continue
                errors.append(f"{doc.relative_to(REPO_ROOT)}:{lineno}: lists feishu_worker.py as target")
    return errors


def check_docs_no_active_worker() -> list[str]:
    """Source-of-truth docs must not describe FeishuWorker as active runtime."""
    errors = []
    # Positive descriptor patterns that indicate FeishuWorker is active
    active_patterns = [
        (re.compile(r"`FeishuWorker`\s*(是|为|负责).*执行"), "describes FeishuWorker as active executor"),
        (re.compile(r"FeishuWorker\s*是执行中枢"), "describes FeishuWorker as execution core"),
        (re.compile(r"class\s+FeishuWorker"), "defines FeishuWorker class (interface doc)"),
    ]
    sot_dirs = ["docs/spec", "docs/interfaces", "docs/feishu_gui_agent_master_plan.md"]
    for entry in sot_dirs:
        path = REPO_ROOT / entry
        if path.is_dir():
            for doc in _iter_doc_files(path, set()):
                text = doc.read_text(encoding="utf-8")
                for pat, desc in active_patterns:
                    if pat.search(text):
                        errors.append(f"{doc.relative_to(REPO_ROOT)}: {desc}")
        elif path.is_file():
            for pat, desc in active_patterns:
                if pat.search(path.read_text(encoding="utf-8")):
                    errors.append(f"{path.relative_to(REPO_ROOT)}: {desc}")
    return errors


def check_docs_no_active_workflow_design() -> list[str]:
    """Source-of-truth docs must not restore fixed planner/workflow design."""
    errors = []
    active_patterns = [
        (re.compile(r"Planner\s*/\s*Workflow\s+Selector"), "restores Planner / Workflow Selector"),
        (re.compile(r"\bWorkflowPlan\b"), "references WorkflowPlan outside removal guidance"),
        (re.compile(r"\bBaseWorkflow\b"), "defines or references BaseWorkflow outside removal guidance"),
        (re.compile(r"\bSendMessageWorkflow\b"), "references concrete workflow class"),
        (re.compile(r"task_planner\.py"), "references task_planner.py"),
        (re.compile(r"workflow_selector\.py"), "references workflow_selector.py"),
        (re.compile(r"workflow\s+驱动执行"), "describes workflow-driven execution"),
        (re.compile(r"workflow\s+必须是显式阶段机"), "requires explicit workflow stage machines"),
    ]
    allowed_markers = (
        "不",
        "不得",
        "不再",
        "废弃",
        "deprecated",
        "removed",
        "删除",
        "历史",
        "归档",
        "兼容",
        "禁止",
        "严禁",
        "reject",
        "rejected",
    )
    sot_entries = [
        REPO_ROOT / "AGENTS.md",
        REPO_ROOT / "docs" / "feishu_gui_agent_master_plan.md",
        REPO_ROOT / "docs" / "spec",
        REPO_ROOT / "docs" / "interfaces",
        REPO_ROOT / "docs" / "implementation",
    ]
    for entry in sot_entries:
        docs = [entry] if entry.is_file() else list(_iter_doc_files(entry, set()))
        for doc in docs:
            if doc.name in DOC_EXEMPT_FILES:
                continue
            text = doc.read_text(encoding="utf-8")
            if "docs\\implementation" in str(doc.relative_to(REPO_ROOT)):
                if any(
                    marker in text
                    for marker in (
                        "Superseded",
                        "Historical implementation record",
                        "Runtime route corrected",
                        "Partially superseded",
                    )
                ):
                    continue
            for lineno, line in enumerate(_read(doc), 1):
                lowered = line.lower()
                if any(marker in lowered for marker in allowed_markers):
                    continue
                for pat, desc in active_patterns:
                    if pat.search(line):
                        errors.append(f"{doc.relative_to(REPO_ROOT)}:{lineno}: {desc}")
    return errors


def check_agents_md() -> list[str]:
    """AGENTS.md must not list feishu_worker.py in high-coupling or serial-track."""
    errors = []
    agents_md = REPO_ROOT / "AGENTS.md"
    if agents_md.exists():
        text = agents_md.read_text(encoding="utf-8")
        if re.search(r"feishu_worker\.py", text):
            errors.append("AGENTS.md: still references feishu_worker.py")
    return errors


def check_master_plan() -> list[str]:
    """Master plan must not show FeishuWorker in architecture diagram."""
    errors = []
    mp = REPO_ROOT / "docs" / "feishu_gui_agent_master_plan.md"
    if mp.exists():
        text = mp.read_text(encoding="utf-8")
        if re.search(r"->\s*FeishuWorker", text):
            errors.append("docs/feishu_gui_agent_master_plan.md: FeishuWorker in architecture pipeline")
    return errors


def check_ci_parity() -> list[str]:
    """run_ci_checks.py must include this constraint check."""
    errors = []
    ci = REPO_ROOT / "scripts" / "run_ci_checks.py"
    if ci.exists():
        text = ci.read_text(encoding="utf-8")
        if "check_constraints" not in text:
            errors.append("scripts/run_ci_checks.py: does not include check_constraints step")
    return errors


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    all_errors: list[str] = []
    checks = [
        ("code: no feishu_worker.py file", check_no_feishu_worker_file),
        ("code: no FeishuWorker imports", check_no_feishu_worker_import),
        ("code: __init__ clean", check_no_feishu_worker_all),
        ("code: execution modes clean", check_execution_modes),
        ("code: no forbidden patterns", check_no_forbidden_code_patterns),
        ("code: no deterministic executor", check_no_deterministic_executor),
        (
            "code: no deterministic planner/workflows",
            check_no_deterministic_planner_or_workflows,
        ),
        ("code: semantic static Feishu metadata", check_semantic_static_feishu_metadata),
        ("code: no static relative locator path", check_no_static_relative_locator_path),
        ("docs: implementation no target file", check_docs_no_target_file),
        ("docs: SOT no active worker", check_docs_no_active_worker),
        ("docs: SOT no active workflow design", check_docs_no_active_workflow_design),
        ("docs: AGENTS.md clean", check_agents_md),
        ("docs: master_plan clean", check_master_plan),
        ("docs: CI parity", check_ci_parity),
    ]

    for name, func in checks:
        errors = func()
        if errors:
            print(f"[FAIL] {name}")
            for e in errors:
                print(f"  {e}")
            all_errors.extend(errors)
        else:
            print(f"[PASS] {name}")

    if all_errors:
        print(f"\n{len(all_errors)} constraint violation(s) found.")
        return 1
    print("\n[OK] All constraints passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
