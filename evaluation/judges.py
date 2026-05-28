from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

from novelagent import LLMClient

if TYPE_CHECKING:
    from .core import StoryEvalCase


@dataclass
class QwenJudgeResult:
    dimension: str
    score: int
    evidence: str
    failure_reason: str
    revision_advice: str


class StoryJudge(Protocol):
    def judge(
        self, *, case: "StoryEvalCase", observed: dict[str, Any]
    ) -> list[QwenJudgeResult]:
        """Return structured soft-quality judgments for one eval case."""


class QwenStoryJudge:
    def __init__(self, client: LLMClient):
        self.client = client

    def judge(
        self, *, case: "StoryEvalCase", observed: dict[str, Any]
    ) -> list[QwenJudgeResult]:
        payload = {
            "case_id": case.id,
            "task": case.task,
            "required": case.required,
            "observed": observed,
            "output_schema": {
                "results": [
                    {
                        "dimension": "string",
                        "score": "integer 0-100",
                        "evidence": "string, must cite concrete story/contract evidence",
                        "failure_reason": "string",
                        "revision_advice": "string",
                    }
                ]
            },
            "scoring_rule": (
                "只评软质量。没有正文证据或结构化证据时不得给高分；"
                "不要替代规则层硬检查。"
            ),
        }
        result = self.client.generate_json(
            system_prompt=(
                "你是 NovelAgent 的小说评测 Judge。"
                "你必须输出合法 JSON，并严格包含 results 数组。"
                "每个结果必须包含 dimension、score、evidence、"
                "failure_reason、revision_advice。"
            ),
            user_payload=payload,
        )
        raw_results = result.get("results", [])
        if isinstance(raw_results, dict):
            raw_results = [raw_results]
        return [self._parse_result(item) for item in raw_results]

    def _parse_result(self, item: dict[str, Any]) -> QwenJudgeResult:
        return QwenJudgeResult(
            dimension=str(item.get("dimension", "unknown")),
            score=max(0, min(100, int(item.get("score", 0)))),
            evidence=str(item.get("evidence", "")),
            failure_reason=str(item.get("failure_reason", "")),
            revision_advice=str(item.get("revision_advice", "")),
        )
