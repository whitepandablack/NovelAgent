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

    def test_plan_case_scores_required_chapter_plan_constraints(self):
        cases = load_evalset(Path("evaluation/evalsets/star_clinic_basic.json"))
        case = next(item for item in cases if item.id == "star_clinic_plan_chapter_02")

        report = StoryQualityEvaluator().evaluate(case)

        self.assertEqual(report.case_id, case.id)
        self.assertTrue(report.passed)
        self.assertGreaterEqual(report.total_score, 80)
        self.assertIn("hard_constraints", report.scores)

    def test_beat_grounding_case_exposes_template_weakness(self):
        cases = load_evalset(Path("evaluation/evalsets/star_clinic_basic.json"))
        case = next(item for item in cases if item.id == "star_clinic_beat_grounding")

        report = StoryQualityEvaluator().evaluate(case)

        self.assertFalse(report.passed)
        self.assertLess(report.scores["beat_grounding"], 4)
        self.assertTrue(
            any(finding.category == "beat_grounding" for finding in report.findings)
        )

    def test_revision_non_regression_case_records_revision_and_open_thread(self):
        cases = load_evalset(Path("evaluation/evalsets/star_clinic_basic.json"))
        case = next(item for item in cases if item.id == "star_clinic_revision_non_regression")

        report = StoryQualityEvaluator().evaluate(case)

        self.assertTrue(report.passed)
        self.assertEqual(report.observed["latest_revision"], 1)
        self.assertIn("PT-001", report.observed["open_plot_threads"])

    def test_minimal_pair_case_scores_narrative_memory(self):
        cases = load_evalset(Path("evaluation/evalsets/star_clinic_basic.json"))
        case = next(item for item in cases if item.id == "star_clinic_minimal_pairs")

        report = StoryQualityEvaluator().evaluate(case)

        self.assertTrue(report.passed)
        self.assertEqual(report.scores["minimal_pair_accuracy"], 100)
        self.assertEqual(report.observed["correct_pairs"], report.observed["total_pairs"])

    def test_revision_quality_case_exposes_append_only_revision(self):
        cases = load_evalset(Path("evaluation/evalsets/star_clinic_basic.json"))
        case = next(item for item in cases if item.id == "star_clinic_revision_quality")

        report = StoryQualityEvaluator().evaluate(case)

        self.assertFalse(report.passed)
        self.assertLess(report.scores["revision_quality"], 60)
        self.assertTrue(
            any(finding.category == "append_only_revision" for finding in report.findings)
        )

    def test_evaluator_writes_json_and_markdown_results(self):
        cases = load_evalset(Path("evaluation/evalsets/star_clinic_basic.json"))

        with tempfile.TemporaryDirectory() as tmp:
            reports = StoryQualityEvaluator().evaluate_all(cases, Path(tmp))

            self.assertEqual(len(reports), len(cases))
            self.assertTrue((Path(tmp) / "story_quality_results.json").exists())
            self.assertTrue((Path(tmp) / "story_quality_results.md").exists())


if __name__ == "__main__":
    unittest.main()
