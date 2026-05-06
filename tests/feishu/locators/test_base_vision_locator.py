from pathlib import Path
import unittest

from gui_agents.feishu.detectors.base_state_detector import detect_base_state
from gui_agents.feishu.locators.vision_locator import locate_target


BASE_FIXTURE_DIR = Path("tests/fixtures/base")


class TestBaseVisionLocator(unittest.TestCase):
    def _observation(self, filename: str) -> dict:
        return {"image_path": str(BASE_FIXTURE_DIR / filename)}

    def test_rejects_base_home_new_button_fixed_locator(self) -> None:
        observation = self._observation("多维表格主页-不带弹窗.png")
        state = detect_base_state(observation)

        result = locate_target("base_home_new_button", state, observation)

        self.assertFalse(result["matched"])
        self.assertEqual(result["page_id"], "base_home")
        self.assertEqual(result["failure_type"], "location")
        self.assertIn("do not expose fixed coordinates", result["failure_reason"])

    def test_rejects_base_new_table_option_fixed_locator(self) -> None:
        observation = self._observation("点击新建.png")
        state = detect_base_state(observation)

        result = locate_target("base_new_table_option", state, observation)

        self.assertFalse(result["matched"])
        self.assertEqual(result["page_id"], "base_new_menu")

    def test_rejects_base_blank_table_card_fixed_locator(self) -> None:
        observation = self._observation("点击新建后.png")
        state = detect_base_state(observation)

        result = locate_target("base_blank_table_card", state, observation)

        self.assertFalse(result["matched"])
        self.assertEqual(result["page_id"], "base_template_gallery")

    def test_rejects_base_grid_fixed_locator(self) -> None:
        observation = self._observation("新建多维表格后浏览器界面-带弹窗.png")
        state = detect_base_state(observation)

        result = locate_target("base_grid", state, observation)

        self.assertFalse(result["matched"])
        self.assertEqual(result["page_id"], "base_browser_table")

    def test_base_locator_failure_is_consistent_across_surfaces(self) -> None:
        observation = self._observation("点击新建后.png")
        state = detect_base_state(observation)

        result = locate_target("base_home_new_button", state, observation)

        self.assertFalse(result["matched"])
        self.assertEqual(result["failure_type"], "location")
        self.assertIn("grounded browser actions", result["failure_reason"])


if __name__ == "__main__":
    unittest.main()
