from pathlib import Path
import unittest

from gui_agents.feishu.detectors.im_state_detector import detect_feishu_state


IM_FIXTURE_DIR = Path("tests/fixtures/im")
SHELL_FIXTURE_DIR = Path("tests/fixtures/feishu_shell")


class TestIMStateDetector(unittest.TestCase):
    def _im_observation(self, filename: str) -> dict:
        return {"image_path": str(IM_FIXTURE_DIR / filename)}

    def _shell_observation(self, filename: str) -> dict:
        return {"image_path": str(SHELL_FIXTURE_DIR / filename)}

    def test_detects_chat_main_from_full_fixture(self) -> None:
        state = detect_feishu_state(self._im_observation("im_chat_main_full.png"))

        self.assertEqual(state["product"], "im")
        self.assertEqual(state["page_type"], "chat_main")
        self.assertEqual(state["chat_name"], "bot功能测试")
        self.assertTrue(state["message_input_visible"])
        self.assertTrue(state["send_button_visible"])
        self.assertFalse(state["search_box_visible"])
        self.assertEqual(
            state["product_state"]["active_conversation_item_text"], "bot功能测试"
        )
        self.assertEqual(
            state["product_state"]["visible_conversation_items"], ["bot功能测试"]
        )
        self.assertEqual(state["product_state"]["draft_present"], False)

    def test_detects_placeholder_state(self) -> None:
        state = detect_feishu_state(
            self._im_observation("im_message_placeholder_visible.png")
        )

        self.assertTrue(state["message_input_visible"])
        self.assertTrue(state["send_button_visible"])
        self.assertFalse(state["product_state"]["draft_present"])
        self.assertFalse(state["product_state"]["send_button_enabled"])

    def test_detects_draft_state(self) -> None:
        state = detect_feishu_state(
            self._im_observation("im_message_draft_visible.png")
        )

        self.assertTrue(state["message_input_visible"])
        self.assertTrue(state["product_state"]["draft_present"])
        self.assertEqual(state["product_state"]["draft_text"], "测试文字")
        self.assertTrue(state["product_state"]["send_button_enabled"])

    def test_detects_sent_state(self) -> None:
        state = detect_feishu_state(self._im_observation("im_message_sent_visible.png"))

        self.assertTrue(state["message_input_visible"])
        self.assertTrue(state["product_state"]["message_sent_visible"])
        self.assertEqual(state["product_state"]["sent_message_text"], "测试文字")

    def test_detects_in_chat_search_panel_state(self) -> None:
        state = detect_feishu_state(
            self._im_observation("im_message_searchchat_visible.png")
        )

        self.assertEqual(state["product"], "im")
        self.assertEqual(state["page_type"], "chat_search_panel")
        self.assertFalse(state["message_input_visible"])
        self.assertFalse(state["send_button_visible"])
        self.assertTrue(state["search_box_visible"])
        self.assertTrue(state["product_state"]["local_search_panel_visible"])
        self.assertTrue(state["product_state"]["local_search_filters_visible"])
        self.assertTrue(state["product_state"]["local_search_empty_hint_visible"])
        self.assertFalse(state["product_state"]["local_search_result_list_visible"])

    def test_detects_real_in_chat_search_result_state(self) -> None:
        state = detect_feishu_state(
            self._im_observation("im_message_searchresult_visible.png")
        )

        self.assertEqual(state["page_type"], "chat_search_panel")
        self.assertTrue(state["product_state"]["local_search_result_list_visible"])
        self.assertFalse(state["product_state"]["local_search_empty_hint_visible"])
        self.assertEqual(state["product_state"]["search_query"], "需求")
        self.assertIn(
            "…实现了然后还要实现哪些需求",
            state["product_state"]["visible_conversation_search_results"],
        )

    def test_detects_search_result_context_jump_state(self) -> None:
        state = detect_feishu_state(
            self._im_observation("im_chat_search_result_context_jump.png")
        )

        self.assertEqual(state["page_type"], "chat_search_panel")
        self.assertTrue(state["search_box_visible"])
        self.assertTrue(state["product_state"]["local_search_result_list_visible"])
        self.assertTrue(state["product_state"]["search_result_context_in_chat_visible"])
        self.assertEqual(state["product_state"]["search_query"], "ui")
        self.assertEqual(
            state["product_state"]["selected_conversation_search_result_text"],
            "ui我感觉gemini就可以",
        )
        self.assertIn(
            "ui如果改了会变吧",
            state["product_state"]["visible_conversation_search_results"],
        )

    def test_detects_shell_search_state_from_real_fixture(self) -> None:
        state = detect_feishu_state(
            self._shell_observation("global_search_results.png")
        )

        self.assertEqual(state["product"], "feishu")
        self.assertEqual(state["page_type"], "shell_search")
        self.assertFalse(state["message_input_visible"])
        self.assertFalse(state["send_button_visible"])
        self.assertTrue(state["search_box_visible"])
        self.assertTrue(state["product_state"]["search_result_list_visible"])
        self.assertIn("bot功能测试", state["product_state"]["visible_search_results"])
        self.assertIn("孙思超", state["product_state"]["visible_search_results"])


if __name__ == "__main__":
    unittest.main()
