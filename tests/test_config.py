import os
import unittest
from unittest.mock import patch

from novelagent import LLMConfig


class LLMConfigTests(unittest.TestCase):
    def test_default_dashscope_config_uses_current_qwen_max_preview(self):
        with patch.dict(os.environ, {}, clear=True):
            config = LLMConfig.from_env()

        self.assertEqual(config.base_url, "https://dashscope.aliyuncs.com/compatible-mode/v1")
        self.assertEqual(config.model_name, "qwen3.6-max-preview")
        self.assertTrue(config.enable_thinking)
        self.assertEqual(config.api_key, "")

    def test_env_overrides_do_not_require_hardcoded_key(self):
        with patch.dict(
            os.environ,
            {
                "DASHSCOPE_API_KEY": "test-key",
                "DASHSCOPE_MODEL": "qwen-plus",
                "DASHSCOPE_ENABLE_THINKING": "false",
            },
            clear=True,
        ):
            config = LLMConfig.from_env()

        self.assertEqual(config.api_key, "test-key")
        self.assertEqual(config.model_name, "qwen-plus")
        self.assertFalse(config.enable_thinking)


if __name__ == "__main__":
    unittest.main()

