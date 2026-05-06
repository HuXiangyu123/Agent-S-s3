"""RuntimeContext contract tests for advanced feature field freeze."""

import unittest


class TestRuntimeContextContract(unittest.TestCase):
    def test_advanced_feature_fields_are_optional(self) -> None:
        from gui_agents.feishu.contracts import RuntimeContext

        expected_fields = {
            "recovery_attempts",
            "anomaly_events",
            "semantic_steps",
        }

        self.assertTrue(expected_fields.issubset(RuntimeContext.__annotations__))

        for field in expected_fields:
            annotation = RuntimeContext.__annotations__[field]
            annotation_text = getattr(annotation, "__forward_arg__", str(annotation))
            self.assertTrue(annotation_text.startswith("NotRequired["))

    def test_minimal_runtime_context_stays_compatible(self) -> None:
        from gui_agents.feishu.contracts import RuntimeContext

        context: RuntimeContext = {
            "run_id": "run-contract-test",
            "status": "running",
            "intent": None,
            "params": {},
            "page_id": None,
            "precondition_results": [],
            "action_logs": [],
            "screenshots": [],
            "step_results": [],
            "failure_type": None,
            "failure_reason": None,
            "started_at": "2026-05-06T00:00:00+08:00",
        }

        self.assertNotIn("recovery_attempts", context)
        self.assertNotIn("anomaly_events", context)
        self.assertNotIn("semantic_steps", context)


if __name__ == "__main__":
    unittest.main()
