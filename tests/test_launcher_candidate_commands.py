import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import launcher


class LauncherCandidateCommandsTest(unittest.TestCase):
    def test_candidate_commands_cover_basic_business_products(self) -> None:
        joined = "\n".join(launcher.CANDIDATE_COMMANDS)

        expected_keywords = {
            "im": ("消息", "发送"),
            "docs": ("云文档", "项目周报"),
            "calendar": ("日历", "日程"),
            "base": ("多维表格", "测试用例记录表"),
            "vc": ("视频会议", "邀请"),
        }

        for product, keywords in expected_keywords.items():
            with self.subTest(product=product):
                self.assertTrue(all(keyword in joined for keyword in keywords))

    def test_candidate_commands_avoid_unsupported_random_emoji_probe(self) -> None:
        joined = "\n".join(launcher.CANDIDATE_COMMANDS)

        self.assertNotIn("随机选择一个表情", joined)

    def test_load_command_history_merges_new_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            history_path = Path(tmpdir) / "command_history.json"
            history_path.write_text(
                json.dumps(["自定义历史指令"], ensure_ascii=False),
                encoding="utf-8",
            )

            with patch.object(launcher, "HISTORY_FILE", str(history_path)):
                values = launcher.Launcher._load_command_history(object())

        self.assertEqual(values[0], "自定义历史指令")
        for command in launcher.CANDIDATE_COMMANDS:
            self.assertIn(command, values)

    def test_load_command_history_filters_invalid_items(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            history_path = Path(tmpdir) / "command_history.json"
            history_path.write_text(
                json.dumps(["  自定义历史指令  ", "", 1], ensure_ascii=False),
                encoding="utf-8",
            )

            with patch.object(launcher, "HISTORY_FILE", str(history_path)):
                values = launcher.Launcher._load_command_history(object())

        self.assertIn("自定义历史指令", values)
        self.assertNotIn("", values)
        self.assertNotIn(1, values)


if __name__ == "__main__":
    unittest.main()
