import unittest

from gui_agents.feishu.pages.registry import get_page_descriptor, get_page_ids


class TestBasePageRegistry(unittest.TestCase):
    def test_registry_exposes_base_home_descriptor(self) -> None:
        self.assertIn("base_home", get_page_ids())
        descriptor = get_page_descriptor("base_home")
        self.assertIsNotNone(descriptor)
        self.assertIn("base_home_new_button_area", descriptor["key_regions"])
        self.assertNotIn("supported_workflows", descriptor)
        self.assertNotIn(
            "relative_bounds",
            descriptor["key_regions"]["base_home_new_button_area"],
        )

    def test_registry_exposes_base_new_menu_descriptor(self) -> None:
        self.assertIn("base_new_menu", get_page_ids())
        descriptor = get_page_descriptor("base_new_menu")
        self.assertIsNotNone(descriptor)
        self.assertIn("base_new_table_option_area", descriptor["key_regions"])
        self.assertIn(
            "description",
            descriptor["key_regions"]["base_new_table_option_area"],
        )

    def test_registry_exposes_base_template_gallery_descriptor(self) -> None:
        self.assertIn("base_template_gallery", get_page_ids())
        descriptor = get_page_descriptor("base_template_gallery")
        self.assertIsNotNone(descriptor)
        self.assertIn("base_blank_table_card_area", descriptor["key_regions"])
        self.assertNotIn("supported_workflows", descriptor)

    def test_registry_exposes_base_browser_table_descriptor(self) -> None:
        self.assertIn("base_browser_table", get_page_ids())
        descriptor = get_page_descriptor("base_browser_table")
        self.assertIsNotNone(descriptor)
        self.assertIn("base_grid_area", descriptor["key_regions"])
        self.assertIn("base_share_button_area", descriptor["key_regions"])
        self.assertNotIn("relative_bounds", descriptor["key_regions"]["base_grid_area"])

    def test_registry_exposes_deferred_secondary_descriptors(self) -> None:
        for page_id in (
            "base_share_panel",
            "base_dashboard",
            "base_automation",
            "base_app_market",
        ):
            with self.subTest(page_id=page_id):
                descriptor = get_page_descriptor(page_id)
                self.assertIsNotNone(descriptor)
                self.assertNotIn("supported_workflows", descriptor)


if __name__ == "__main__":
    unittest.main()
