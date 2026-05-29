import json
import tempfile
import unittest
from pathlib import Path

from evaluation import StoryEvalCase, StoryQualityEvaluator, load_evalset
from evaluation.judges import QwenJudgeResult, QwenStoryJudge


REQUEST = {
    "title": "走马灯星球",
    "premise": "星球和地球无限相似，文明整体倒退，远距离光接触会触发退变。",
    "genre": "文明退变科幻",
    "style": "倒序、危险、克制",
}


class FakeJudge:
    def __init__(self, *results):
        self.results = list(results)

    def judge(self, *, case, observed):
        return self.results


class FakeLLMClient:
    def __init__(self, payloads):
        self.payloads = list(payloads)

    def generate_json(self, *, system_prompt, user_payload):
        if not self.payloads:
            raise AssertionError(f"unexpected llm call: {user_payload['task']}")
        payload = self.payloads.pop(0)
        if callable(payload):
            return payload(user_payload)
        return payload


def capability_case(**overrides):
    data = {
        "id": "capability_smoke",
        "task": "story_agent_capability",
        "request": REQUEST,
        "required": {
            "contract_keys": [
                "character_choice_chain",
                "plot_thread_progression",
                "timeline_causality",
            ],
            "choice_required_fields": [
                "goal",
                "pressure",
                "decision",
                "cost",
                "consequence",
            ],
            "text_must_include": ["承担代价"],
        },
        "expected_state_delta": {
            "plot_thread_status": {"PT-001": "developed"},
            "timeline_causal_markers": ["因为", "所以"],
        },
        "rubric": {
            "contract_rules": 35,
            "state_delta": 35,
            "revision_effectiveness": 10,
            "text_payoff": 20,
        },
        "pass_threshold": 80,
    }
    data.update(overrides)
    return StoryEvalCase(**data)


def valid_plan_payload():
    return {
        "number": 2,
        "title": "第二章：光的回信",
        "goal": "主角在远距离光接触后选择继续靠近真相。",
        "scenes": ["走廊中的光信号", "主角主动承担代价"],
        "beats": ["光接触证据", "主动选择", "线索推进"],
        "required_characters": ["主角", "引路者"],
        "plot_threads": ["PT-001"],
        "narrative_contract": {
            "character_choice_chain": [
                {
                    "character": "主角",
                    "goal": "弄清文明倒退的触发原因",
                    "pressure": "继续调查会让自己暴露在退变风险里",
                    "decision": "不再退缩，主动接收引路者的信号",
                    "cost": "承担代价",
                    "consequence": "他从旁观者变成选择者",
                }
            ],
            "plot_thread_progression": [
                {
                    "thread_code": "PT-001",
                    "previous_status": "open",
                    "new_status": "developed",
                    "evidence": "光信号证明退变不是自然灾害",
                }
            ],
            "timeline_causality": [
                {
                    "cause_chapter": 1,
                    "effect_chapter": 2,
                    "cause": "第一章出现倒退现场",
                    "effect": "第二章主角追查光接触",
                }
            ],
        },
    }


def valid_draft_payload(content=None):
    return {
        "summary": "因为第一章的倒退现场无法解释，所以主角追查光接触。",
        "content": content
        or "引路者把冷白的光信号递到主角掌心。因为第一章的倒退现场无法解释，所以他没有后退，而是决定接收信号并承担代价：他的记忆会先于城市倒退。",
        "referenced_characters": ["主角", "引路者"],
        "narrative_contract": valid_plan_payload()["narrative_contract"],
    }


