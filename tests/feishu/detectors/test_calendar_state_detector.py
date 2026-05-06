from pathlib import Path
import unittest

from gui_agents.feishu.detectors.calendar_state_detector import detect_calendar_state


CALENDAR_FIXTURE_DIR = Path("tests/fixtures/calendar")


class TestCalendarStateDetector(unittest.TestCase):
    def _calendar_observation(self, filename: str) -> dict:
        return {"image_path": str(CALENDAR_FIXTURE_DIR / filename)}

    def test_detects_calendar_home_state(self) -> None:
        state = detect_calendar_state(self._calendar_observation("日历主页.png"))

        self.assertEqual(state["product"], "calendar")
        self.assertEqual(state["page_type"], "calendar_home")
        self.assertTrue(state["product_state"]["calendar_home_visible"])
        self.assertTrue(state["product_state"]["create_event_button_visible"])

    def test_detects_calendar_event_modal_state(self) -> None:
        state = detect_calendar_state(self._calendar_observation("点击创建日程后.png"))

        self.assertEqual(state["product"], "calendar")
        self.assertEqual(state["page_type"], "calendar_event_modal")
        self.assertEqual(state["modal_type"], "create_event")
        self.assertTrue(state["product_state"]["event_modal_visible"])
        self.assertTrue(state["product_state"]["title_input_visible"])
        self.assertTrue(state["product_state"]["save_button_visible"])


if __name__ == "__main__":
    unittest.main()
