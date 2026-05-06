import unittest

from gui_agents.s3.agents._feishu_exec import (
    build_feishu_doc_click_code,
    build_feishu_doc_type_code,
    build_feishu_uia_click_code,
    build_win32_click_code,
    build_windows_open_code,
)


class TestFeishuExecBuilders(unittest.TestCase):
    def test_win32_click_code_has_bounds_guard_and_button_flags(self) -> None:
        code = build_win32_click_code(100, 200, num_clicks=2, button_type="right")

        self.assertIn("FEISHU_CLICK_SKIPPED_OUT_OF_BOUNDS", code)
        self.assertIn("FEISHU_CLICK_COORDS:", code)
        self.assertIn("mouse_event(0x0008", code)
        self.assertIn("mouse_event(0x0010", code)

    def test_uia_click_code_embeds_optional_fallback(self) -> None:
        code = build_feishu_uia_click_code(
            "bot功能测试",
            fallback_code="print('fallback-path')",
        )

        self.assertIn("FEISHU_UIA_CLICK_FALLBACK", code)
        self.assertIn("fallback-path", code)
        self.assertIn('Desktop(backend="uia")', code)

    def test_doc_helpers_emit_traceable_code(self) -> None:
        click_code = build_feishu_doc_click_code("分享")
        type_code = build_feishu_doc_type_code("hello")

        self.assertIn("FEISHU_DOC_CLICK_SEMANTIC", click_code)
        self.assertIn("agent.click", click_code)
        self.assertNotIn("_OFFSETS", click_code)
        self.assertNotIn("SetCursorPos", click_code)
        self.assertIn("'分享'", click_code)
        self.assertIn("FEISHU_DOC_TYPED", type_code)
        self.assertIn("'hello'", type_code)

    def test_windows_open_code_special_cases_feishu_and_browser(self) -> None:
        feishu_code = build_windows_open_code("飞书")
        browser_code = build_windows_open_code("chrome")

        self.assertIn("FEISHU_OPEN_CTYPES", feishu_code)
        self.assertIn("is_feishu = ", feishu_code)
        self.assertIn("_focus_existing_browser", browser_code)
        self.assertIn("WINDOWS_OPEN_EXISTING_BROWSER", browser_code)


if __name__ == "__main__":
    unittest.main()
