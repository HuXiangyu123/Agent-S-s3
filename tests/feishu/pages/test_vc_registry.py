import unittest

from gui_agents.feishu.pages.registry import get_page_descriptor, get_page_ids


class TestVCPageRegistry(unittest.TestCase):
    def test_registry_exposes_vc_semantic_descriptors(self) -> None:
        for page_id in (
            "vc_home",
            "vc_start_preview",
            "vc_meeting_active",
            "vc_join_preview",
            "vc_invite_dialog",
        ):
            with self.subTest(page_id=page_id):
                self.assertIn(page_id, get_page_ids())
                descriptor = get_page_descriptor(page_id)
                self.assertIsNotNone(descriptor)
                self.assertEqual(descriptor["supported_workflows"], [])
                for region in descriptor["key_regions"].values():
                    self.assertNotIn("relative_bounds", region)
                    self.assertIn("role", region)


if __name__ == "__main__":
    unittest.main()
