from __future__ import annotations

import os
from dataclasses import dataclass


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class LLMConfig:
    api_key: str = ""
    base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    model_name: str = "qwen3.6-max-preview"
    enable_thinking: bool = True

    @classmethod
    def from_env(cls) -> "LLMConfig":
        return cls(
            api_key=os.getenv("DASHSCOPE_API_KEY", ""),
            base_url=os.getenv(
                "DASHSCOPE_BASE_URL",
                "https://dashscope.aliyuncs.com/compatible-mode/v1",
            ),
            model_name=os.getenv("DASHSCOPE_MODEL", "qwen3.6-max-preview"),
            enable_thinking=_env_bool("DASHSCOPE_ENABLE_THINKING", True),
        )

    def chat_extra_body(self) -> dict[str, bool]:
        return {"enable_thinking": self.enable_thinking}

