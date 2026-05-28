from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    return default if raw is None else float(raw)


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    return default if raw is None else int(raw)


def _env_list(name: str) -> list[str] | None:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return None
    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass
class LLMConfig:
    api_key: str = ""
    base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    model_name: str = "qwen3.7-max"
    enable_thinking: bool = True
    temperature: float = 0.1
    max_tokens: int = 8192
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    logprobs: bool = True
    top_logprobs: int = 5
    stream: bool = False
    stop_sequences: list[str] | None = None
    timeout: int = 900

    @classmethod
    def from_env(cls) -> "LLMConfig":
        return cls(
            api_key=os.getenv("DASHSCOPE_API_KEY", ""),
            base_url=os.getenv(
                "DASHSCOPE_BASE_URL",
                "https://dashscope.aliyuncs.com/compatible-mode/v1",
            ),
            model_name=os.getenv("DASHSCOPE_MODEL", "qwen3.7-max"),
            enable_thinking=_env_bool("DASHSCOPE_ENABLE_THINKING", True),
            temperature=_env_float("DASHSCOPE_TEMPERATURE", 0.1),
            max_tokens=_env_int("DASHSCOPE_MAX_TOKENS", 8192),
            top_p=_env_float("DASHSCOPE_TOP_P", 0.9),
            frequency_penalty=_env_float("DASHSCOPE_FREQUENCY_PENALTY", 0.0),
            presence_penalty=_env_float("DASHSCOPE_PRESENCE_PENALTY", 0.0),
            logprobs=_env_bool("DASHSCOPE_LOGPROBS", True),
            top_logprobs=_env_int("DASHSCOPE_TOP_LOGPROBS", 5),
            stream=_env_bool("DASHSCOPE_STREAM", False),
            stop_sequences=_env_list("DASHSCOPE_STOP"),
            timeout=_env_int("DASHSCOPE_TIMEOUT", 900),
        )

    def chat_extra_body(self) -> dict[str, bool]:
        return {"enable_thinking": self.enable_thinking}

    def chat_body_options(self) -> dict[str, Any]:
        body: dict[str, Any] = {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            "logprobs": self.logprobs,
            "top_logprobs": self.top_logprobs,
            "stream": self.stream,
            "extra_body": self.chat_extra_body(),
        }
        if self.stop_sequences:
            body["stop"] = self.stop_sequences
        return body
