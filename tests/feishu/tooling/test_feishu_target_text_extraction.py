import unittest

from gui_agents.s3.agents.grounding_feishu import WindowsFeishuACI


class TestFeishuTargetTextExtraction(unittest.TestCase):
    def setUp(self) -> None:
        # The helper methods under test do not depend on full ACI initialization.
        self.aci = object.__new__(WindowsFeishuACI)

    def test_preserves_explicit_short_visible_text(self) -> None:
        text = self.aci._extract_feishu_target_text("发送给 bot功能测试")
        self.assertEqual(text, "发送给 bot功能测试")

    def test_does_not_collapse_long_contextual_emoji_description(self) -> None:
        description = (
            "The smiley face emoji icon to the right of the message input box "
            "at the bottom of the bot功能测试 chat window"
        )
        text = self.aci._extract_feishu_target_text(description)
        self.assertEqual(text, description)

    def test_does_not_extract_reference_label_from_context_sentence(self) -> None:
        description = (
            "The circular smiley face emoji button immediately to the right "
            "of the 'Aa' text format button at the bottom right"
        )
        text = self.aci._extract_feishu_target_text(description)
        self.assertEqual(text, description)

    def test_extracts_quoted_text_only_when_input_is_effectively_just_that_label(
        self,
    ) -> None:
        text = self.aci._extract_feishu_target_text('"确定"')
        self.assertEqual(text, "确定")


if __name__ == "__main__":
    unittest.main()
