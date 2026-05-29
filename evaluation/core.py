from __future__ import annotations

import json
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from novelagent import (
    LLMClient,
    LLMNovelWorkflow,
    NovelRequest,
    NovelWorkflow,
    OpenAICompatibleClient,
)


CHOICE_ALIASES = {
    "decision": ("decision", "choice", "action"),
    "pressure": ("pressure", "conflict", "risk"),
}


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
    rule_scores: dict[str, int] = field(default_factory=dict)
    state_scores: dict[str, int] = field(default_factory=dict)
    judge_scores: dict[str, int] = field(default_factory=dict)
    raw_scores: dict[str, Any] = field(default_factory=dict)
    judge_observations: dict[str, Any] = field(default_factory=dict)


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


def score_contract_rules(
    contract: dict[str, Any],
    required: dict[str, Any],
    findings: list[StoryQualityFinding],
) -> dict[str, int]:
    required_keys = required.get("contract_keys", [])
    missing_keys = [key for key in required_keys if not contract.get(key)]
    for key in missing_keys:
        findings.append(
            StoryQualityFinding(
                "contract_rules",
                f"narrative_contract 缺少或未填充字段：{key}。",
                "error",
            )
        )

    key_score = (
        round(100 * (len(required_keys) - len(missing_keys)) / len(required_keys))
        if required_keys
        else 100
    )

    chain = _as_list(contract.get("character_choice_chain"))
    choice_fields = required.get(
        "choice_required_fields",
        ["goal", "pressure", "decision", "cost", "consequence"],
    )
    choice_errors = 0
    if "character_choice_chain" in required_keys or choice_fields:
        if not chain:
            choice_errors += len(choice_fields) or 1
            findings.append(
                StoryQualityFinding("contract_rules", "人物选择链为空。", "error")
            )
        for index, item in enumerate(chain):
            if not isinstance(item, dict):
                choice_errors += 1
                findings.append(
                    StoryQualityFinding(
                        "contract_rules",
                        f"人物选择链第 {index + 1} 项不是对象。",
                        "error",
                    )
                )
                continue
            missing = [
                field_name
                for field_name in choice_fields
                if not _contract_value(item, field_name)
            ]
            if missing:
                choice_errors += len(missing)
                findings.append(
                    StoryQualityFinding(
                        "contract_rules",
                        f"人物选择链第 {index + 1} 项缺少：{', '.join(missing)}。",
                        "error",
                    )
                )

    progression = _as_list(contract.get("plot_thread_progression"))
    progression_errors = 0
    if "plot_thread_progression" in required_keys:
        if not progression:
            progression_errors += 1
            findings.append(
                StoryQualityFinding("contract_rules", "伏笔推进链为空。", "error")
            )
        for index, item in enumerate(progression):
            if not isinstance(item, dict):
                progression_errors += 1
                findings.append(
                    StoryQualityFinding(
                        "contract_rules",
                        f"伏笔推进链第 {index + 1} 项不是对象。",
                        "error",
                    )
                )
                continue
            if not item.get("thread_code"):
                progression_errors += 1
                findings.append(
                    StoryQualityFinding("contract_rules", "伏笔推进缺少 thread_code。", "error")
                )
            if not any(
                item.get(key)
                for key in ("new_status", "status", "current_state", "evidence")
            ):
                progression_errors += 1
                findings.append(
                    StoryQualityFinding("contract_rules", "伏笔推进缺少阶段变化证据。", "error")
                )

    causality = _as_list(contract.get("timeline_causality"))
    causality_errors = 0
    if "timeline_causality" in required_keys:
        if not causality:
            causality_errors += 1
            findings.append(
                StoryQualityFinding("contract_rules", "时间线因果链为空。", "error")
            )
        for index, item in enumerate(causality):
            if not isinstance(item, dict):
                causality_errors += 1
                findings.append(
                    StoryQualityFinding(
                        "contract_rules",
                        f"时间线因果链第 {index + 1} 项不是对象。",
                        "error",
                    )
                )
                continue
            if not (item.get("cause") and item.get("effect")):
                causality_errors += 1
                findings.append(
                    StoryQualityFinding(
                        "contract_rules",
                        "时间线因果链必须同时包含 cause 和 effect。",
                        "error",
                    )
                )

    structural_errors = choice_errors + progression_errors + causality_errors
    structural_score = max(0, 100 - 20 * structural_errors)
    return {
        "contract_rules": round((key_score + structural_score) / 2),
        "contract_completeness": key_score,
    }


