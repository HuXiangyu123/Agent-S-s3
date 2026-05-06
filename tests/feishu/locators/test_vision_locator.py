from pathlib import Path
import unittest

from gui_agents.feishu.detectors.im_state_detector import detect_feishu_state
from gui_agents.feishu.locators.vision_locator import locate_target
from gui_agents.feishu.pages.registry import get_page_descriptor


IM_FIXTURE_DIR = Path("tests/fixtures/im")
SHELL_FIXTURE_DIR = Path("tests/fixtures/feishu_shell")


class TestVisionLocator(unittest.TestCase):
    def _im_observation(self, filename: str) -> dict:
        return {"image_path": str(IM_FIXTURE_DIR / filename)}

    def _shell_observation(self, filename: str) -> dict:
        return {"image_path": str(SHELL_FIXTURE_DIR / filename)}

    def _with_runtime_regions(self, observation: dict) -> dict:
        updated = dict(observation)
        updated["runtime_regions"] = {
            "message_input_area": {"bounds": [160, 900, 995, 985]},
            "send_button_area": {"bounds": [950, 900, 995, 985]},
            "active_chat_list_item_area": {"bounds": [34, 112, 205, 175]},
            "conversation_search_entry_area": {"bounds": [100, 230, 900, 280]},
            "conversation_search_close_button_area": {"bounds": [860, 120, 940, 200]},
            "conversation_search_result_item_area": {"bounds": [100, 370, 900, 450]},
            "global_search_entry_area": {"bounds": [20, 20, 960, 80]},
            "search_result_item_area": {"bounds": [10, 190, 280, 340]},
        }
        updated["runtime_named_regions"] = {
            "conversation_list_items": {
                "bot功能测试": {"bounds": [34, 112, 205, 175]},
            },
            "conversation_search_result_items": {
                "…实现了然后还要实现哪些需求": {"bounds": [100, 370, 900, 450]},
                "ui如果改了会变吧": {"bounds": [100, 420, 900, 500]},
            },
            "search_result_items": {
                "孙思超": {"bounds": [10, 190, 280, 340]},
            },
        }
        return updated

    def test_locates_message_input_from_full_fixture(self) -> None:
        observation = self._with_runtime_regions(
            self._im_observation("im_chat_main_full.png")
        )
        state = detect_feishu_state(observation)

        result = locate_target(
            "message_input",
            state,
            observation,
            page_context={"page_descriptor": get_page_descriptor("im_chat_main")},
        )

        self.assertTrue(result["matched"])
        self.assertEqual(result["page_id"], "im_chat_main")
        self.assertEqual(result["strategy"], "runtime_region")
        self.assertEqual(result["action_target"]["kind"], "point")
        self.assertNotIn("bbox", result)
        self.assertNotIn("confidence", result)

    def test_locates_send_button_from_full_fixture(self) -> None:
        observation = self._with_runtime_regions(
            self._im_observation("im_chat_main_full.png")
        )
        state = detect_feishu_state(observation)

        result = locate_target("send_button", state, observation)

        self.assertTrue(result["matched"])
        self.assertEqual(result["page_id"], "im_chat_main")
        self.assertEqual(result["action_target"]["kind"], "point")

    def test_locates_conversation_list_item_from_full_fixture(self) -> None:
        observation = self._with_runtime_regions(
            self._im_observation("im_chat_main_full.png")
        )
        state = detect_feishu_state(observation)

        result = locate_target(
            "conversation_list_item",
            state,
            observation,
            page_context={"target_text": "bot功能测试"},
        )

        self.assertTrue(result["matched"])
        self.assertEqual(result["page_id"], "im_chat_main")
        self.assertEqual(result["action_target"]["kind"], "point")

    def test_locates_conversation_search_entry_from_in_chat_search_panel(self) -> None:
        observation = self._with_runtime_regions(
            self._im_observation("im_message_searchchat_visible.png")
        )
        state = detect_feishu_state(observation)

        result = locate_target("conversation_search_entry", state, observation)

        self.assertTrue(result["matched"])
        self.assertEqual(result["page_id"], "im_chat_search_panel")
        self.assertEqual(result["action_target"]["kind"], "point")

    def test_locates_conversation_search_close_button(self) -> None:
        observation = self._with_runtime_regions(
            self._im_observation("im_message_searchchat_visible.png")
        )
        state = detect_feishu_state(observation)

        result = locate_target("conversation_search_close_button", state, observation)

        self.assertTrue(result["matched"])
        self.assertEqual(result["page_id"], "im_chat_search_panel")
        self.assertEqual(result["action_target"]["kind"], "point")

    def test_conversation_search_result_item_fails_on_empty_state(self) -> None:
        observation = self._im_observation("im_message_searchchat_visible.png")
        state = detect_feishu_state(observation)

        result = locate_target(
            "conversation_search_result_item",
            state,
            observation,
            page_context={"target_text": "…实现了然后还要实现哪些需求"},
        )

        self.assertFalse(result["matched"])
        self.assertEqual(result["failure_type"], "location")
        self.assertIn("result list not visible", result["failure_reason"])

    def test_locates_real_conversation_search_result_item(self) -> None:
        observation = self._with_runtime_regions(
            self._im_observation("im_message_searchresult_visible.png")
        )
        state = detect_feishu_state(observation)

        result = locate_target(
            "conversation_search_result_item",
            state,
            observation,
            page_context={"target_text": "…实现了然后还要实现哪些需求"},
        )

        self.assertTrue(result["matched"])
        self.assertEqual(result["page_id"], "im_chat_search_panel")
        self.assertEqual(result["action_target"]["kind"], "point")

    def test_locates_conversation_search_result_item_from_context_jump_state(
        self,
    ) -> None:
        observation = self._with_runtime_regions(
            self._im_observation("im_chat_search_result_context_jump.png")
        )
        state = detect_feishu_state(observation)

        result = locate_target(
            "conversation_search_result_item",
            state,
            observation,
            page_context={"target_text": "ui如果改了会变吧"},
        )

        self.assertTrue(result["matched"])
        self.assertEqual(result["page_id"], "im_chat_search_panel")
        self.assertEqual(result["action_target"]["kind"], "point")

    def test_global_search_entry_returns_visibility_failure_on_im_page(self) -> None:
        observation = self._im_observation("im_chat_main_full.png")
        state = detect_feishu_state(observation)

        result = locate_target("global_search_entry", state, observation)

        self.assertFalse(result["matched"])
        self.assertEqual(result["failure_type"], "location")
        self.assertIn("unsupported on current page", result["failure_reason"])

    def test_locates_global_search_entry_from_shell_fixture(self) -> None:
        observation = self._with_runtime_regions(
            self._shell_observation("global_search_results.png")
        )
        state = detect_feishu_state(observation)

        result = locate_target("global_search_entry", state, observation)

        self.assertTrue(result["matched"])
        self.assertEqual(result["page_id"], "feishu_shell_search")
        self.assertEqual(result["action_target"]["kind"], "point")

    def test_locates_search_result_item_from_shell_fixture(self) -> None:
        observation = self._with_runtime_regions(
            self._shell_observation("global_search_results.png")
        )
        state = detect_feishu_state(observation)

        result = locate_target(
            "search_result_item",
            state,
            observation,
            page_context={"target_text": "孙思超"},
        )

        self.assertTrue(result["matched"])
        self.assertEqual(result["page_id"], "feishu_shell_search")
        self.assertEqual(result["action_target"]["kind"], "point")

    def test_legacy_alias_targets_still_resolve_safely(self) -> None:
        observation = self._with_runtime_regions(
            self._shell_observation("global_search_results.png")
        )
        state = detect_feishu_state(observation)

        result = locate_target("chat_search_box", state, observation)

        self.assertTrue(result["matched"])
        self.assertEqual(result["page_id"], "feishu_shell_search")

    def test_fixture_relative_bounds_are_not_used_as_locator_source(self) -> None:
        observation = self._im_observation("im_chat_main_full.png")
        state = detect_feishu_state(observation)

        result = locate_target("message_input", state, observation)

        self.assertFalse(result["matched"])
        self.assertIn("runtime region unavailable", result["failure_reason"])

    def test_message_input_returns_unsupported_failure_on_in_chat_search_panel(
        self,
    ) -> None:
        observation = self._im_observation("im_message_searchchat_visible.png")
        state = detect_feishu_state(observation)

        result = locate_target("message_input", state, observation)

        self.assertFalse(result["matched"])
        self.assertEqual(result["failure_type"], "location")
        self.assertIn("unsupported on current page", result["failure_reason"])

    def test_returns_structured_failure_for_non_matching_conversation_item(
        self,
    ) -> None:
        observation = self._im_observation("im_chat_main_full.png")
        state = detect_feishu_state(observation)

        result = locate_target(
            "conversation_list_item",
            state,
            observation,
            page_context={"target_text": "不存在的会话"},
        )

        self.assertFalse(result["matched"])
        self.assertEqual(result["failure_type"], "location")
        self.assertIn("conversation item not visible", result["failure_reason"])

    def test_returns_structured_failure_for_non_matching_search_result(self) -> None:
        observation = self._shell_observation("global_search_results.png")
        state = detect_feishu_state(observation)

        result = locate_target(
            "search_result_item",
            state,
            observation,
            page_context={"target_text": "不存在的搜索结果"},
        )

        self.assertFalse(result["matched"])
        self.assertEqual(result["failure_type"], "location")
        self.assertIn("search result not visible", result["failure_reason"])

    def test_returns_structured_failure_for_non_matching_conversation_search_result(
        self,
    ) -> None:
        observation = self._im_observation("im_message_searchresult_visible.png")
        state = detect_feishu_state(observation)

        result = locate_target(
            "conversation_search_result_item",
            state,
            observation,
            page_context={"target_text": "不存在的搜索结果"},
        )

        self.assertFalse(result["matched"])
        self.assertEqual(result["failure_type"], "location")
        self.assertIn(
            "conversation search result not visible",
            result["failure_reason"],
        )

    def test_returns_recognition_failure_without_page_context(self) -> None:
        state = detect_feishu_state({"ocr_text": ""})
        result = locate_target("message_input", state, {"ocr_text": ""})

        self.assertFalse(result["matched"])
        self.assertEqual(result["failure_type"], "recognition")


if __name__ == "__main__":
    unittest.main()
