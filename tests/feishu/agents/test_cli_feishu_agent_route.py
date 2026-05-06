import argparse
import unittest
from unittest.mock import Mock, patch

from gui_agents.s3 import cli_app


class TestCliFeishuAgentRoute(unittest.TestCase):
    def _args(self, execution_mode: str = "feishu_agent") -> argparse.Namespace:
        return argparse.Namespace(
            execution_mode=execution_mode,
            max_trajectory_length=8,
            enable_reflection=True,
        )

    def test_feishu_agent_runtime_builds_agent_s3_with_feishu_aci(self) -> None:
        fake_grounding = Mock(name="feishu_grounding")
        fake_runtime = Mock(name="agent_s3")

        with (
            patch.object(
                cli_app, "_get_feishu_primary_capture_size", return_value=(1920, 1080)
            ),
            patch.object(
                cli_app, "WindowsFeishuACI", return_value=fake_grounding
            ) as aci_cls,
            patch.object(cli_app, "AgentS3", return_value=fake_runtime) as agent_s3_cls,
        ):
            runtime, scaled_width, scaled_height, runtime_kind = (
                cli_app.build_execution_runtime(
                    self._args(),
                    engine_params={"engine_type": "test"},
                    engine_params_for_grounding={
                        "grounding_width": 1000,
                        "grounding_height": 1000,
                    },
                    platform_name="windows",
                )
            )

        self.assertIs(runtime, fake_runtime)
        self.assertEqual(runtime_kind, "agent_s3")
        self.assertEqual((scaled_width, scaled_height), (1000, 562))
        aci_cls.assert_called_once()
        agent_s3_cls.assert_called_once_with(
            {"engine_type": "test"},
            fake_grounding,
            platform="windows",
            max_trajectory_length=8,
            enable_reflection=True,
        )

    def test_classic_s3_runtime_still_builds_agent_s3_with_osworld_aci(self) -> None:
        fake_grounding = Mock(name="classic_grounding")
        fake_runtime = Mock(name="agent_s3")

        with (
            patch.object(cli_app.pyautogui, "size", return_value=(1600, 900)),
            patch.object(
                cli_app, "OSWorldACI", return_value=fake_grounding
            ) as osworld_cls,
            patch.object(cli_app, "AgentS3", return_value=fake_runtime) as agent_s3_cls,
        ):
            runtime, scaled_width, scaled_height, runtime_kind = (
                cli_app.build_execution_runtime(
                    self._args(execution_mode="classic_s3"),
                    engine_params={"engine_type": "test"},
                    engine_params_for_grounding={
                        "grounding_width": 1000,
                        "grounding_height": 1000,
                    },
                    platform_name="windows",
                )
            )

        self.assertIs(runtime, fake_runtime)
        self.assertEqual(runtime_kind, "agent_s3")
        self.assertEqual((scaled_width, scaled_height), (1000, 562))
        osworld_cls.assert_called_once()
        agent_s3_cls.assert_called_once()


if __name__ == "__main__":
    unittest.main()
