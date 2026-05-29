from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

from novelagent import LLMClient

if TYPE_CHECKING:
    from .core import StoryEvalCase


REQUIRED_JUDGE_FIELDS = {
    "dimension",
    "score",
    "evidence",
    "failure_reason",
    "revision_advice",
}


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
        """返回某个 eval case 的结构化软质量评审结果。"""


class QwenStoryJudge:
    """用 Qwen 对小说软质量做结构化评审。

    Judge 只负责可信度、自然度、正文兑现度等软质量判断；硬规则和状态变化
    仍由代码层评分，不能被 Judge 高分覆盖。
    """

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
            "rubric": {
                "原则": "只评软质量，不替代规则层和状态变化层。",
                "高分条件": "必须引用正文或结构字段作为 evidence。",
                "禁止": "没有 evidence 时不得给高分；不得用泛泛表扬代替证据。",
            },
            "output_schema": {
                "results": [
                    {
                        "dimension": "string",
                        "score": "integer 0-100",
                        "evidence": "string，必须引用具体正文或结构证据",
                        "failure_reason": "string，没有失败也填空字符串",
                        "revision_advice": "string，给出可执行修订建议",
                    }
                ]
            },
        }
        result = self.client.generate_json(
            system_prompt=(
                "你是 NovelAgent 的中文小说评测 Judge。"
                "你必须输出合法 JSON，顶层包含 results 数组。"
                "每个结果必须包含 dimension、score、evidence、failure_reason、revision_advice。"
                "你只评人物选择是否可信、伏笔推进是否有效、因果是否自然、正文是否兑现结构；"
                "不得替代规则层硬检查。"
            ),
            user_payload=payload,
        )
        raw_results = result.get("results", [])
        if isinstance(raw_results, dict):
            raw_results = [raw_results]
        if not isinstance(raw_results, list):
            raise ValueError("Judge 结果的 results 必须是数组。")
        return [self._parse_result(item) for item in raw_results]

    def _parse_result(self, item: dict[str, Any]) -> QwenJudgeResult:
        if not isinstance(item, dict):
            raise ValueError("Judge 单条结果必须是对象。")
        missing = sorted(field for field in REQUIRED_JUDGE_FIELDS if field not in item)
        if missing:
            raise ValueError(f"Judge 结果缺少字段：{', '.join(missing)}")
        try:
            score = int(item["score"])
        except (TypeError, ValueError) as exc:
            raise ValueError("Judge score 必须是 0-100 的整数。") from exc
        return QwenJudgeResult(
            dimension=str(item["dimension"]),
            score=max(0, min(100, score)),
            evidence=str(item["evidence"]),
            failure_reason=str(item["failure_reason"]),
            revision_advice=str(item["revision_advice"]),
        )
