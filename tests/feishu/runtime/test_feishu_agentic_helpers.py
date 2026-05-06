import unittest

from gui_agents.s3.agents.grounding_feishu import WindowsFeishuACI


class TestFeishuAgenticHelpers(unittest.TestCase):
    def _agent_stub(self) -> WindowsFeishuACI:
        return object.__new__(WindowsFeishuACI)

    def test_im_message_input_helper_returns_direct_click_code(self) -> None:
        agent = self._agent_stub()
        agent.click = lambda description, num_clicks=1, button_type="left", hold_keys=[]: (  # noqa: B006
            f"CLICK::{description}::{num_clicks}::{button_type}"
        )

        result = WindowsFeishuACI.feishu_click_message_input(agent)

        self.assertIn("Feishu IM message composer input", result)
        self.assertNotIn("agent.click", result)

    def test_vc_start_card_helper_uses_exact_start_label(self) -> None:
        agent = self._agent_stub()
        seen: list[str] = []

        def _fake_feishu_click(
            description: str,
            num_clicks: int = 1,
            button_type: str = "left",
        ) -> str:
            seen.append(description)
            return "VC_START_CARD_CODE"

        agent.feishu_click = _fake_feishu_click

        result = WindowsFeishuACI.feishu_vc_click_start_card(agent)

        self.assertEqual(result, "VC_START_CARD_CODE")
        self.assertEqual(seen, ["发起会议"])

    def test_vc_meeting_id_helper_targets_visible_input(self) -> None:
        agent = self._agent_stub()
        seen: list[tuple[str, str | None, bool, bool]] = []

        def _fake_feishu_type(
            text: str,
            element_description: str | None = None,
            overwrite: bool = False,
            enter: bool = False,
        ) -> str:
            seen.append((text, element_description, overwrite, enter))
            return "VC_TYPE_CODE"

        agent.feishu_type = _fake_feishu_type

        result = WindowsFeishuACI.feishu_vc_type_meeting_id(agent, "123456789")

        self.assertEqual(result, "VC_TYPE_CODE")
        self.assertEqual(seen, [("123456789", "会议 ID", True, False)])

    def test_vc_invite_button_helper_uses_grounded_toolbar_description(self) -> None:
        agent = self._agent_stub()
        seen: list[str] = []

        def _fake_click(
            description: str,
            num_clicks: int = 1,
            button_type: str = "left",
            hold_keys=[],
        ) -> str:  # noqa: B006
            seen.append(description)
            return "VC_INVITE_BUTTON_CODE"

        agent.click = _fake_click

        result = WindowsFeishuACI.feishu_vc_click_invite_button(agent)

        self.assertEqual(result, "VC_INVITE_BUTTON_CODE")
        self.assertIn("invite or participants control", seen[0])


if __name__ == "__main__":
    unittest.main()
