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
    raw_scores: dict[str, Any] = field(default_factory=dict)


def load_evalset(path: Path) -> list[StoryEvalCase]:
    data = json.loads(path.read_text(encoding="utf-8"))
    raw_cases: list[dict[str, Any]] = []
    if isinstance(data, dict):
        for include in data.get("include", []):
            raw_cases.extend(
                asdict(case) for case in load_evalset((path.parent / include).resolve())
            )
        raw_cases.extend(data.get("cases", []))
    else:
        raw_cases = data
    return [StoryEvalCase(**item) for item in raw_cases]


class StoryQualityEvaluator:
    def evaluate(self, case: StoryEvalCase) -> StoryQualityReport:
        handlers = {
            "plan_next_chapter": self._evaluate_plan_next_chapter,
            "draft_next_chapter_grounding": self._evaluate_beat_grounding,
            "revision_non_regression": self._evaluate_revision_non_regression,
            "narrative_minimal_pairs": self._evaluate_narrative_minimal_pairs,
            "revision_quality": self._evaluate_revision_quality,
            "character_arc_consistency": self._evaluate_character_arc_consistency,
            "plot_thread_progression": self._evaluate_plot_thread_progression,
            "timeline_causality": self._evaluate_timeline_causality,
            "harder_minimal_pairs": self._evaluate_narrative_minimal_pairs,
        }
        handler = handlers.get(case.task)
        if handler is None:
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
        return handler(case)

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
            combined = f"{plan.title}\n{plan.goal}\n{' '.join(plan.beats)}"
            for text in case.forbidden.get("text", []):
                if text in combined:
                    findings.append(
                        StoryQualityFinding(
                            category="forbidden_text",
                            message=f"章节计划提前泄露禁用信息：{text}。",
                            severity="error",
                        )
                    )

            return self._build_report(
                case=case,
                scores={"hard_constraints": self._hard_score(findings)},
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
            workflow = NovelWorkflow()
            workflow.plan_next_chapter(project)
            chapter = workflow.draft_next_chapter(project)
            beat = case.required.get("grounded_beat", "")
            raw_score = self._score_beat_grounding(chapter.content, beat)
            normalized = raw_score * 20
            minimum = case.required.get("minimum_grounding_score", 4)
            findings: list[StoryQualityFinding] = []
            if raw_score < minimum:
                findings.append(
                    StoryQualityFinding(
                        category="beat_grounding",
                        message=f"beat grounding 原始分 {raw_score}/5，低于 {minimum}/5。",
                    )
                )
            return self._build_report(
                case=case,
                scores={"beat_grounding": normalized},
                findings=findings,
                observed={"content": chapter.content, "grounded_beat": beat},
                raw_scores={"beat_grounding": raw_score},
            )

    def _evaluate_revision_non_regression(self, case: StoryEvalCase) -> StoryQualityReport:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._seed_project(case, Path(tmp))
            workflow = NovelWorkflow()
            workflow.plan_next_chapter(project)
            chapter = workflow.draft_next_chapter(project)
            chapter.content = case.required.get("damaged_content", chapter.content)
            review = workflow.review_chapter(project, chapter.number)
            workflow.create_revision_tasks(project, review)
            revised = workflow.revise_chapter(project, chapter.number)

            findings: list[StoryQualityFinding] = []
            if revised.revision <= chapter.revision:
                findings.append(
                    StoryQualityFinding(
                        category="revision_version",
                        message="修订版本没有递增 revision。",
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
                name for name in revised.referenced_characters if name not in known_names
            ]
            if unknown:
                findings.append(
                    StoryQualityFinding(
                        category="unknown_character",
                        message=f"修订引入未知人物：{'、'.join(unknown)}。",
                        severity="error",
                    )
                )

            return self._build_report(
                case=case,
                scores={"hard_constraints": self._hard_score(findings)},
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
                true_score = self._narrative_statement_support(
                    project, pair["true_statement"]
                )
                false_score = self._narrative_statement_support(
                    project, pair["false_statement"]
                )
                predicted = "true" if true_score > false_score else "false"
                correct = predicted == pair.get("expected", "true")
                results.append(
                    {
                        "id": pair["id"],
                        "predicted": predicted,
                        "correct": correct,
                        "true_score": true_score,
                        "false_score": false_score,
                        "near_miss": pair.get("near_miss", False),
                        "evidence": pair.get("evidence", []),
                    }
                )
            correct_count = sum(1 for item in results if item["correct"])
            total = len(results)
            accuracy = round(100 * correct_count / total) if total else 0
            findings: list[StoryQualityFinding] = []
            if accuracy < case.pass_threshold:
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
                    "correct_pairs": correct_count,
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
            review = workflow.review_chapter(project, chapter.number)
            workflow.create_revision_tasks(project, review)
            revised = workflow.revise_chapter(project, chapter.number)
            score = self._score_revision_quality(revised.content)
            minimum = case.required.get("minimum_revision_quality", 60)
            findings: list[StoryQualityFinding] = []
            if self._looks_like_append_only_revision(revised.content):
                findings.append(
                    StoryQualityFinding(
                        category="append_only_revision",
                        message="修订结果仍像追加审稿说明，没有重写成小说场景。",
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

    def _evaluate_character_arc_consistency(
        self, case: StoryEvalCase
    ) -> StoryQualityReport:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._seed_project(case, Path(tmp))
            workflow = NovelWorkflow()
            workflow.plan_next_chapter(project)
            chapter = workflow.draft_next_chapter(project)
            content = chapter.content
            required_markers = case.required.get("arc_markers", [])
            forbidden_markers = case.forbidden.get("passive_markers", [])
            matched = [marker for marker in required_markers if marker in content]
            forbidden_hits = [marker for marker in forbidden_markers if marker in content]
            findings: list[StoryQualityFinding] = []
            if len(matched) < case.required.get("minimum_arc_markers", 1):
                findings.append(
                    StoryQualityFinding(
                        category="character_arc_consistency",
                        message="人物行动没有足够体现 goal/conflict/arc。",
                        severity="error",
                    )
                )
            if forbidden_hits:
                findings.append(
                    StoryQualityFinding(
                        category="character_arc_consistency",
                        message=f"人物弧线出现被动化表达：{forbidden_hits}。",
                    )
                )
            score = round(100 * len(matched) / len(required_markers)) if required_markers else 100
            if forbidden_hits:
                score = max(0, score - 20)
            return self._build_report(
                case=case,
                scores={"character_arc_consistency": score},
                findings=findings,
                observed={"matched_arc_markers": matched, "content": content},
            )

    def _evaluate_plot_thread_progression(
        self, case: StoryEvalCase
    ) -> StoryQualityReport:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._seed_project(case, Path(tmp))
            workflow = NovelWorkflow()
            workflow.plan_next_chapter(project)
            workflow.draft_next_chapter(project)
            required_status = case.required.get("thread_status", {})
            findings: list[StoryQualityFinding] = []
            observed = {
                thread.code: {
                    "status": thread.status,
                    "related_chapters": thread.related_chapters,
                }
                for thread in project.plot_threads
            }
            for code, status in required_status.items():
                if observed.get(code, {}).get("status") != status:
                    findings.append(
                        StoryQualityFinding(
                            category="plot_thread_progression",
                            message=f"{code} 没有从重复提及推进到 {status} 状态。",
                            severity="error",
                        )
                    )
            for code, chapter_number in case.required.get("related_chapters", {}).items():
                if chapter_number not in observed.get(code, {}).get("related_chapters", []):
                    findings.append(
                        StoryQualityFinding(
                            category="plot_thread_progression",
                            message=f"{code} 没有记录第 {chapter_number} 章的推进。",
                            severity="error",
                        )
                    )
            return self._build_report(
                case=case,
                scores={"plot_thread_progression": self._hard_score(findings)},
                findings=findings,
                observed=observed,
            )

    def _evaluate_timeline_causality(self, case: StoryEvalCase) -> StoryQualityReport:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._seed_project(case, Path(tmp))
            workflow = NovelWorkflow()
            workflow.plan_next_chapter(project)
            workflow.draft_next_chapter(project)
            summaries = [event.summary for event in project.timeline]
            causal_markers = case.required.get("causal_markers", [])
            matched = [
                marker for marker in causal_markers if any(marker in item for item in summaries)
            ]
            findings: list[StoryQualityFinding] = []
            if len(project.timeline) < case.required.get("minimum_events", 2):
                findings.append(
                    StoryQualityFinding(
                        category="timeline_causality",
                        message="时间线事件不足，无法评估章节因果链。",
                        severity="error",
                    )
                )
            if len(matched) < case.required.get("minimum_causal_markers", 1):
                findings.append(
                    StoryQualityFinding(
                        category="timeline_causality",
                        message="时间线摘要没有记录可审计的因果连接。",
                        severity="error",
                    )
                )
            score = 100 if not findings else 50 if summaries else 0
            return self._build_report(
                case=case,
                scores={"timeline_causality": score},
                findings=findings,
                observed={"timeline_summaries": summaries, "matched_markers": matched},
            )

    def _seed_project(self, case: StoryEvalCase, root: Path):
        request = NovelRequest(**case.request)
        return NovelWorkflow().run_seed_project(request, root)

    def _score_beat_grounding(self, content: str, beat: str) -> int:
        if self._has_scene_action(content) and (not beat or beat in content):
            return 5
        if self._has_scene_action(content):
            return 4
        if beat and beat in content:
            return 3
        if content:
            return 1
        return 0

    def _narrative_statement_support(self, project, statement: str) -> int:
        corpus = self._project_corpus(project)
        support = 0
        for token in self._statement_tokens(statement):
            if token in corpus:
                support += 1
        for marker in self._negation_markers():
            if marker in statement:
                support -= 2
        return support

    def _statement_tokens(self, statement: str) -> list[str]:
        candidates = [
            "Mira",
            "secret",
            "memory",
            "tremor",
            "abnormal",
            "public",
            "resolved",
            "source",
            "Lin",
            "PT-001",
            "WR-001",
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

    def _negation_markers(self) -> list[str]:
        return [
            "already public",
            "fully resolved",
            "true source",
            "safe public explanation",
            "已经安全公开",
            "完全解决",
            "真实来源",
            "公开解释",
        ]

    def _project_corpus(self, project) -> str:
        text_sources = [
            project.title,
            project.premise,
            project.genre,
            project.style,
            project.story_bible.logline,
            " ".join(project.story_bible.rules),
        ]
        text_sources.extend(
            f"{character.name} {character.role} {character.goal} {character.conflict} {character.arc}"
            for character in project.characters
        )
        text_sources.extend(
            f"{rule.code} {rule.description} {rule.source} {rule.status}"
            for rule in project.world_rules
        )
        text_sources.extend(
            f"{thread.code} {thread.title} {thread.status} {thread.payoff}"
            for thread in project.plot_threads
        )
        text_sources.extend(chapter.content for chapter in project.chapters)
        return "\n".join(text_sources)

    def _score_revision_quality(self, content: str) -> int:
        if self._looks_like_append_only_revision(content):
            return 20
        if self._has_scene_action(content):
            return 80
        return 50

    def _looks_like_append_only_revision(self, content: str) -> bool:
        return "修订补充" in content or "revision patch" in content.lower()

    def _has_scene_action(self, content: str) -> bool:
        markers = [
            "说",
            "问",
            "看见",
            "记录",
            "扫描",
            "走廊",
            "证据",
            "递到",
            "低声",
            "said",
            "asked",
            "record",
            "evidence",
        ]
        return any(marker in content for marker in markers) or len(content) >= 120

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

    def _hard_score(self, findings: list[StoryQualityFinding]) -> int:
        errors = sum(1 for item in findings if item.severity == "error")
        return 100 if errors == 0 else max(0, 100 - 25 * errors)

    def _build_report(
        self,
        case: StoryEvalCase,
        scores: dict[str, int],
        findings: list[StoryQualityFinding],
        observed: dict[str, Any],
        raw_scores: dict[str, Any] | None = None,
    ) -> StoryQualityReport:
        bounded_scores = {
            key: max(0, min(100, value)) for key, value in scores.items()
        }
        total = self._weighted_score(bounded_scores, case.rubric)
        return StoryQualityReport(
            case_id=case.id,
            passed=not any(item.severity == "error" for item in findings)
            and total >= case.pass_threshold,
            total_score=max(0, min(100, total)),
            scores=bounded_scores,
            findings=findings,
            observed=observed,
            raw_scores=raw_scores or {},
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
                    f"- Total: {report.total_score}/100",
                    f"- Scores: {report.scores}",
                    f"- Raw scores: {report.raw_scores}",
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
