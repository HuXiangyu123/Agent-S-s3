from pathlib import Path
import unittest

from gui_agents.feishu.detectors.im_state_detector import detect_feishu_state
from gui_agents.feishu.verifiers.assertion_verifier import AssertionVerifier


IM_FIXTURE_DIR = Path("tests/fixtures/im")


class TestAssertionVerifier(unittest.TestCase):
    def setUp(self) -> None:
        self.verifier = AssertionVerifier()

    def _observation(self, filename: str) -> dict:
        return {"image_path": str(IM_FIXTURE_DIR / filename)}

    def test_verifies_chat_title_match(self) -> None:
        observation = self._observation("im_chat_main_full.png")
        state = detect_feishu_state(observation)

        result = self.verifier.verify_assertion(
            "chat_title_matched",
            state,
            observation,
            expected={"chat_name": "bot功能测试"},
        )

        self.assertTrue(result["passed"])
        self.assertEqual(result["assertion"], "chat_title_matched")

    def test_verifies_message_input_contains_text(self) -> None:
        observation = self._observation("im_message_draft_visible.png")
        state = detect_feishu_state(observation)

        result = self.verifier.verify_assertion(
            "message_input_contains_text",
            state,
            observation,
            expected={"message_text": "测试文字"},
        )

        self.assertTrue(result["passed"])
        self.assertIn("draft_present=True", result["evidence"])

    def test_verifies_message_sent(self) -> None:
        observation = self._observation("im_message_sent_visible.png")
        state = detect_feishu_state(observation)

        result = self.verifier.verify_assertion(
            "message_sent",
            state,
            observation,
            expected={"message_text": "测试文字"},
        )

        self.assertTrue(result["passed"])
        self.assertIn("message_sent_visible=True", result["evidence"])

    def test_returns_structured_failure_for_mismatch(self) -> None:
        observation = self._observation("im_message_draft_visible.png")
        state = detect_feishu_state(observation)

        result = self.verifier.verify_assertion(
            "message_input_contains_text",
            state,
            observation,
            expected={"message_text": "错误文本"},
        )

        self.assertFalse(result["passed"])
        self.assertEqual(result["failure_type"], "verification")
        self.assertIn("mismatch", result["failure_reason"])

    def test_verify_step_wraps_step_id(self) -> None:
        observation = self._observation("im_message_sent_visible.png")
        state = detect_feishu_state(observation)

        result = self.verifier.verify_step(
            {
                "step_id": "step_3",
                "assertion": "message_sent",
                "payload": {"text": "测试文字"},
            },
            state,
            observation,
        )

        self.assertTrue(result["passed"])
        self.assertEqual(result["step_id"], "step_3")

    def test_message_input_verifier_supports_ocr_fallback(self) -> None:
        result = self.verifier.verify_assertion(
            "message_input_contains_text",
            {
                "page_type": "chat_main",
                "product": "im",
                "chat_name": "bot功能测试",
                "message_input_visible": True,
                "send_button_visible": True,
                "search_box_visible": False,
                "modal_type": None,
                "last_error_banner": None,
                "product_state": {},
            },
            {"ocr_text": "发送给 bot功能测试\n测试文字\n发送"},
            expected={"params": {"text": "测试文字"}},
        )

        self.assertTrue(result["passed"])
        self.assertIn("source=ocr_fallback", result["evidence"])

    def test_message_sent_verifier_supports_ocr_fallback(self) -> None:
        result = self.verifier.verify_assertion(
            "message_sent",
            {
                "page_type": "chat_main",
                "product": "im",
                "chat_name": "bot功能测试",
                "message_input_visible": True,
                "send_button_visible": True,
                "search_box_visible": False,
                "modal_type": None,
                "last_error_banner": None,
                "product_state": {},
            },
            {"ocr_text": "bot功能测试\n测试文字\n19:20"},
            expected={"params": {"text": "测试文字"}},
        )

        self.assertTrue(result["passed"])
        self.assertIn("source=ocr_fallback", result["evidence"])


if __name__ == "__main__":
    unittest.main()
