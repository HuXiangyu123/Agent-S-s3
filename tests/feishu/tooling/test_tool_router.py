from pathlib import Path
import unittest

from gui_agents.feishu.detectors.im_state_detector import detect_feishu_state
from gui_agents.feishu.tooling.tool_router import (
    build_feishu_tool_guidance,
    route_feishu_tools,
)


IM_FIXTURE_DIR = Path("tests/fixtures/im")
SHELL_FIXTURE_DIR = Path("tests/fixtures/feishu_shell")


class TestFeishuToolRouter(unittest.TestCase):
    def _im_observation(self, filename: str) -> dict:
        return {"image_path": str(IM_FIXTURE_DIR / filename)}

    def _shell_observation(self, filename: str) -> dict:
        return {"image_path": str(SHELL_FIXTURE_DIR / filename)}

    def test_chat_main_prefers_composer_tools(self) -> None:
        observation = self._im_observation("im_chat_main_full.png")
        state = detect_feishu_state(observation)

        recommendation = route_feishu_tools(
            '在 "bot功能测试" 发送 hello world',
            observation,
            state=state,
        )

        self.assertEqual(recommendation.page_type, "chat_main")
        self.assertEqual(recommendation.next_step_focus, "message_composer")
        self.assertIn("feishu_type_message", recommendation.preferred_tools)
        self.assertIn("feishu_click_message_input", recommendation.preferred_tools)
        self.assertIn("hotkey", recommendation.preferred_tools)
        self.assertIn("click", recommendation.enabled_tools)
        self.assertEqual(recommendation.target_chat_name, "bot功能测试")

    def test_shell_search_prefers_text_driven_search(self) -> None:
        observation = self._shell_observation("global_search_results.png")
        state = detect_feishu_state(observation)

        recommendation = route_feishu_tools(
            "打开消息中的bot功能测试群聊并搜索需求",
            observation,
            state=state,
        )

        self.assertEqual(recommendation.page_type, "shell_search")
        self.assertEqual(recommendation.next_step_focus, "global_search_entry")
        self.assertIn("feishu_type", recommendation.preferred_tools)
        self.assertIn("feishu_click", recommendation.preferred_tools)
        self.assertIn("click", recommendation.discouraged_tools)

    def test_search_panel_prefers_panel_local_actions(self) -> None:
        observation = self._im_observation("im_message_searchresult_visible.png")
        state = detect_feishu_state(observation)

        recommendation = route_feishu_tools(
            "搜索需求并打开对应消息结果",
            observation,
            state=state,
        )

        self.assertEqual(recommendation.page_type, "chat_search_panel")
        self.assertEqual(
            recommendation.next_step_focus, "conversation_search_entry_or_result"
        )
        self.assertIn("feishu_click", recommendation.preferred_tools)
        self.assertIn("feishu_type", recommendation.preferred_tools)
        self.assertIn("type", recommendation.discouraged_tools)

    def test_guidance_mentions_emoji_fallback_on_chat_main(self) -> None:
        observation = self._im_observation("im_message_draft_visible.png")
        recommendation = route_feishu_tools(
            "在当前群聊点击表情并发送一个随机表情",
            observation,
        )
        guidance = build_feishu_tool_guidance(
            "在当前群聊点击表情并发送一个随机表情",
            observation,
        )

        self.assertEqual(recommendation.next_step_focus, "emoji_icon_or_picker")
        self.assertEqual(recommendation.preferred_tools[1], "click")
        self.assertIn("feishu_click", recommendation.discouraged_tools)
        self.assertIn("Preferred tools:", guidance)
        self.assertIn("click", guidance)
        self.assertIn("recovery guidance", guidance)
        self.assertNotIn("source of truth", guidance)
        self.assertIn("agent.click(...)", guidance)

    def test_full_send_then_emoji_instruction_stays_on_message_composer_first(
        self,
    ) -> None:
        observation = self._im_observation("im_chat_main_full.png")
        recommendation = route_feishu_tools(
            "打开消息中的bot功能测试群聊，在消息发送框输入hello，并且点击右侧表情图标随机选择一个表情并发送",
            observation,
        )

        self.assertEqual(recommendation.page_type, "chat_main")
        self.assertEqual(recommendation.next_step_focus, "message_composer")
        self.assertIn("feishu_type_message", recommendation.preferred_tools)
        self.assertIn("feishu_click_message_input", recommendation.preferred_tools)
        self.assertIn("Do not go to emoji first", " ".join(recommendation.hints))


if __name__ == "__main__":
    unittest.main()