def score_state_delta(
    *,
    project: Any,
    case: StoryEvalCase,
    timeline_before: int,
    findings: list[StoryQualityFinding],
) -> dict[str, int]:
    required_status = case.expected_state_delta.get("plot_thread_status", {})
    status_errors = 0
    for code, expected in required_status.items():
        actual = next(
            (thread.status for thread in project.plot_threads if thread.code == code),
            None,
        )
        if actual != expected:
            status_errors += 1
            findings.append(
                StoryQualityFinding(
                    "state_delta",
                    f"{code} 状态为 {actual!r}，未达到预期 {expected!r}。",
                    "error",
                )
            )
    plot_thread_score = 100 if not status_errors else max(0, 100 - 35 * status_errors)

    timeline_markers = case.expected_state_delta.get("timeline_causal_markers", [])
    new_events = project.timeline[timeline_before:]
    summaries = [event.summary for event in new_events]
    timeline_score = 100
    if case.expected_state_delta.get("timeline_required", bool(timeline_markers)):
        if not new_events:
            timeline_score = 0
            findings.append(
                StoryQualityFinding("state_delta", "时间线没有新增章节事件。", "error")
            )
        elif timeline_markers and not any(
            all(marker in summary for marker in timeline_markers)
            for summary in summaries
        ):
            timeline_score = 50
            findings.append(
                StoryQualityFinding(
                    "state_delta",
                    f"新增时间线没有同时包含因果标记：{timeline_markers}。",
                    "error",
                )
            )

    return {
        "state_delta": round((plot_thread_score + timeline_score) / 2),
        "plot_thread_state": plot_thread_score,
        "timeline_state": timeline_score,
    }


def score_revision_effectiveness(
    *,
    original: Any | None,
    revised: Any | None,
    project: Any,
    required: dict[str, Any],
    findings: list[StoryQualityFinding],
) -> dict[str, int]:
    if not required.get("revision_required"):
        return {"revision_effectiveness": 100}
    if original is None or revised is None:
        findings.append(
            StoryQualityFinding("revision_effectiveness", "要求修订，但未执行修订流程。", "error")
        )
        return {"revision_effectiveness": 0}

    score = 100
    if revised.revision <= original.revision:
        score -= 35
        findings.append(
            StoryQualityFinding("revision_effectiveness", "修订版本号没有递增。", "error")
        )
    incomplete = [
        task for task in project.revision_tasks if task.target_chapter == revised.number and not task.completed
    ]
    if incomplete:
        score -= 35
        findings.append(
            StoryQualityFinding("revision_effectiveness", "存在未完成的修订任务。", "error")
        )
    for text in required.get("revision_must_include", []):
        if text not in revised.content:
            score -= 20
            findings.append(
                StoryQualityFinding(
                    "revision_effectiveness",
                    f"修订正文没有兑现要求文本：{text}。",
                    "error",
                )
            )
    return {"revision_effectiveness": max(0, score)}


