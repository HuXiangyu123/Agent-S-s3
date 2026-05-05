import unittest

from gui_agents.feishu.detectors.im_state_detector import detect_feishu_state


class TestIMStateDetectorRuntimeOCR(unittest.TestCase):
    def test_detects_chat_main_from_runtime_ocr_text(self) -> None:
        state = detect_feishu_state(
            {"ocr_text": "消息\n发送给 bot功能测试\n发送\n表情"}
        )

        self.assertEqual(state["page_type"], "chat_main")
        self.assertEqual(state["product"], "im")
        self.assertEqual(state["chat_name"], "bot功能测试")
        self.assertTrue(state["message_input_visible"])
        self.assertTrue(state["send_button_visible"])

    def test_detects_chat_search_panel_from_runtime_ocr_text(self) -> None:
        state = detect_feishu_state(
            {"ocr_text": "搜索会话内容\n来自用户\n时间\n高级搜索"}
        )

        self.assertEqual(state["page_type"], "chat_search_panel")
        self.assertEqual(state["product"], "im")
        self.assertTrue(state["search_box_visible"])
        self.assertTrue(state["product_state"]["local_search_panel_visible"])
        self.assertTrue(state["product_state"]["local_search_filters_visible"])


if __name__ == "__main__":
    unittest.main()
