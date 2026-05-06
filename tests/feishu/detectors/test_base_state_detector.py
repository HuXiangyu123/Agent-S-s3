from pathlib import Path
import unittest

from gui_agents.feishu.detectors.base_state_detector import detect_base_state


BASE_FIXTURE_DIR = Path("tests/fixtures/base")


class TestBaseStateDetector(unittest.TestCase):
    def _base_observation(self, filename: str) -> dict:
        return {"image_path": str(BASE_FIXTURE_DIR / filename)}

    def test_detects_base_home_state(self) -> None:
        state = detect_base_state(self._base_observation("多维表格主页-不带弹窗.png"))

        self.assertEqual(state["product"], "base")
        self.assertEqual(state["page_type"], "base_home")
        self.assertTrue(state["search_box_visible"])
        self.assertTrue(state["product_state"]["base_home_visible"])
        self.assertTrue(state["product_state"]["new_button_visible"])
        self.assertNotIn("workflow_support", state["product_state"])

    def test_detects_base_new_menu_state(self) -> None:
        state = detect_base_state(self._base_observation("点击新建.png"))

        self.assertEqual(state["page_type"], "base_new_menu")
        self.assertEqual(state["modal_type"], "base_new_menu")
        self.assertTrue(state["product_state"]["new_base_table_option_visible"])

    def test_detects_base_template_gallery_state(self) -> None:
        state = detect_base_state(self._base_observation("点击新建后.png"))

        self.assertEqual(state["page_type"], "base_template_gallery")
        self.assertTrue(state["search_box_visible"])
        self.assertTrue(state["product_state"]["blank_base_table_card_visible"])

    def test_detects_base_browser_table_state(self) -> None:
        state = detect_base_state(
            self._base_observation("新建多维表格后浏览器界面-带弹窗.png")
        )

        self.assertEqual(state["page_type"], "base_browser_table")
        self.assertEqual(state["modal_type"], "base_ai_upgrade_popup")
        self.assertTrue(state["product_state"]["base_editor_ready"])
        self.assertTrue(state["product_state"]["grid_visible"])

    def test_all_base_png_fixtures_have_metadata_and_detect_product(self) -> None:
        for image_path in BASE_FIXTURE_DIR.glob("*.png"):
            with self.subTest(image=image_path.name):
                metadata_path = image_path.with_suffix(".json")
                self.assertTrue(metadata_path.exists())
                state = detect_base_state({"image_path": str(image_path)})
                self.assertEqual(state["product"], "base")
                self.assertNotEqual(state["page_type"], "unknown")

    def test_base_fixture_metadata_is_semantic_only(self) -> None:
        forbidden_markers = (
            "relative_bounds",
            "supported_workflows",
            "workflow_support",
            "bbox",
            "confidence",
            "score",
            "image_width",
            "image_height",
        )
        for metadata_path in BASE_FIXTURE_DIR.glob("*.json"):
            with self.subTest(metadata=metadata_path.name):
                text = metadata_path.read_text(encoding="utf-8")
                for marker in forbidden_markers:
                    self.assertNotIn(marker, text)


if __name__ == "__main__":
    unittest.main()
