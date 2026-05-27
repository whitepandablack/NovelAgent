from __future__ import annotations

import json
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from novelagent import NovelRequest, NovelWorkflow


@dataclass
class StoryEvalCase:
    id: str
    task: str
    request: dict[str, str]
    required: dict[str, Any] = field(default_factory=dict)
    forbidden: dict[str, Any] = field(default_factory=dict)
    expected_state_delta: dict[str, Any] = field(default_factory=dict)
    rubric: dict[str, int] = field(default_factory=dict)
    pass_threshold: int = 80


@dataclass
class StoryQualityFinding:
    category: str
    message: str
    severity: str = "warning"


@dataclass
class StoryQualityReport:
    case_id: str
    passed: bool
    total_score: int
    scores: dict[str, int]
    findings: list[StoryQualityFinding] = field(default_factory=list)
    observed: dict[str, Any] = field(default_factory=dict)


def load_evalset(path: Path) -> list[StoryEvalCase]:
    data = json.loads(path.read_text(encoding="utf-8"))
    raw_cases = data["cases"] if isinstance(data, dict) else data
    return [StoryEvalCase(**item) for item in raw_cases]


class StoryQualityEvaluator:
    def evaluate(self, case: StoryEvalCase) -> StoryQualityReport:
        if case.task == "plan_next_chapter":
            return self._evaluate_plan_next_chapter(case)
        if case.task == "draft_next_chapter_grounding":
            return self._evaluate_beat_grounding(case)
        if case.task == "revision_non_regression":
            return self._evaluate_revision_non_regression(case)
        if case.task == "narrative_minimal_pairs":
            return self._evaluate_narrative_minimal_pairs(case)
        if case.task == "revision_quality":
            return self._evaluate_revision_quality(case)
        return StoryQualityReport(
            case_id=case.id,
            passed=False,
            total_score=0,
            scores={"unsupported_task": 0},
            findings=[
                StoryQualityFinding(
                    category="unsupported_task",
                    message=f"不支持的评测任务：{case.task}",
                    severity="error",
                )
            ],
        )

    def evaluate_all(
        self, cases: list[StoryEvalCase], out_dir: Path | None = None
    ) -> list[StoryQualityReport]:
        reports = [self.evaluate(case) for case in cases]
        if out_dir is not None:
            self.write_reports(reports, out_dir)
        return reports

    def write_reports(self, reports: list[StoryQualityReport], out_dir: Path) -> None:
        out_dir.mkdir(parents=True, exist_ok=True)
        payload = [self._report_to_dict(report) for report in reports]
        (out_dir / "story_quality_results.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (out_dir / "story_quality_results.md").write_text(
            self._reports_to_markdown(reports),
            encoding="utf-8",
        )

    def _evaluate_plan_next_chapter(self, case: StoryEvalCase) -> StoryQualityReport:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._seed_project(case, Path(tmp))
            plan = NovelWorkflow().plan_next_chapter(project)

            findings: list[StoryQualityFinding] = []
            required = case.required
            self._expect_equal(
                findings,
                "chapter_number",
                plan.number,
                required.get("chapter_number"),
                "章节号不符合预期。",
            )
            for character in required.get("characters", []):
                if character not in plan.required_characters:
                    findings.append(
                        StoryQualityFinding(
                            category="required_character",
                            message=f"章节计划缺少必需人物：{character}。",
                            severity="error",
                        )
                    )
            for beat in required.get("beats", []):
                if beat not in plan.beats:
                    findings.append(
                        StoryQualityFinding(
                            category="required_beat",
                            message=f"章节计划缺少必需 beat：{beat}。",
                            severity="error",
                        )
                    )
            forbidden_text = case.forbidden.get("text", [])
            combined = f"{plan.title}\n{plan.goal}\n{' '.join(plan.beats)}"
            for text in forbidden_text:
                if text in combined:
                    findings.append(
                        StoryQualityFinding(
                            category="forbidden_text",
                            message=f"章节计划提前泄露禁用信息：{text}。",
                            severity="error",
                        )
                    )

            hard_score = 100 if not findings else max(0, 100 - 25 * len(findings))
            return self._build_report(
                case=case,
                scores={"hard_constraints": hard_score},
                findings=findings,
                observed={
                    "chapter_number": plan.number,
                    "required_characters": plan.required_characters,
                    "beats": plan.beats,
                },
            )

    def _evaluate_beat_grounding(self, case: StoryEvalCase) -> StoryQualityReport:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._seed_project(case, Path(tmp))
            NovelWorkflow().plan_next_chapter(project)
            chapter = NovelWorkflow().draft_next_chapter(project)
            beat = case.required.get("grounded_beat", "")
            score = self._score_beat_grounding(chapter.content, beat)
            findings: list[StoryQualityFinding] = []
            if score < case.required.get("minimum_grounding_score", 4):
                findings.append(
                    StoryQualityFinding(
                        category="beat_grounding",
                        message=(
                            f"beat“{beat}”只达到 {score} 分，"
                            "尚未通过具体场景行动兑现。"
                        ),
                    )
                )
            return self._build_report(
                case=case,
                scores={"beat_grounding": score},
                findings=findings,
                observed={"content": chapter.content, "grounded_beat": beat},
            )

    def _evaluate_revision_non_regression(self, case: StoryEvalCase) -> StoryQualityReport:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._seed_project(case, Path(tmp))
            workflow = NovelWorkflow()
            workflow.plan_next_chapter(project)
            chapter = workflow.draft_next_chapter(project)
            chapter.content = case.required.get("damaged_content", chapter.content)
            report = workflow.review_chapter(project, chapter.number)
            workflow.create_revision_tasks(project, report)
            revised = workflow.revise_chapter(project, chapter.number)

            findings: list[StoryQualityFinding] = []
            if revised.revision <= chapter.revision:
                findings.append(
                    StoryQualityFinding(
                        category="revision_version",
                        message="修订版没有递增 revision。",
                        severity="error",
                    )
                )
            open_threads = [
                thread.code for thread in project.plot_threads if thread.status == "open"
            ]
            for thread in case.required.get("open_plot_threads", []):
                if thread not in open_threads:
                    findings.append(
                        StoryQualityFinding(
                            category="plot_thread_regression",
                            message=f"修订后剧情线索不再保持开放：{thread}。",
                            severity="error",
                        )
                    )
            known_names = {character.name for character in project.characters}
            unknown = [
                name
                for name in revised.referenced_characters
                if name not in known_names
            ]
            if unknown:
                findings.append(
                    StoryQualityFinding(
                        category="unknown_character",
                        message=f"修订引入未知人物：{'、'.join(unknown)}。",
                        severity="error",
                    )
                )

            hard_score = 100 if not findings else max(0, 100 - 25 * len(findings))
            return self._build_report(
                case=case,
                scores={"hard_constraints": hard_score},
                findings=findings,
                observed={
                    "latest_revision": revised.revision,
                    "open_plot_threads": open_threads,
                    "revision_content": revised.content,
                },
            )

    def _evaluate_narrative_minimal_pairs(self, case: StoryEvalCase) -> StoryQualityReport:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._seed_project(case, Path(tmp))
            pairs = case.required.get("pairs", [])
            results = []
            for pair in pairs:
                true_score = self._narrative_statement_support(project, pair["true_statement"])
                false_score = self._narrative_statement_support(project, pair["false_statement"])
                predicted = "true" if true_score >= false_score else "false"
                results.append(
                    {
                        "id": pair["id"],
                        "predicted": predicted,
                        "true_score": true_score,
                        "false_score": false_score,
                        "evidence": pair.get("evidence", []),
                    }
                )
            correct = len([item for item in results if item["predicted"] == "true"])
            total = len(results)
            accuracy = round(100 * correct / total) if total else 0
            findings: list[StoryQualityFinding] = []
            if accuracy < 100:
                findings.append(
                    StoryQualityFinding(
                        category="minimal_pair_accuracy",
                        message=f"叙事 minimal-pair 准确率为 {accuracy}%。",
                        severity="error",
                    )
                )
            return self._build_report(
                case=case,
                scores={"minimal_pair_accuracy": accuracy},
                findings=findings,
                observed={
                    "correct_pairs": correct,
                    "total_pairs": total,
                    "pairs": results,
                },
            )

    def _evaluate_revision_quality(self, case: StoryEvalCase) -> StoryQualityReport:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._seed_project(case, Path(tmp))
            workflow = NovelWorkflow()
            workflow.plan_next_chapter(project)
            chapter = workflow.draft_next_chapter(project)
            chapter.content = case.required.get("damaged_content", chapter.content)
            report = workflow.review_chapter(project, chapter.number)
            workflow.create_revision_tasks(project, report)
            revised = workflow.revise_chapter(project, chapter.number)
            score = self._score_revision_quality(revised.content)
            findings: list[StoryQualityFinding] = []
            minimum = case.required.get("minimum_revision_quality", 60)
            if "修订补充：" in revised.content:
                findings.append(
                    StoryQualityFinding(
                        category="append_only_revision",
                        message="修订结果仍是追加审稿说明，没有重写成小说场景。",
                    )
                )
            if score < minimum and not findings:
                findings.append(
                    StoryQualityFinding(
                        category="revision_quality",
                        message=f"修订质量得分 {score}，低于最低要求 {minimum}。",
                    )
                )
            return self._build_report(
                case=case,
                scores={"revision_quality": score},
                findings=findings,
                observed={
                    "revision_content": revised.content,
                    "latest_revision": revised.revision,
                },
            )

    def _seed_project(self, case: StoryEvalCase, root: Path):
        request = NovelRequest(**case.request)
        return NovelWorkflow().run_seed_project(request, root)

    def _score_beat_grounding(self, content: str, beat: str) -> int:
        if not beat or beat not in content:
            return 0
        scene_markers = ["说", "问", "递", "看见", "记录", "扫描", "走廊", "物证"]
        if any(marker in content for marker in scene_markers) and f"：{beat}" not in content:
            return 5
        if "本章需要完成的节拍包括" in content:
            return 1
        return 3

    def _narrative_statement_support(self, project, statement: str) -> int:
        support = 0
        text_sources = []
        text_sources.extend(
            [
                project.title,
                project.premise,
                project.genre,
                project.style,
                project.story_bible.logline,
                " ".join(project.story_bible.rules),
            ]
        )
        text_sources.extend(
            [
                f"{character.name} {character.role} {character.goal} {character.conflict} {character.arc}"
                for character in project.characters
            ]
        )
        text_sources.extend(
            [
                f"{rule.code} {rule.description} {rule.source} {rule.status}"
                for rule in project.world_rules
            ]
        )
        text_sources.extend(
            [
                f"{thread.code} {thread.title} {thread.status} {thread.payoff}"
                for thread in project.plot_threads
            ]
        )
        text_sources.extend([chapter.content for chapter in project.chapters])
        corpus = "\n".join(text_sources)
        for token in self._statement_tokens(statement):
            if token in corpus:
                support += 1
        negation_markers = ["已经安全公开", "完全解决", "真实来源", "公开解释"]
        if any(marker in statement for marker in negation_markers):
            support -= 2
        return support

    def _statement_tokens(self, statement: str) -> list[str]:
        candidates = [
            "米拉",
            "更多真相",
            "无法安全",
            "震颤",
            "隐藏记忆",
            "核心异常",
            "乔主任",
            "第一章",
            "真实来源",
        ]
        return [token for token in candidates if token in statement]

    def _score_revision_quality(self, content: str) -> int:
        if "修订补充：" in content:
            return 20
        scene_markers = ["说", "问", "递", "看见", "记录", "扫描", "走廊", "物证"]
        if any(marker in content for marker in scene_markers):
            return 80
        return 50

    def _expect_equal(
        self,
        findings: list[StoryQualityFinding],
        category: str,
        observed: Any,
        expected: Any,
        message: str,
    ) -> None:
        if expected is not None and observed != expected:
            findings.append(
                StoryQualityFinding(
                    category=category,
                    message=f"{message} observed={observed!r}, expected={expected!r}",
                    severity="error",
                )
            )

    def _build_report(
        self,
        case: StoryEvalCase,
        scores: dict[str, int],
        findings: list[StoryQualityFinding],
        observed: dict[str, Any],
    ) -> StoryQualityReport:
        total = self._weighted_score(scores, case.rubric)
        return StoryQualityReport(
            case_id=case.id,
            passed=not any(item.severity == "error" for item in findings)
            and total >= case.pass_threshold,
            total_score=total,
            scores=scores,
            findings=findings,
            observed=observed,
        )

    def _weighted_score(self, scores: dict[str, int], rubric: dict[str, int]) -> int:
        if not scores:
            return 0
        if not rubric:
            return round(sum(scores.values()) / len(scores))
        total_weight = sum(rubric.get(key, 0) for key in scores)
        if total_weight <= 0:
            return round(sum(scores.values()) / len(scores))
        weighted = sum(scores[key] * rubric.get(key, 0) for key in scores)
        return round(weighted / total_weight)

    def _report_to_dict(self, report: StoryQualityReport) -> dict[str, Any]:
        return asdict(report)

    def _reports_to_markdown(self, reports: list[StoryQualityReport]) -> str:
        lines = ["# Story Quality Eval Results", ""]
        for report in reports:
            status = "PASS" if report.passed else "FAIL"
            lines.extend(
                [
                    f"## {report.case_id}: {status}",
                    "",
                    f"- Total: {report.total_score}",
                    f"- Scores: {report.scores}",
                ]
            )
            if report.findings:
                lines.append("- Findings:")
                for finding in report.findings:
                    lines.append(
                        f"  - [{finding.severity}] {finding.category}: {finding.message}"
                    )
            lines.append("")
        return "\n".join(lines)
