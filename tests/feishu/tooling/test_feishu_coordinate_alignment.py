import unittest
from unittest.mock import patch

from PIL import Image

from gui_agents.s3.agents.grounding_feishu import WindowsFeishuACI
from gui_agents.s3.cli_app import _get_feishu_primary_capture_size


class TestFeishuCoordinateAlignment(unittest.TestCase):
    def test_resize_coordinates_stays_in_primary_screen_space(self) -> None:
        aci = object.__new__(WindowsFeishuACI)
        aci.width = 1920
        aci.height = 1080
        aci.engine_params_for_grounding = {"ground_coord_scale": 1000}

        coords = aci.resize_coordinates([523, 957])

        self.assertEqual(coords, [1004, 1034])

    def test_semantic_prior_tools_do_not_use_static_relative_bounds(self) -> None:
        aci = object.__new__(WindowsFeishuACI)
        aci.click = lambda description="", *a, **kw: f"agent.click({description!r})"

        code = aci.feishu_click_message_input()

        self.assertIn("agent.click(", code)
        self.assertIn("composer input", code)
        self.assertNotIn("relative_bounds", code)
        self.assertNotIn("page_descriptor", code)

    def test_capture_observation_uses_primary_screen_grab(self) -> None:
        aci = object.__new__(WindowsFeishuACI)
        trace_messages: list[str] = []
        aci._trace_execution = trace_messages.append

        with patch(
            "gui_agents.s3.agents.grounding_feishu.ImageGrab.grab",
            return_value=Image.new("RGB", (1920, 1080), "black"),
        ) as grab_mock:
            obs = aci.capture_observation(1000, 1000)

        grab_mock.assert_called_once_with()
        self.assertEqual(obs["source_image_width"], 1920)
        self.assertEqual(obs["source_image_height"], 1080)
        self.assertEqual(obs["image_width"], 1000)
        self.assertEqual(obs["image_height"], 1000)
        self.assertIn("primary_screen", "".join(trace_messages))

    def test_cli_primary_capture_size_uses_same_capture_path(self) -> None:
        with patch(
            "gui_agents.s3.cli_app.ImageGrab.grab",
            return_value=Image.new("RGB", (1920, 1080), "black"),
        ) as grab_mock:
            width, height = _get_feishu_primary_capture_size()

        grab_mock.assert_called_once_with()
        self.assertEqual((width, height), (1920, 1080))


if __name__ == "__main__":
    unittest.main()