class StoryQualityEvaluator:
    def __init__(
        self,
        *,
        workflow_mode: str = "baseline",
        judge: Any | None = None,
        llm_client: LLMClient | None = None,
    ):
        if workflow_mode not in {"baseline", "llm"}:
            raise ValueError(f"Unsupported workflow mode: {workflow_mode}")
        self.workflow_mode = workflow_mode
        self.judge = judge
        self.llm_client = llm_client

    def evaluate(self, case: StoryEvalCase) -> StoryQualityReport:
        handlers = {
            "plan_next_chapter": self._evaluate_plan_next_chapter,
            "draft_next_chapter_grounding": self._evaluate_beat_grounding,
            "revision_non_regression": self._evaluate_revision_non_regression,
            "narrative_minimal_pairs": self._evaluate_narrative_minimal_pairs,
            "harder_minimal_pairs": self._evaluate_narrative_minimal_pairs,
            "revision_quality": self._evaluate_revision_quality,
            "character_arc_consistency": self._evaluate_character_arc_consistency,
            "plot_thread_progression": self._evaluate_plot_thread_progression,
            "timeline_causality": self._evaluate_timeline_causality,
            "story_agent_structural_contract": self._evaluate_story_agent_capability,
            "story_agent_capability": self._evaluate_story_agent_capability,
        }
        handler = handlers.get(case.task)
        if handler is None:
            return StoryQualityReport(
                case_id=case.id,
                passed=False,
                total_score=0,
                scores={"unsupported_task": 0},
                rule_scores={"unsupported_task": 0},
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
            plan = self._workflow().plan_next_chapter(project)
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
                            "required_character",
                            f"章节计划缺少必需人物：{character}。",
                            "error",
                        )
                    )
            for beat in required.get("beats", []):
                if beat not in plan.beats:
                    findings.append(
                        StoryQualityFinding(
                            "required_beat",
                            f"章节计划缺少必需 beat：{beat}。",
                            "error",
                        )
                    )
            combined = f"{plan.title}\n{plan.goal}\n{' '.join(plan.beats)}"
            for text in case.forbidden.get("text", []):
                if text in combined:
                    findings.append(
                        StoryQualityFinding(
                            "forbidden_text",
                            f"章节计划提前泄露禁用信息：{text}。",
                            "error",
                        )
                    )
            return self._build_report(
                case=case,
                rule_scores={"hard_constraints": self._hard_score(findings)},
                state_scores={},
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
            workflow = self._workflow()
            workflow.plan_next_chapter(project)
            chapter = workflow.draft_next_chapter(project)
            beat = case.required.get("grounded_beat", "")
            raw_score = self._score_beat_grounding(chapter.content, beat)
            minimum = case.required.get("minimum_grounding_score", 4)
            findings: list[StoryQualityFinding] = []
            if raw_score < minimum:
                findings.append(
                    StoryQualityFinding(
                        "beat_grounding",
                        f"beat grounding 原始分 {raw_score}/5，低于 {minimum}/5。",
                        "error",
                    )
                )
            return self._build_report(
                case=case,
                rule_scores={"beat_grounding": raw_score * 20},
                state_scores={},
                findings=findings,
                observed={"content": chapter.content, "grounded_beat": beat},
                raw_scores={"beat_grounding": raw_score},
            )

    def _evaluate_revision_non_regression(
        self, case: StoryEvalCase
    ) -> StoryQualityReport:
        with tempfile.TemporaryDirectory() as tmp:
            project, workflow, chapter, revised = self._run_revision_flow(case, Path(tmp))
            findings: list[StoryQualityFinding] = []
            if revised.revision <= chapter.revision:
                findings.append(
                    StoryQualityFinding("revision_version", "修订版本没有递增。", "error")
                )
            open_threads = [
                thread.code for thread in project.plot_threads if thread.status == "open"
            ]
            for thread in case.required.get("open_plot_threads", []):
                if thread not in open_threads:
                    findings.append(
                        StoryQualityFinding(
                            "plot_thread_regression",
                            f"修订后剧情线索不再保持开放：{thread}。",
                            "error",
                        )
                    )
            known_names = {character.name for character in project.characters}
            unknown = [
                name for name in revised.referenced_characters if name not in known_names
            ]
            if unknown:
                findings.append(
                    StoryQualityFinding(
                        "unknown_character",
                        f"修订引入未知人物：{'、'.join(unknown)}。",
                        "error",
                    )
                )
            return self._build_report(
                case=case,
                rule_scores={"hard_constraints": self._hard_score(findings)},
                state_scores={},
                findings=findings,
                observed={
                    "latest_revision": revised.revision,
                    "open_plot_threads": open_threads,
                    "revision_content": revised.content,
                    "workflow": workflow.__class__.__name__,
                },
            )

    def _evaluate_narrative_minimal_pairs(
        self, case: StoryEvalCase
    ) -> StoryQualityReport:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._seed_project(case, Path(tmp))
            results = []
            for pair in case.required.get("pairs", []):
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
            total = len(results)
            correct_count = sum(1 for item in results if item["correct"])
            accuracy = round(100 * correct_count / total) if total else 0
            findings: list[StoryQualityFinding] = []
            if accuracy < case.pass_threshold:
                findings.append(
                    StoryQualityFinding(
                        "minimal_pair_accuracy",
                        f"叙事 minimal-pair 准确率为 {accuracy}%。",
                        "error",
                    )
                )
            return self._build_report(
                case=case,
                rule_scores={"minimal_pair_accuracy": accuracy},
                state_scores={},
                findings=findings,
                observed={"correct_pairs": correct_count, "total_pairs": total, "pairs": results},
            )

    def _evaluate_revision_quality(self, case: StoryEvalCase) -> StoryQualityReport:
        with tempfile.TemporaryDirectory() as tmp:
            _project, _workflow, _chapter, revised = self._run_revision_flow(
                case, Path(tmp)
            )
            score = self._score_revision_quality(revised.content)
            findings: list[StoryQualityFinding] = []
            if self._looks_like_append_only_revision(revised.content):
                findings.append(
                    StoryQualityFinding(
                        "append_only_revision",
                        "修订结果仍像追加审稿说明，没有重写成小说场景。",
                    )
                )
            minimum = case.required.get("minimum_revision_quality", 60)
            if score < minimum and not findings:
                findings.append(
                    StoryQualityFinding(
                        "revision_quality",
                        f"修订质量得分 {score}，低于最低要求 {minimum}。",
                    )
                )
            return self._build_report(
                case=case,
                rule_scores={"revision_quality": score},
                state_scores={},
                findings=findings,
                observed={"revision_content": revised.content, "latest_revision": revised.revision},
            )

    def _evaluate_character_arc_consistency(
        self, case: StoryEvalCase
    ) -> StoryQualityReport:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._seed_project(case, Path(tmp))
            workflow = self._workflow()
            workflow.plan_next_chapter(project)
            chapter = workflow.draft_next_chapter(project)
            content = chapter.content
            required_markers = case.required.get("arc_markers", [])
            forbidden_hits = [
                marker for marker in case.forbidden.get("passive_markers", []) if marker in content
            ]
            matched = [marker for marker in required_markers if marker in content]
            findings: list[StoryQualityFinding] = []
            if len(matched) < case.required.get("minimum_arc_markers", 1):
                findings.append(
                    StoryQualityFinding(
                        "character_arc_consistency",
                        "人物行动没有足够体现 goal/conflict/arc。",
                        "error",
                    )
                )
            if forbidden_hits:
                findings.append(
                    StoryQualityFinding(
                        "character_arc_consistency",
                        f"人物弧线出现被动化表达：{forbidden_hits}。",
                    )
                )
            score = round(100 * len(matched) / len(required_markers)) if required_markers else 100
            if forbidden_hits:
                score = max(0, score - 20)
            return self._build_report(
                case=case,
                rule_scores={"character_arc_consistency": score},
                state_scores={},
                findings=findings,
                observed={"matched_arc_markers": matched, "content": content},
            )

    def _evaluate_plot_thread_progression(
        self, case: StoryEvalCase
    ) -> StoryQualityReport:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._seed_project(case, Path(tmp))
            workflow = self._workflow()
            workflow.plan_next_chapter(project)
            workflow.draft_next_chapter(project)
            observed = self._plot_thread_observed(project)
            findings: list[StoryQualityFinding] = []
            for code, status in case.required.get("thread_status", {}).items():
                if observed.get(code, {}).get("status") != status:
                    findings.append(
                        StoryQualityFinding(
                            "plot_thread_progression",
                            f"{code} 没有推进到 {status} 状态。",
                            "error",
                        )
                    )
            for code, chapter_number in case.required.get("related_chapters", {}).items():
                if chapter_number not in observed.get(code, {}).get("related_chapters", []):
                    findings.append(
                        StoryQualityFinding(
                            "plot_thread_progression",
                            f"{code} 没有记录第 {chapter_number} 章推进。",
                            "error",
                        )
                    )
            return self._build_report(
                case=case,
                rule_scores={},
                state_scores={"plot_thread_progression": self._hard_score(findings)},
                findings=findings,
                observed=observed,
            )

    def _evaluate_timeline_causality(self, case: StoryEvalCase) -> StoryQualityReport:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._seed_project(case, Path(tmp))
            workflow = self._workflow()
            workflow.plan_next_chapter(project)
            workflow.draft_next_chapter(project)
            summaries = [event.summary for event in project.timeline]
            matched = [
                marker
                for marker in case.required.get("causal_markers", [])
                if any(marker in summary for summary in summaries)
            ]
            findings: list[StoryQualityFinding] = []
            if len(project.timeline) < case.required.get("minimum_events", 2):
                findings.append(
                    StoryQualityFinding(
                        "timeline_causality",
                        "时间线事件不足，无法评估章节因果链。",
                        "error",
                    )
                )
            if len(matched) < case.required.get("minimum_causal_markers", 1):
                findings.append(
                    StoryQualityFinding(
                        "timeline_causality",
                        "时间线摘要没有记录可审计的因果连接。",
                        "error",
                    )
                )
            score = 100 if not findings else 50 if summaries else 0
            return self._build_report(
                case=case,
                rule_scores={},
                state_scores={"timeline_causality": score},
                findings=findings,
                observed={"timeline_summaries": summaries, "matched_markers": matched},
            )

    def _evaluate_story_agent_capability(
        self, case: StoryEvalCase
    ) -> StoryQualityReport:
        with tempfile.TemporaryDirectory() as tmp:
            project = self._seed_project(case, Path(tmp))
            workflow = self._workflow()
            timeline_before = len(project.timeline)
            plan = workflow.plan_next_chapter(project)
            chapter = workflow.draft_next_chapter(project)
            revised = None
            if case.required.get("revision_required"):
                chapter.content = case.required.get("damaged_content", chapter.content)
                review = workflow.review_chapter(project, chapter.number)
                workflow.create_revision_tasks(project, review)
                revised = workflow.revise_chapter(project, chapter.number)

            findings: list[StoryQualityFinding] = []
            contract = chapter.narrative_contract or plan.narrative_contract
            rule_scores = score_contract_rules(contract, case.required, findings)
            text_score = self._score_text_payoff(chapter.content, contract, case, findings)
            rule_scores["text_payoff"] = text_score
            state_scores = score_state_delta(
                project=project,
                case=case,
                timeline_before=timeline_before,
                findings=findings,
            )
            revision_scores = score_revision_effectiveness(
                original=chapter,
                revised=revised,
                project=project,
                required=case.required,
                findings=findings,
            )
            state_scores.update(revision_scores)

            observed = {
                "workflow": self.workflow_mode,
                "source_dataset": case.required.get("source_dataset"),
                "template": case.required.get("template", {}),
                "plan_contract": plan.narrative_contract,
                "chapter_contract": chapter.narrative_contract,
                "content": chapter.content,
                "revised_content": getattr(revised, "content", None),
                "plot_threads": self._plot_thread_observed(project),
                "timeline": [event.summary for event in project.timeline],
            }
            judge_scores, judge_observations = self._apply_judge(case, observed, findings)
            return self._build_report(
                case=case,
                rule_scores=rule_scores,
                state_scores=state_scores,
                judge_scores=judge_scores,
                findings=findings,
                observed=observed,
                judge_observations=judge_observations,
            )

    def _run_revision_flow(self, case: StoryEvalCase, root: Path):
        project = self._seed_project(case, root)
        workflow = self._workflow()
        workflow.plan_next_chapter(project)
        chapter = workflow.draft_next_chapter(project)
        chapter.content = case.required.get("damaged_content", chapter.content)
        review = workflow.review_chapter(project, chapter.number)
        workflow.create_revision_tasks(project, review)
        revised = workflow.revise_chapter(project, chapter.number)
        return project, workflow, chapter, revised

    def _seed_project(self, case: StoryEvalCase, root: Path):
        request = NovelRequest(**case.request)
        return NovelWorkflow().run_seed_project(request, root)

    def _workflow(self):
        if self.workflow_mode == "baseline":
            return NovelWorkflow()
        return LLMNovelWorkflow(self.llm_client or OpenAICompatibleClient())

    def _score_text_payoff(
        self,
        content: str,
        contract: dict[str, Any],
        case: StoryEvalCase,
        findings: list[StoryQualityFinding],
    ) -> int:
        required_texts = list(case.required.get("text_must_include", []))
        for item in _as_list(contract.get("character_choice_chain")):
            if isinstance(item, dict):
                for field_name in ("decision", "choice", "cost", "consequence"):
                    value = item.get(field_name)
                    if isinstance(value, str) and value and len(value) <= 24:
                        required_texts.append(value)
        required_texts = list(dict.fromkeys(required_texts))
        if not required_texts:
            return 100 if content else 0
        hits = [text for text in required_texts if text in content]
        score = round(100 * len(hits) / len(required_texts))
        if score < case.required.get("text_payoff_minimum", 60):
            missing = [text for text in required_texts if text not in content]
            findings.append(
                StoryQualityFinding(
                    "text_payoff",
                    f"正文没有兑现结构链中的具体内容：{missing[:5]}。",
                    "error",
                )
            )
        return score

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
        support = sum(1 for token in self._statement_tokens(statement) if token in corpus)
        support -= 2 * sum(1 for marker in self._negation_markers() if marker in statement)
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
            "主角",
            "引路者",
            "记忆",
            "震颤",
            "异常",
            "光接触",
            "退变",
            "倒退",
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
            "fully explained",
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
            "决定",
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
                    category,
                    f"{message} observed={observed!r}, expected={expected!r}",
                    "error",
                )
            )

    def _hard_score(self, findings: list[StoryQualityFinding]) -> int:
        errors = sum(1 for item in findings if item.severity == "error")
        return 100 if errors == 0 else max(0, 100 - 25 * errors)

    def _build_report(
        self,
        *,
        case: StoryEvalCase,
        rule_scores: dict[str, int],
        state_scores: dict[str, int],
        findings: list[StoryQualityFinding],
        observed: dict[str, Any],
        raw_scores: dict[str, Any] | None = None,
        judge_scores: dict[str, int] | None = None,
        judge_observations: dict[str, Any] | None = None,
    ) -> StoryQualityReport:
        bounded_rules = self._bound_scores(rule_scores)
        bounded_state = self._bound_scores(state_scores)
        bounded_judge = self._bound_scores(judge_scores or {})
        combined_scores = {**bounded_rules, **bounded_state, **bounded_judge}
        total_inputs = {**bounded_rules, **bounded_state}
        if not total_inputs:
            total_inputs = combined_scores
        total = self._weighted_score(total_inputs, case.rubric)
        return StoryQualityReport(
            case_id=case.id,
            passed=not any(item.severity == "error" for item in findings)
            and total >= case.pass_threshold,
            total_score=max(0, min(100, total)),
            scores=combined_scores,
            findings=findings,
            observed=observed,
            rule_scores=bounded_rules,
            state_scores=bounded_state,
            judge_scores=bounded_judge,
            raw_scores=raw_scores or {},
            judge_observations=judge_observations or {},
        )

    def _apply_judge(
        self,
        case: StoryEvalCase,
        observed: dict[str, Any],
        findings: list[StoryQualityFinding],
    ) -> tuple[dict[str, int], dict[str, Any]]:
        if self.judge is None:
            return {}, {}
        try:
            results = self.judge.judge(case=case, observed=observed)
        except ValueError as exc:
            findings.append(
                StoryQualityFinding("judge_schema", f"Judge 结构化输出无效：{exc}", "error")
            )
            return {}, {"schema_error": str(exc)}
        except Exception as exc:
            findings.append(
                StoryQualityFinding(
                    "judge_runtime",
                    f"Judge 调用失败：{exc.__class__.__name__}: {exc}",
                    "error",
                )
            )
            return {}, {"runtime_error": f"{exc.__class__.__name__}: {exc}"}

        scores: dict[str, int] = {}
        observations: dict[str, Any] = {}
        for result in results:
            missing = [
                name
                for name in (
                    "dimension",
                    "score",
                    "evidence",
                    "failure_reason",
                    "revision_advice",
                )
                if not hasattr(result, name)
            ]
            if missing:
                findings.append(
                    StoryQualityFinding(
                        "judge_schema",
                        f"Judge result 缺少字段：{', '.join(missing)}。",
                        "error",
                    )
                )
                continue
            score = max(0, min(100, int(result.score)))
            scores[str(result.dimension)] = score
            observations[str(result.dimension)] = {
                "evidence": str(result.evidence),
                "failure_reason": str(result.failure_reason),
                "revision_advice": str(result.revision_advice),
            }
            if score >= 80 and not str(result.evidence).strip():
                findings.append(
                    StoryQualityFinding(
                        "judge_missing_evidence",
                        f"{result.dimension} Judge 高分缺少 evidence。",
                        "error",
                    )
                )
        return scores, observations

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

    def _bound_scores(self, scores: dict[str, int]) -> dict[str, int]:
        return {key: max(0, min(100, int(value))) for key, value in scores.items()}

    def _plot_thread_observed(self, project) -> dict[str, Any]:
        return {
            thread.code: {
                "status": thread.status,
                "related_chapters": thread.related_chapters,
                "payoff": thread.payoff,
            }
            for thread in project.plot_threads
        }

    def _report_to_dict(self, report: StoryQualityReport) -> dict[str, Any]:
        return asdict(report)

    def _reports_to_markdown(self, reports: list[StoryQualityReport]) -> str:
        lines = ["# 小说 Agent 质量评测结果", ""]
        for report in reports:
            status = "通过" if report.passed else "未通过"
            lines.extend(
                [
                    f"## {report.case_id}: {status}",
                    "",
                    f"- 总分：{report.total_score}/100",
                    f"- 规则层分数：{report.rule_scores}",
                    f"- 状态变化层分数：{report.state_scores}",
                    f"- Judge 层分数：{report.judge_scores}",
                    f"- 原始指标：{report.raw_scores}",
                ]
            )
            if report.judge_observations:
                lines.append("- Judge 证据与建议：")
                for dimension, item in report.judge_observations.items():
                    if dimension == "schema_error":
                        lines.append(f"  - schema_error：{item}")
                        continue
                    if dimension == "runtime_error":
                        lines.append(f"  - runtime_error：{item}")
                        continue
                    lines.append(
                        "  - "
                        f"{dimension}：证据={item.get('evidence', '')}；"
                        f"失败原因={item.get('failure_reason', '')}；"
                        f"修订建议={item.get('revision_advice', '')}"
                    )
            if report.findings:
                lines.append("- 失败原因：")
                for finding in report.findings:
                    lines.append(
                        f"  - [{finding.severity}] {finding.category}: {finding.message}"
                    )
            lines.append("")
        return "\n".join(lines)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _contract_value(item: dict[str, Any], field_name: str) -> Any:
    for key in CHOICE_ALIASES.get(field_name, (field_name,)):
        value = item.get(key)
        if value:
            return value
    return None
