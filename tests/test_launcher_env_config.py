import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import launcher


class LauncherEnvRoutingTest(unittest.TestCase):
    def _fresh_config(self) -> dict:
        return copy.deepcopy(launcher.DEFAULT_CONFIG)

    def test_env_defaults_split_main_and_ground_ark_keys(self) -> None:
        cfg = self._fresh_config()
        env = {
            "ep-id": "ep-main-123",
            "api-key": "ark-main-key",
            "ARK_API_KEY": "ark-ground-key",
        }

        with patch.object(launcher, "_parse_env_txt", return_value=env):
            launcher._apply_env_defaults(cfg, had_main_routing=False)

        self.assertEqual(cfg["main_providers"]["volcano"]["model_id"], "ep-main-123")
        self.assertEqual(
            cfg["main_providers"]["volcano"]["model_api_key"], "ark-main-key"
        )
        self.assertEqual(
            cfg["ground_providers"]["doubao_ark"]["api_key"], "ark-ground-key"
        )

    def test_env_defaults_fallback_to_ground_key_when_main_key_missing(self) -> None:
        cfg = self._fresh_config()
        env = {
            "ep-id": "ep-main-123",
            "ARK_API_KEY": "ark-shared-key",
        }

        with patch.object(launcher, "_parse_env_txt", return_value=env):
            launcher._apply_env_defaults(cfg, had_main_routing=False)

        self.assertEqual(
            cfg["main_providers"]["volcano"]["model_api_key"], "ark-shared-key"
        )
        self.assertEqual(
            cfg["ground_providers"]["doubao_ark"]["api_key"], "ark-shared-key"
        )

    def test_env_defaults_repairs_legacy_main_key_fallback(self) -> None:
        cfg = self._fresh_config()
        cfg["main_providers"]["volcano"]["model_api_key"] = "ark-ground-key"
        env = {
            "ep-id": "ep-main-123",
            "api-key": "ark-main-key",
            "ARK_API_KEY": "ark-ground-key",
        }

        with patch.object(launcher, "_parse_env_txt", return_value=env):
            launcher._apply_env_defaults(cfg, had_main_routing=True)

        self.assertEqual(
            cfg["main_providers"]["volcano"]["model_api_key"], "ark-main-key"
        )

    def test_openai_env_does_not_override_default_doubao_main_provider(self) -> None:
        cfg = self._fresh_config()
        env = {
            "ep-id": "ep-main-123",
            "api-key": "ark-main-key",
            "oai_api": "openai-key",
            "oai_model": "gpt-5.4",
            "oai_base_url": "https://example.test/v1",
        }

        with patch.object(launcher, "_parse_env_txt", return_value=env):
            launcher._apply_env_defaults(cfg, had_main_routing=False)

        self.assertEqual(cfg["main_provider"], "volcano")
        self.assertEqual(cfg["model_id"], "ep-main-123")
        self.assertEqual(
            cfg["main_providers"]["openai_gpt"]["model_api_key"], "openai-key"
        )

    def test_load_config_defaults_to_doubao_when_only_openai_env_exists(self) -> None:
        env = {
            "oai_api": "openai-key",
            "oai_model": "gpt-5.4",
            "oai_base_url": "https://example.test/v1",
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = str(Path(tmpdir) / "missing-config.json")
            with (
                patch.object(launcher, "CONFIG_FILE", config_path),
                patch.object(launcher, "_parse_env_txt", return_value=env),
            ):
                cfg = launcher.load_config()

        self.assertEqual(cfg["main_provider"], "volcano")
        self.assertEqual(cfg["main_providers"]["openai_gpt"]["model_id"], "gpt-5.4")

    def test_explicit_openai_main_provider_is_preserved(self) -> None:
        raw = {
            "main_provider": "openai_gpt",
            "main_providers": {
                "openai_gpt": {
                    "model_api_key": "saved-openai-key",
                    "model_id": "gpt-5.4",
                    "model_url": "https://example.test/v1",
                }
            },
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text(json.dumps(raw), encoding="utf-8")
            with (
                patch.object(launcher, "CONFIG_FILE", str(config_path)),
                patch.object(launcher, "_parse_env_txt", return_value={}),
            ):
                cfg = launcher.load_config()

        self.assertEqual(cfg["main_provider"], "openai_gpt")
        self.assertEqual(cfg["model_id"], "gpt-5.4")


if __name__ == "__main__":
    unittest.main()
