import unittest

from gui_agents.s3.agents.grounding_feishu import WindowsFeishuACI


class TestFeishuRuntimePriorTools(unittest.TestCase):
    def setUp(self) -> None:
        self.aci = object.__new__(WindowsFeishuACI)
        self.aci.width = 1920
        self.aci.height = 1080
        self.aci.virtual_screen_left = 0
        self.aci.virtual_screen_top = 0
        self.trace_messages: list[str] = []
        self.aci._trace_execution = self.trace_messages.append

    def test_click_message_input_uses_known_region(self) -> None:
        code = self.aci.feishu_click_message_input()

        self.assertIn("pyautogui.click", code)
        self.assertIn("im_chat_main", "".join(self.trace_messages))
        self.assertIn("message_input_area", "".join(self.trace_messages))

    def test_type_message_uses_prior_region_then_paste(self) -> None:
        code = self.aci.feishu_type_message("hello", overwrite=False, enter=False)

        self.assertIn("pyautogui.click", code)
        self.assertIn("pyperclip.copy('hello')", code)
        self.assertIn("pyautogui.hotkey('ctrl', 'v')", code)

    def test_click_send_button_uses_known_region(self) -> None:
        code = self.aci.feishu_click_send_button()

        self.assertIn("pyautogui.click", code)
        self.assertIn("send_button_area", "".join(self.trace_messages))

    def test_feishu_click_prepares_grounded_fallback_for_icon_description(self) -> None:
        self.aci.obs = {"screenshot": b"fake"}
        self.aci.generate_coords = lambda description, obs: [500, 600]
        self.aci.resize_coordinates = lambda coords: [960, 540]

        code = self.aci.feishu_click(
            "The smiley face emoji icon to the right of the message input box"
        )

        self.assertIn("FEISHU_UIA_CLICK_FALLBACK", code)
        self.assertIn("FEISHU_CLICK_COORDS:", code)
        self.assertIn(
            "FEISHU_CLICK_GROUNDED_FALLBACK_READY",
            "".join(self.trace_messages),
        )

    def test_feishu_click_keeps_plain_text_targets_uia_only(self) -> None:
        self.aci.obs = {"screenshot": b"fake"}
        self.aci.generate_coords = lambda description, obs: [500, 600]
        self.aci.resize_coordinates = lambda coords: [960, 540]

        code = self.aci.feishu_click("bot功能测试")

        self.assertNotIn("FEISHU_UIA_CLICK_FALLBACK", code)
        self.assertNotIn("FEISHU_CLICK_COORDS:", code)

    def test_worker_im_prompt_adds_static_prior_tool_strategy(self) -> None:
        prompt = self.aci.build_worker_system_prompt(
            "打开消息中的bot功能测试群聊，在消息发送框输入hello，并发送",
            "windows",
        )

        self.assertIn("First reason from the screenshot", prompt)
        self.assertIn("agent.feishu_type_message(...)", prompt)
        self.assertIn("icon-only controls", prompt)


if __name__ == "__main__":
    unittest.main()
