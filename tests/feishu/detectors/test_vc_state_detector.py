from pathlib import Path
import unittest

from gui_agents.feishu.detectors.vc_state_detector import detect_vc_state


VC_FIXTURE_DIR = Path("tests/fixtures/vc")


class TestVCStateDetector(unittest.TestCase):
    def _vc_observation(self, filename: str) -> dict:
        return {"image_path": str(VC_FIXTURE_DIR / filename)}

    def test_detects_vc_home_state(self) -> None:
        state = detect_vc_state(self._vc_observation("会议主页面.png"))

        self.assertEqual(state["product"], "vc")
        self.assertEqual(state["page_type"], "vc_home")
        self.assertTrue(state["product_state"]["start_card_visible"])
        self.assertTrue(state["product_state"]["join_card_visible"])

    def test_detects_start_preview_state(self) -> None:
        state = detect_vc_state(self._vc_observation("发起会议.png"))

        self.assertEqual(state["page_type"], "vc_start_preview")
        self.assertEqual(state["modal_type"], "vc_start_preview")
        self.assertTrue(state["product_state"]["start_button_visible"])

    def test_detects_active_meeting_state(self) -> None:
        state = detect_vc_state(self._vc_observation("正在会议的页面.png"))

        self.assertEqual(state["page_type"], "vc_meeting_active")
        self.assertTrue(state["product_state"]["meeting_active"])
        self.assertTrue(state["product_state"]["invite_button_visible"])

    def test_detects_join_preview_state(self) -> None:
        state = detect_vc_state(self._vc_observation("选择加入会议.png"))

        self.assertEqual(state["page_type"], "vc_join_preview")
        self.assertTrue(state["product_state"]["meeting_id_input_visible"])
        self.assertFalse(state["product_state"]["join_button_enabled"])

    def test_detects_invite_dialog_state(self) -> None:
        state = detect_vc_state(self._vc_observation("会议邀请点击后.png"))

        self.assertEqual(state["page_type"], "vc_invite_dialog")
        self.assertEqual(state["modal_type"], "vc_invite_dialog")
        self.assertTrue(state["product_state"]["invite_dialog_visible"])

    def test_detects_invite_popover_state(self) -> None:
        state = detect_vc_state(self._vc_observation("会议进行邀请.png"))

        self.assertEqual(state["page_type"], "vc_meeting_active")
        self.assertEqual(state["modal_type"], "vc_invite_popover")
        self.assertTrue(state["product_state"]["invite_popover_visible"])

    def test_fallback_detects_invite_popover_from_ocr(self) -> None:
        state = detect_vc_state({"ocr_text": "会议信息\n布局\n邀请\n复制邀请链接"})

        self.assertEqual(state["product"], "vc")
        self.assertEqual(state["page_type"], "vc_meeting_active")
        self.assertEqual(state["modal_type"], "vc_invite_popover")
        self.assertTrue(state["product_state"]["invite_entry_visible"])

    def test_vc_fixture_metadata_is_semantic_only(self) -> None:
        forbidden_markers = (
            "relative_bounds",
            "bbox",
            "confidence",
            "score",
            "image_width",
            "image_height",
        )
        for metadata_path in VC_FIXTURE_DIR.glob("*.json"):
            with self.subTest(metadata=metadata_path.name):
                text = metadata_path.read_text(encoding="utf-8")
                for marker in forbidden_markers:
                    self.assertNotIn(marker, text)


if __name__ == "__main__":
    unittest.main()
