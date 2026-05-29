import json
import tempfile
import unittest
from pathlib import Path

from evaluation import StoryEvalCase, StoryQualityEvaluator, load_evalset


class StoryEvaluationTests(unittest.TestCase):
    def test_load_evalset_reads_story_eval_cases(self):
        cases = load_evalset(Path("evaluation/evalsets/star_clinic_basic.json"))

        self.assertGreaterEqual(len(cases), 3)
        self.assertIsInstance(cases[0], StoryEvalCase)
        self.assertEqual(cases[0].id, "star_clinic_plan_chapter_02")

    def test_load_evalset_reads_dev_holdout_and_basic_includes(self):
        dev_cases = load_evalset(Path("evaluation/evalsets/star_clinic_dev.json"))
        holdout_cases = load_evalset(Path("evaluation/evalsets/star_clinic_holdout.json"))
        basic_cases = load_evalset(Path("evaluation/evalsets/star_clinic_basic.json"))

        self.assertGreaterEqual(len(dev_cases), 5)
        self.assertGreaterEqual(len(holdout_cases), 4)
        self.assertEqual(
            [case.id for case in basic_cases],
            [case.id for case in dev_cases] + [case.id for case in holdout_cases],
        )

    def test_report_scores_are_percent_scale_and_raw_metric_is_preserved(self):
        cases = load_evalset(Path("evaluation/evalsets/star_clinic_dev.json"))
        case = next(item for item in cases if item.id == "star_clinic_beat_grounding")

        report = StoryQualityEvaluator().evaluate(case)

        self.assertTrue(0 <= report.total_score <= 100)
        self.assertTrue(all(0 <= score <= 100 for score in report.scores.values()))
        self.assertGreaterEqual(case.pass_threshold, 80)
        self.assertIn("beat_grounding", report.raw_scores)
        self.assertTrue(0 <= report.raw_scores["beat_grounding"] <= 5)

    def test_plan_case_scores_required_chapter_plan_constraints(self):
        cases = load_evalset(Path("evaluation/evalsets/star_clinic_dev.json"))
        case = next(item for item in cases if item.id == "star_clinic_plan_chapter_02")

        report = StoryQualityEvaluator().evaluate(case)

        self.assertEqual(report.case_id, case.id)
        self.assertTrue(report.passed)
        self.assertGreaterEqual(report.total_score, 80)
        self.assertIn("hard_constraints", report.scores)

    def test_beat_grounding_case_passes_when_draft_uses_scene_action(self):
        cases = load_evalset(Path("evaluation/evalsets/star_clinic_dev.json"))
        case = next(item for item in cases if item.id == "star_clinic_beat_grounding")

        report = StoryQualityEvaluator().evaluate(case)

        self.assertTrue(report.passed)
        self.assertGreaterEqual(report.scores["beat_grounding"], 80)
        self.assertGreaterEqual(report.raw_scores["beat_grounding"], 4)

    def test_revision_non_regression_case_records_revision_and_open_thread(self):
        cases = load_evalset(Path("evaluation/evalsets/star_clinic_dev.json"))
        case = next(item for item in cases if item.id == "star_clinic_revision_non_regression")

        report = StoryQualityEvaluator().evaluate(case)

        self.assertTrue(report.passed)
        self.assertEqual(report.observed["latest_revision"], 1)
        self.assertIn("PT-001", report.observed["open_plot_threads"])

    def test_minimal_pair_case_scores_narrative_memory(self):
        cases = load_evalset(Path("evaluation/evalsets/star_clinic_dev.json"))
        case = next(item for item in cases if item.id == "star_clinic_minimal_pairs")

        report = StoryQualityEvaluator().evaluate(case)

        self.assertTrue(report.passed)
        self.assertEqual(report.scores["minimal_pair_accuracy"], 100)
        self.assertEqual(report.observed["correct_pairs"], report.observed["total_pairs"])

    def test_revision_quality_case_passes_when_revision_rewrites_scene(self):
        cases = load_evalset(Path("evaluation/evalsets/star_clinic_dev.json"))
        case = next(item for item in cases if item.id == "star_clinic_revision_quality")

        report = StoryQualityEvaluator().evaluate(case)

        self.assertTrue(report.passed)
        self.assertGreaterEqual(report.scores["revision_quality"], 60)
        self.assertNotIn("revision patch", report.observed["revision_content"].lower())

    def test_evaluator_writes_json_and_markdown_results(self):
        cases = load_evalset(Path("evaluation/evalsets/star_clinic_dev.json"))

        with tempfile.TemporaryDirectory() as tmp:
            reports = StoryQualityEvaluator().evaluate_all(cases, Path(tmp))

            self.assertEqual(len(reports), len(cases))
            self.assertTrue((Path(tmp) / "story_quality_results.json").exists())
            self.assertTrue((Path(tmp) / "story_quality_results.md").exists())

            payload = json.loads(
                (Path(tmp) / "story_quality_results.json").read_text(encoding="utf-8")
            )
            self.assertTrue(all(0 <= item["total_score"] <= 100 for item in payload))
            self.assertTrue(all("raw_scores" in item for item in payload))

    def test_holdout_records_current_capability_boundary(self):
        cases = load_evalset(Path("evaluation/evalsets/star_clinic_holdout.json"))
        reports = StoryQualityEvaluator().evaluate_all(cases)

        failed = [report.case_id for report in reports if not report.passed]

        self.assertIn("star_clinic_holdout_character_choice_chain", failed)
        self.assertIn("star_clinic_holdout_plot_thread_progression", failed)
        self.assertIn("star_clinic_holdout_timeline_causality", failed)
        self.assertTrue(all(case.task == "story_agent_capability" for case in cases))

    def test_external_inspired_cases_include_nocha_near_miss_template(self):
        cases = load_evalset(Path("evaluation/evalsets/external_inspired_cases.json"))
        case = next(item for item in cases if item.required["source_dataset"] == "NoCha")

        template = case.required["template"]

        self.assertIn("关键词相似", template["ability"])
        self.assertIn("时间", template["expected_structure"])
        self.assertIn("因果", template["expected_structure"])

    def test_ara_claims_reference_stable_evidence_ids(self):
        claims = Path("research/ara/logic/claims.md").read_text(encoding="utf-8")

        for evidence_id in [
            "EV-NOCHA-001",
            "EV-GEVAL-001",
            "EV-SWEBENCH-001",
            "EV-AGENTBENCH-001",
            "EV-STORIUM-001",
        ]:
            self.assertTrue(Path(f"research/ara/evidence/{evidence_id}.md").exists())
            self.assertIn(evidence_id, claims)


if __name__ == "__main__":
    unittest.main()
