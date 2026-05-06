from pathlib import Path
import unittest

from gui_agents.feishu.detectors.docs_state_detector import detect_docs_state


DOCS_FIXTURE_DIR = Path("tests/fixtures/docs")


class TestDocsStateDetector(unittest.TestCase):
    def _docs_observation(self, filename: str) -> dict:
        return {"image_path": str(DOCS_FIXTURE_DIR / filename)}

    def test_detects_docs_home_state(self) -> None:
        state = detect_docs_state(self._docs_observation("主页.png"))

        self.assertEqual(state["product"], "docs")
        self.assertEqual(state["page_type"], "docs_home")
        self.assertTrue(state["search_box_visible"])
        self.assertTrue(state["product_state"]["docs_home_visible"])
        self.assertTrue(state["product_state"]["new_card_visible"])
        self.assertTrue(state["product_state"]["document_list_visible"])

    def test_detects_docs_new_dropdown_state(self) -> None:
        state = detect_docs_state(self._docs_observation("新建.png"))

        self.assertEqual(state["product"], "docs")
        self.assertEqual(state["page_type"], "docs_new_dropdown")
        self.assertTrue(state["product_state"]["new_dropdown_visible"])
        self.assertTrue(state["product_state"]["document_option_visible"])
        self.assertFalse(state["search_box_visible"])

    def test_detects_docs_template_gallery_state(self) -> None:
        state = detect_docs_state(self._docs_observation("文档模板选择.png"))

        self.assertEqual(state["page_type"], "docs_template_gallery")
        self.assertTrue(state["search_box_visible"])
        self.assertTrue(state["product_state"]["template_gallery_visible"])
        self.assertTrue(state["product_state"]["blank_doc_card_visible"])

    def test_detects_docs_browser_editor_state(self) -> None:
        state = detect_docs_state(self._docs_observation("网页端文档.png"))

        self.assertEqual(state["page_type"], "docs_browser_editor")
        self.assertTrue(state["product_state"]["editor_ready"])
        self.assertTrue(state["product_state"]["title_input_visible"])
        self.assertTrue(state["product_state"]["body_editor_visible"])
        self.assertEqual(state["product_state"]["doc_title"], "未命名文档")

    def test_retains_share_dialog_as_non_primary_docs_state(self) -> None:
        state = detect_docs_state(self._docs_observation("网页端文档分享.png"))

        self.assertEqual(state["page_type"], "docs_share_dialog")
        self.assertNotIn("workflow_support", state["product_state"])
        self.assertTrue(state["product_state"]["share_dialog_visible"])


if __name__ == "__main__":
    unittest.main()
