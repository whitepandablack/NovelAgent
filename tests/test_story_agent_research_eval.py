import json
import tempfile
import unittest
from pathlib import Path

from evaluation import StoryQualityEvaluator, load_evalset
from evaluation.judges import QwenJudgeResult, QwenStoryJudge


class FakeJudge:
    def __init__(self, result):
        self.result = result

    def judge(self, case, observed):
        return [self.result]


class FakeLLMClient:
    def __init__(self, payload):
        self.payload = payload

    def generate_json(self, *, system_prompt, user_payload):
        return self.payload


class SequentialLLMClient:
    def __init__(self, payloads):
        self.payloads = list(payloads)

    def generate_json(self, *, system_prompt, user_payload):
        return self.payloads.pop(0)


class StoryAgentResearchEvalTests(unittest.TestCase):
    def test_research_evalset_contains_external_inspired_templates(self):
        cases = load_evalset(Path("evaluation/evalsets/story_agent_research_dev.json"))

        self.assertEqual(len(cases), 5)
        self.assertEqual(
            {
                "NoCha",
                "ROCStories",
                "FairytaleQA",
                "TellMeWhy/GLUCOSE",
                "STORIUM",
            },
            {case.required["source_dataset"] for case in cases},
        )
        for case in cases:
            template = case.required["template"]
            self.assertIn("ability", template)
            self.assertIn("input", template)
            self.assertIn("expected_structure", template)
            self.assertIn("failure_example", template)

    def test_qwen_judge_parses_structured_result(self):
        client = FakeLLMClient(
            {
                "results": [
                    {
                        "dimension": "character_choice",
                        "score": 82,
                        "evidence": "The chapter shows a deliberate choice.",
                        "failure_reason": "",
                        "revision_advice": "Make the cost clearer.",
                    }
                ]
            }
        )

        results = QwenStoryJudge(client).judge(
            case=load_evalset(Path("evaluation/evalsets/story_agent_research_dev.json"))[0],
            observed={"content": "draft"},
        )

        self.assertEqual(results[0].dimension, "character_choice")
        self.assertEqual(results[0].score, 82)
        self.assertEqual(results[0].evidence, "The chapter shows a deliberate choice.")

    def test_missing_judge_evidence_fails_even_with_high_score(self):
        cases = load_evalset(Path("evaluation/evalsets/story_agent_research_dev.json"))
        case = cases[0]
        judge = FakeJudge(
            QwenJudgeResult(
                dimension="character_choice",
                score=95,
                evidence="",
                failure_reason="",
                revision_advice="",
            )
        )

        report = StoryQualityEvaluator(judge=judge).evaluate(case)

        self.assertFalse(report.passed)
        self.assertIn("character_choice", report.judge_scores)
        self.assertTrue(
            any(finding.category == "judge_missing_evidence" for finding in report.findings)
        )

    def test_rule_and_judge_scores_are_written_to_report(self):
        cases = load_evalset(Path("evaluation/evalsets/story_agent_research_dev.json"))
        case = cases[0]
        judge = FakeJudge(
            QwenJudgeResult(
                dimension="character_choice",
                score=88,
                evidence="The observed contract and draft support the choice.",
                failure_reason="",
                revision_advice="Strengthen consequence wording.",
            )
        )

        with tempfile.TemporaryDirectory() as tmp:
            reports = StoryQualityEvaluator(judge=judge).evaluate_all([case], Path(tmp))
            payload = json.loads(
                (Path(tmp) / "story_quality_results.json").read_text(encoding="utf-8")
            )

        self.assertIn("contract_completeness", reports[0].scores)
        self.assertEqual(reports[0].judge_scores["character_choice"], 88)
        self.assertIn("judge_scores", payload[0])
        self.assertIn("judge_observations", payload[0])

    def test_baseline_and_llm_workflows_can_run_same_eval_case(self):
        case = load_evalset(Path("evaluation/evalsets/story_agent_research_dev.json"))[0]
        llm_client = SequentialLLMClient(
            [
                {
                    "number": 2,
                    "title": "第二章：米拉的警告",
                    "goal": "米拉推动林澈追查异常。",
                    "scenes": ["走廊交接证据"],
                    "beats": ["第二位见证者"],
                    "required_characters": ["林澈", "米拉"],
                    "plot_threads": ["PT-001"],
                    "narrative_contract": {
                        "character_choice_chain": [
                            {
                                "character": "林澈",
                                "choice": "暂缓上报并追查记录来源",
                                "cost": "承担制度压力",
                            }
                        ],
                        "plot_thread_progression": [
                            {
                                "thread_code": "PT-001",
                                "new_status": "developed",
                                "evidence": "米拉交出新的扫描记录",
                            }
                        ],
                        "timeline_causality": [
                            {
                                "cause": "第一章的异常记录无法解释",
                                "effect": "第二章林澈继续追查",
                            }
                        ],
                    },
                },
                {
                    "summary": "林澈因异常记录继续追查。",
                    "content": "林澈在走廊接过米拉递来的扫描记录，因此决定承担压力继续追查。",
                    "referenced_characters": ["林澈", "米拉"],
                    "narrative_contract": {
                        "character_choice_chain": [
                            {
                                "character": "林澈",
                                "choice": "继续追查",
                                "cost": "承担制度压力",
                            }
                        ],
                        "plot_thread_progression": [
                            {
                                "thread_code": "PT-001",
                                "new_status": "developed",
                                "evidence": "扫描记录",
                            }
                        ],
                        "timeline_causality": [
                            {
                                "cause": "异常记录无法解释",
                                "effect": "继续追查",
                            }
                        ],
                    },
                },
            ]
        )

        baseline_report = StoryQualityEvaluator(workflow_mode="baseline").evaluate(case)
        llm_report = StoryQualityEvaluator(
            workflow_mode="llm",
            llm_client=llm_client,
        ).evaluate(case)

        self.assertEqual(baseline_report.observed["workflow"], "baseline")
        self.assertEqual(llm_report.observed["workflow"], "llm")
        self.assertIn("contract_completeness", llm_report.scores)

    def test_research_survey_records_dataset_matrix(self):
        survey = Path("research/eval-research/story-agent-eval-survey.md").read_text(
            encoding="utf-8"
        )

        for dataset in [
            "NoCha",
            "STORIUM",
            "ROCStories",
            "FairytaleQA",
            "TellMeWhy",
            "GLUCOSE",
        ]:
            self.assertIn(dataset, survey)
        self.assertIn("可直接用", survey)
        self.assertIn("只能借鉴", survey)
        self.assertIn("不适合", survey)


if __name__ == "__main__":
    unittest.main()