class StoryAgentCapabilityEvalTests(unittest.TestCase):
    def test_story_agent_capability_report_has_three_score_layers(self):
        judge = FakeJudge(
            QwenJudgeResult(
                dimension="正文兑现度",
                score=86,
                evidence="正文写出主角接收信号并承担代价。",
                failure_reason="",
                revision_advice="可以把代价写得更具体。",
            )
        )
        client = FakeLLMClient([valid_plan_payload(), valid_draft_payload()])

        report = StoryQualityEvaluator(
            workflow_mode="llm",
            llm_client=client,
            judge=judge,
        ).evaluate(capability_case())

        self.assertIn("contract_rules", report.rule_scores)
        self.assertIn("state_delta", report.state_scores)
        self.assertIn("正文兑现度", report.judge_scores)
        self.assertIn("observed", json.loads(json.dumps(report.__dict__, default=str)))
        self.assertGreaterEqual(report.total_score, 80)

    def test_story_agent_capability_fails_when_text_does_not_pay_off_contract(self):
        client = FakeLLMClient(
            [
                valid_plan_payload(),
                valid_draft_payload(content="主角看见光信号，房间很安静。"),
            ]
        )

        report = StoryQualityEvaluator(
            workflow_mode="llm",
            llm_client=client,
        ).evaluate(capability_case())

        self.assertFalse(report.passed)
        self.assertIn("text_payoff", report.rule_scores)
        self.assertTrue(
            any(finding.category == "text_payoff" for finding in report.findings)
        )

    def test_qwen_judge_rejects_missing_required_fields(self):
        client = FakeLLMClient(
            [
                {
                    "results": [
                        {
                            "dimension": "人物选择链",
                            "score": 90,
                            "evidence": "有选择证据",
                        }
                    ]
                }
            ]
        )

        with self.assertRaises(ValueError):
            QwenStoryJudge(client).judge(
                case=capability_case(),
                observed={"content": "正文"},
            )

    def test_evaluator_converts_judge_schema_error_to_finding(self):
        class BrokenJudge:
            def judge(self, *, case, observed):
                raise ValueError("Judge 结果缺少字段：failure_reason")

        report = StoryQualityEvaluator(
            workflow_mode="llm",
            llm_client=FakeLLMClient([valid_plan_payload(), valid_draft_payload()]),
            judge=BrokenJudge(),
        ).evaluate(capability_case())

        self.assertFalse(report.passed)
        self.assertTrue(any(item.category == "judge_schema" for item in report.findings))

    def test_evaluator_converts_judge_runtime_error_to_finding(self):
        class BrokenJudge:
            def judge(self, *, case, observed):
                raise ConnectionError("remote closed")

        report = StoryQualityEvaluator(
            workflow_mode="llm",
            llm_client=FakeLLMClient([valid_plan_payload(), valid_draft_payload()]),
            judge=BrokenJudge(),
        ).evaluate(capability_case())

        self.assertFalse(report.passed)
        self.assertTrue(any(item.category == "judge_runtime" for item in report.findings))
        self.assertIn("runtime_error", report.judge_observations)

    def test_story_agent_judge_dev_evalset_exists_and_uses_capability_task(self):
        cases = load_evalset(Path("evaluation/evalsets/story_agent_judge_dev.json"))

        self.assertGreaterEqual(len(cases), 4)
        self.assertTrue(all(case.task == "story_agent_capability" for case in cases))

    def test_external_inspired_cases_cover_research_sources(self):
        cases = load_evalset(Path("evaluation/evalsets/external_inspired_cases.json"))

        self.assertEqual(
            {"NoCha", "STORIUM", "ROCStories", "FairytaleQA", "TellMeWhy", "GLUCOSE"},
            {case.required["source_dataset"] for case in cases},
        )

    def test_report_writer_outputs_layered_chinese_markdown(self):
        report = StoryQualityEvaluator(
            workflow_mode="llm",
            llm_client=FakeLLMClient([valid_plan_payload(), valid_draft_payload()]),
        ).evaluate(capability_case())

        with tempfile.TemporaryDirectory() as tmp:
            StoryQualityEvaluator().write_reports([report], Path(tmp))
            markdown = (Path(tmp) / "story_quality_results.md").read_text(
                encoding="utf-8"
            )

        self.assertIn("规则层分数", markdown)
        self.assertIn("状态变化层分数", markdown)
        self.assertIn("Judge 层分数", markdown)


if __name__ == "__main__":
    unittest.main()
