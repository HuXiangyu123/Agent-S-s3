import unittest

from gui_agents.feishu.pages.registry import get_page_descriptor, get_page_ids


class TestDocsPageRegistry(unittest.TestCase):
    def test_registry_exposes_docs_home_descriptor(self) -> None:
        self.assertIn("docs_home", get_page_ids())
        descriptor = get_page_descriptor("docs_home")
        self.assertIsNotNone(descriptor)
        self.assertEqual(descriptor["page_type"], "docs_home")
        self.assertIn("new_card_area", descriptor["key_regions"])
        self.assertNotIn("supported_workflows", descriptor)
        self.assertNotIn("relative_bounds", str(descriptor["key_regions"]))

    def test_registry_exposes_docs_new_dropdown_descriptor(self) -> None:
        self.assertIn("docs_new_dropdown", get_page_ids())
        descriptor = get_page_descriptor("docs_new_dropdown")
        self.assertIsNotNone(descriptor)
        self.assertIn("document_option_area", descriptor["key_regions"])

    def test_registry_exposes_docs_template_gallery_descriptor(self) -> None:
        self.assertIn("docs_template_gallery", get_page_ids())
        descriptor = get_page_descriptor("docs_template_gallery")
        self.assertIsNotNone(descriptor)
        self.assertIn("blank_doc_card_area", descriptor["key_regions"])

    def test_registry_exposes_docs_browser_editor_descriptor(self) -> None:
        self.assertIn("docs_browser_editor", get_page_ids())
        descriptor = get_page_descriptor("docs_browser_editor")
        self.assertIsNotNone(descriptor)
        self.assertIn("title_input_area", descriptor["key_regions"])
        self.assertIn("body_editor_area", descriptor["key_regions"])


if __name__ == "__main__":
    unittest.main()
