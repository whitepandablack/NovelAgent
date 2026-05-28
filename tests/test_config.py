import os
import unittest
from unittest.mock import patch

from novelagent import LLMConfig


class LLMConfigTests(unittest.TestCase):
    def test_default_dashscope_config_uses_qwen_37_without_hardcoded_key(self):
        with patch.dict(os.environ, {}, clear=True):
            config = LLMConfig.from_env()

        self.assertEqual(config.base_url, "https://dashscope.aliyuncs.com/compatible-mode/v1")
        self.assertEqual(config.model_name, "qwen3.7-max")
        self.assertTrue(config.enable_thinking)
        self.assertEqual(config.api_key, "")
        self.assertEqual(config.temperature, 0.1)
        self.assertEqual(config.max_tokens, 4096)
        self.assertEqual(config.top_p, 0.9)
        self.assertTrue(config.logprobs)
        self.assertEqual(config.top_logprobs, 5)

    def test_env_overrides_do_not_require_hardcoded_key(self):
        with patch.dict(
            os.environ,
            {
                "DASHSCOPE_API_KEY": "test-key",
                "DASHSCOPE_MODEL": "qwen-plus",
                "DASHSCOPE_ENABLE_THINKING": "false",
                "DASHSCOPE_TEMPERATURE": "0.3",
                "DASHSCOPE_MAX_TOKENS": "2048",
                "DASHSCOPE_TOP_P": "0.7",
                "DASHSCOPE_FREQUENCY_PENALTY": "0.2",
                "DASHSCOPE_PRESENCE_PENALTY": "0.4",
                "DASHSCOPE_LOGPROBS": "false",
                "DASHSCOPE_TOP_LOGPROBS": "3",
                "DASHSCOPE_STREAM": "true",
                "DASHSCOPE_STOP": "END,STOP",
            },
            clear=True,
        ):
            config = LLMConfig.from_env()

        self.assertEqual(config.api_key, "test-key")
        self.assertEqual(config.model_name, "qwen-plus")
        self.assertFalse(config.enable_thinking)
        self.assertEqual(config.temperature, 0.3)
        self.assertEqual(config.max_tokens, 2048)
        self.assertEqual(config.top_p, 0.7)
        self.assertEqual(config.frequency_penalty, 0.2)
        self.assertEqual(config.presence_penalty, 0.4)
        self.assertFalse(config.logprobs)
        self.assertEqual(config.top_logprobs, 3)
        self.assertTrue(config.stream)
        self.assertEqual(config.stop_sequences, ["END", "STOP"])

    def test_chat_body_includes_generation_parameters(self):
        config = LLMConfig(api_key="test-key", stop_sequences=["END"])

        body = config.chat_body_options()

        self.assertEqual(body["temperature"], 0.1)
        self.assertEqual(body["max_tokens"], 4096)
        self.assertEqual(body["top_p"], 0.9)
        self.assertEqual(body["logprobs"], True)
        self.assertEqual(body["top_logprobs"], 5)
        self.assertEqual(body["stop"], ["END"])
        self.assertEqual(body["extra_body"], {"enable_thinking": True})


if __name__ == "__main__":
    unittest.main()
