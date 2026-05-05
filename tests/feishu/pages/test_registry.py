import unittest

from gui_agents.feishu.pages.registry import get_page_descriptor, get_page_ids


class TestPageRegistry(unittest.TestCase):
    def test_registry_exposes_im_chat_search_panel_descriptor(self) -> None:
        page_ids = get_page_ids()
        self.assertIn("im_chat_search_panel", page_ids)

        descriptor = get_page_descriptor("im_chat_search_panel")
        self.assertIsNotNone(descriptor)
        self.assertEqual(descriptor["page_type"], "chat_search_panel")
        self.assertIn("conversation_search_entry_area", descriptor["key_regions"])
        self.assertIn("search_panel_area", descriptor["key_regions"])

    def test_registry_exposes_shell_search_descriptor(self) -> None:
        page_ids = get_page_ids()
        self.assertIn("feishu_shell_search", page_ids)

        descriptor = get_page_descriptor("feishu_shell_search")
        self.assertIsNotNone(descriptor)
        self.assertEqual(descriptor["page_type"], "shell_search")
        self.assertIn("open_chat", descriptor["supported_workflows"])
        self.assertIn("global_search_entry_area", descriptor["key_regions"])
        self.assertIn("search_result_item_area", descriptor["key_regions"])

    def test_registry_exposes_im_chat_main_descriptor(self) -> None:
        page_ids = get_page_ids()
        self.assertIn("im_chat_main", page_ids)

        descriptor = get_page_descriptor("im_chat_main")
        self.assertIsNotNone(descriptor)
        self.assertEqual(descriptor["page_type"], "chat_main")
        self.assertIn("send_message", descriptor["supported_workflows"])
        self.assertIn("message_input_area", descriptor["key_regions"])
        self.assertIn("send_button_area", descriptor["key_regions"])


if __name__ == "__main__":
    unittest.main()
