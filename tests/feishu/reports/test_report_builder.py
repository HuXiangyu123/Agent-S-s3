import tempfile
import unittest
from pathlib import Path

from gui_agents.feishu.maintenance.artifact_manager import ArtifactManager
from gui_agents.feishu.reports.report_builder import ReportBuilder


class TestReportBuilder(unittest.TestCase):
    def setUp(self) -> None:
        self.testcase = {
            "id": "tc_im_send_message_001",
            "product": "im",
            "title": "send message",
            "steps": [{}, {}, {}],
            "assertions": ["chat_title_matched", "message_sent"],
        }
        self.runtime = {
            "run_id": "20260506_010203",
            "status": "failed",
            "intent": "send_message",
            "params": {"chat_name": "bot功能测试", "message_text": "hello"},
            "page_id": "chat_main",
            "precondition_results": [],
            "action_logs": [
                {
                    "timestamp": "2026-05-06T01:02:04+08:00",
                    "step_id": "step_3",
                    "stage": "SEND_MESSAGE",
                    "action": "send_message",
                    "target": "send_button",
                    "params": {"text": "hello"},
                    "status": "failed",
                }
            ],
            "screenshots": ["artifacts/test_runs/20260506_010203/screenshots/step.png"],
            "step_results": [
                {
                    "step_id": "step_1",
                    "stage": "ENSURE_CHAT_OPEN",
                    "action": "open_chat",
                    "target": "bot功能测试",
                    "status": "passed",
                    "locator_result": {},
                    "verification_result": {
                        "assertion": "chat_title_matched",
                        "passed": True,
                        "failure_reason": None,
                    },
                    "failure_type": None,
                    "failure_reason": None,
                },
                {
                    "step_id": "step_3",
                    "stage": "SEND_MESSAGE",
                    "action": "send_message",
                    "target": "send_button",
                    "status": "failed",
                    "locator_result": {},
                    "verification_result": {
                        "assertion": "message_sent",
                        "passed": False,
                        "failure_reason": "sent message mismatch",
                    },
                    "failure_type": "verification",
                    "failure_reason": "sent message mismatch",
                },
            ],
            "failure_type": "verification",
            "failure_reason": "sent message mismatch",
            "started_at": "2026-05-06T01:02:03+08:00",
        }

    def test_build_summary_counts_steps_and_assertions(self) -> None:
        builder = ReportBuilder()
        summary = builder.build_summary(self.testcase, self.runtime)

        self.assertEqual(summary["task_id"], "tc_im_send_message_001")
        self.assertEqual(summary["intent"], "send_message")
        self.assertEqual(summary["steps"], 3)
        self.assertEqual(summary["passed_steps"], 1)
        self.assertEqual(summary["failed_steps"], 1)
        self.assertEqual(summary["failure_type"], "verification")
        self.assertEqual(summary["assertions"][0]["name"], "chat_title_matched")
        self.assertTrue(summary["assertions"][0]["passed"])
        self.assertEqual(summary["assertions"][1]["name"], "message_sent")
        self.assertFalse(summary["assertions"][1]["passed"])

    def test_build_markdown_includes_summary_and_steps(self) -> None:
        builder = ReportBuilder()
        summary = builder.build_summary(self.testcase, self.runtime)
        markdown = builder.build_markdown(summary, self.runtime, testcase=self.testcase)

        self.assertIn("# Feishu Run Report", markdown)
        self.assertIn("`send_message`", markdown)
        self.assertIn("`step_3`", markdown)
        self.assertIn("sent message mismatch", markdown)

    def test_write_runtime_artifacts_persists_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = ReportBuilder(ArtifactManager(tmpdir))
            paths = builder.write_runtime_artifacts(self.testcase, self.runtime)

            self.assertTrue(Path(paths["summary"]).exists())
            self.assertTrue(Path(paths["report"]).exists())
            self.assertTrue(Path(paths["actions"]).exists())

    def test_build_summary_supports_docs_agentic_runtime(self) -> None:
        testcase = {
            "id": "tc_docs_create_doc_001",
            "product": "docs",
            "title": "create doc",
            "steps": [{}, {}, {}, {}, {}],
            "assertions": ["doc_editor_ready", "doc_title_contains_text"],
        }
        runtime = {
            "run_id": "20260506_docs",
            "status": "passed",
            "intent": "create_doc_and_edit",
            "params": {"doc_title": "项目周报", "body_text": None},
            "page_id": "docs_browser_editor",
            "precondition_results": [],
            "action_logs": [],
            "screenshots": [],
            "step_results": [
                {
                    "step_id": "docs_wf_step_4",
                    "stage": "SELECT_BLANK_DOC",
                    "action": "select_blank_doc_template",
                    "target": "docs_blank_doc_card",
                    "status": "passed",
                    "locator_result": {},
                    "verification_result": {
                        "assertion": "doc_editor_ready",
                        "passed": True,
                        "failure_reason": None,
                    },
                    "failure_type": None,
                    "failure_reason": None,
                },
                {
                    "step_id": "docs_wf_step_5",
                    "stage": "TYPE_DOC_TITLE",
                    "action": "type_doc_title",
                    "target": "docs_title_input",
                    "status": "passed",
                    "locator_result": {},
                    "verification_result": {
                        "assertion": "doc_title_contains_text",
                        "passed": True,
                        "failure_reason": None,
                    },
                    "failure_type": None,
                    "failure_reason": None,
                },
            ],
            "failure_type": None,
            "failure_reason": None,
            "started_at": "2026-05-06T01:02:03+08:00",
        }

        summary = ReportBuilder().build_summary(testcase, runtime)

        self.assertEqual(summary["product"], "docs")
        self.assertEqual(summary["intent"], "create_doc_and_edit")
        self.assertEqual(summary["failed_steps"], 0)
        self.assertTrue(summary["assertions"][0]["passed"])

    def test_build_summary_supports_base_agentic_runtime(self) -> None:
        testcase = {
            "id": "tc_base_agentic_runtime_001",
            "product": "base",
            "title": "base semantic runtime",
            "steps": [{}, {}],
            "assertions": ["base_home_ready", "base_editor_ready"],
        }
        runtime = {
            "run_id": "20260506_base",
            "status": "passed",
            "intent": "base_semantic_task",
            "params": {},
            "page_id": "base_browser_table",
            "precondition_results": [],
            "action_logs": [],
            "screenshots": [],
            "step_results": [
                {
                    "step_id": "base_agent_step_1",
                    "stage": "OBSERVE_BASE_HOME",
                    "action": "click",
                    "target": "base home new button",
                    "status": "passed",
                    "locator_result": {},
                    "verification_result": {
                        "assertion": "base_home_ready",
                        "passed": True,
                        "failure_reason": None,
                    },
                    "failure_type": None,
                    "failure_reason": None,
                },
                {
                    "step_id": "base_agent_step_2",
                    "stage": "OBSERVE_BASE_EDITOR",
                    "action": "click",
                    "target": "blank base table card",
                    "status": "passed",
                    "locator_result": {},
                    "verification_result": {
                        "assertion": "base_editor_ready",
                        "passed": True,
                        "failure_reason": None,
                    },
                    "failure_type": None,
                    "failure_reason": None,
                },
            ],
            "failure_type": None,
            "failure_reason": None,
            "started_at": "2026-05-06T01:02:03+08:00",
        }

        summary = ReportBuilder().build_summary(testcase, runtime)

        self.assertEqual(summary["product"], "base")
        self.assertEqual(summary["intent"], "base_semantic_task")
        self.assertEqual(summary["failed_steps"], 0)
        self.assertTrue(summary["assertions"][1]["passed"])

    def test_build_summary_uses_runtime_identity_without_testcase(self) -> None:
        runtime = {
            "run_id": "20260506_vc",
            "status": "completed",
            "intent": "agent_s3_feishu",
            "params": {"instruction": "发起视频会议并验证进入成功"},
            "product": "vc",
            "task_id": "agentic_vc_start_meeting",
            "task_title": "发起视频会议并验证进入成功",
            "assertion_plan": [{"assertion": "vc_meeting_active", "expected": {}}],
            "page_id": "vc_meeting_active",
            "precondition_results": [],
            "action_logs": [],
            "screenshots": [],
            "step_results": [
                {
                    "step_id": "final_assertion_1",
                    "stage": "FINAL_ASSERTION",
                    "action": "verify_assertion",
                    "target": "vc_meeting_active",
                    "status": "passed",
                    "locator_result": {},
                    "verification_result": {
                        "assertion": "vc_meeting_active",
                        "passed": True,
                        "failure_reason": None,
                    },
                    "failure_type": None,
                    "failure_reason": None,
                }
            ],
            "failure_type": None,
            "failure_reason": None,
            "started_at": "2026-05-06T01:02:03+08:00",
        }

        summary = ReportBuilder().build_summary(None, runtime)

        self.assertEqual(summary["product"], "vc")
        self.assertEqual(summary["task_id"], "agentic_vc_start_meeting")
        self.assertEqual(summary["assertions"][0]["name"], "vc_meeting_active")
        self.assertTrue(summary["assertions"][0]["passed"])
