import unittest

from gui_agents.feishu.testcases.nl_parser import parse_instruction


class TestNLParser(unittest.TestCase):
    def test_parse_send_message_instruction(self) -> None:
        testcase = parse_instruction('在"测试群"发送"Hello World"并验证发送成功')

        self.assertEqual(testcase["product"], "im")
        self.assertEqual(testcase["steps"][0]["action"], "open_chat")
        self.assertEqual(testcase["steps"][0]["target"], "测试群")
        self.assertEqual(
            testcase["steps"][1]["payload"],
            {"text": "Hello World"},
        )
        self.assertEqual(testcase["steps"][2]["action"], "send_message")
        self.assertIn("message_sent", testcase["assertions"])

    def test_parse_launcher_style_open_chat_and_input_instruction(self) -> None:
        testcase = parse_instruction(
            "打开bot功能测试群聊，在消息发送框输入hello，并且发送"
        )

        self.assertEqual(testcase["steps"][0]["target"], "bot功能测试")
        self.assertEqual(testcase["steps"][1]["payload"], {"text": "hello"})

    def test_rejects_unsupported_emoji_instruction(self) -> None:
        with self.assertRaisesRegex(ValueError, "supports text send_message only"):
            parse_instruction(
                "打开消息中的bot功能测试群聊，在消息发送框输入hello，并且点击表情图标随机选择一个表情并发送"
            )

    def test_rejects_instruction_without_clear_chat_or_message(self) -> None:
        with self.assertRaisesRegex(ValueError, "unable to extract chat_name"):
            parse_instruction("帮我处理一下飞书消息")

    def test_parse_empty_instruction_raises_value_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "instruction cannot be empty"):
            parse_instruction("   ")


if __name__ == "__main__":
    unittest.main()
