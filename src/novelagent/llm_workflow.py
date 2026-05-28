from __future__ import annotations

from typing import Any

from .llm import LLMClient
from .models import ChapterDraft, ChapterPlan, ReviewIssue, ReviewReport, RevisionTask
from .project import NovelProject


SYSTEM_PROMPT = """你是 NovelAgent 的长篇中文小说写作大脑。
你必须根据项目状态进行真实构思，而不是复述模板。
你的输出必须是合法 JSON，且必须包含人物选择链、伏笔推进链、时间线因果链等可审计结构。
正文可以有文学表达，但结构字段必须明确、可检查、可复现。"""


class LLMNovelWorkflow:
    def __init__(self, client: LLMClient):
        self.client = client

    def plan_next_chapter(self, project: NovelProject) -> ChapterPlan:
        next_number = max([chapter.number for chapter in project.chapters], default=0) + 1
        for plan in project.chapter_plans:
            if plan.number == next_number:
                return plan

        payload = self._project_payload(project, "plan_next_chapter")
        payload["next_chapter_number"] = next_number
        payload["requirements"] = {
            "language": "中文",
            "must_return": [
                "number",
                "title",
                "goal",
                "scenes",
                "beats",
                "required_characters",
                "plot_threads",
                "narrative_contract",
            ],
            "narrative_contract": [
                "character_choice_chain",
                "plot_thread_progression",
                "timeline_causality",
            ],
        }
        result = self.client.generate_json(
            system_prompt=SYSTEM_PROMPT,
            user_payload=payload,
        )
        plan = ChapterPlan(
            number=int(result.get("number", next_number)),
            title=str(result.get("title", f"第{next_number}章")),
            goal=str(result.get("goal", "")),
            scenes=list(result.get("scenes", [])),
            beats=list(result.get("beats", [])),
            required_characters=list(result.get("required_characters", [])),
            plot_threads=list(result.get("plot_threads", [])),
            narrative_contract=dict(result.get("narrative_contract", {})),
        )
        project.chapter_plans.append(plan)
        self._apply_plan_state(project, plan)
        project.save()
        return plan

    def draft_next_chapter(self, project: NovelProject) -> ChapterDraft:
        plan = self._next_undrafted_plan(project)
        payload = self._project_payload(project, "draft_chapter")
        payload["plan"] = self._plan_payload(plan)
        payload["requirements"] = {
            "language": "中文",
            "must_return": [
                "summary",
                "content",
                "referenced_characters",
                "narrative_contract",
            ],
            "content_rule": "正文必须兑现 plan.narrative_contract，不允许只写提纲说明。",
        }
        result = self.client.generate_json(
            system_prompt=SYSTEM_PROMPT,
            user_payload=payload,
        )
        chapter = ChapterDraft(
            number=plan.number,
            title=plan.title,
            summary=str(result.get("summary", plan.goal)),
            scenes=plan.scenes,
            content=str(result.get("content", "")),
            referenced_characters=list(result.get("referenced_characters", plan.required_characters)),
            source_plan_number=plan.number,
            narrative_contract=dict(result.get("narrative_contract", plan.narrative_contract)),
        )
        project.chapters.append(chapter)
        project.timeline.append(
            self._timeline_event(
                chapter_number=chapter.number,
                title=chapter.title,
                summary=chapter.summary,
                characters=chapter.referenced_characters,
                contract=chapter.narrative_contract,
            )
        )
        project.save()
        return chapter

    def review_chapter(self, project: NovelProject, chapter_number: int) -> ReviewReport:
        chapter = self._latest_chapter(project, chapter_number)
        payload = self._project_payload(project, "review_chapter")
        payload["chapter"] = self._chapter_payload(chapter)
        payload["requirements"] = {
            "language": "中文",
            "must_return": ["passed", "summary", "issues"],
            "issue_fields": ["category", "message", "severity"],
        }
        result = self.client.generate_json(
            system_prompt=SYSTEM_PROMPT,
            user_payload=payload,
        )
        issues = [
            ReviewIssue(
                category=str(item.get("category", "llm_review")),
                message=str(item.get("message", "")),
                severity=str(item.get("severity", "warning")),
            )
            for item in result.get("issues", [])
        ]
        report = ReviewReport(
            target=f"chapter:{chapter_number}",
            passed=bool(result.get("passed", not issues)),
            summary=str(result.get("summary", "")),
            issues=issues,
        )
        project.reviews.append(report)
        project.save()
        return report

    def create_revision_tasks(
        self, project: NovelProject, report: ReviewReport
    ) -> list[RevisionTask]:
        target = int(report.target.removeprefix("chapter:"))
        tasks = [
            RevisionTask(
                target_chapter=target,
                category=issue.category,
                instruction=issue.message,
                severity=issue.severity,
            )
            for issue in report.issues
        ]
        project.revision_tasks.extend(tasks)
        project.save()
        return tasks

    def revise_chapter(self, project: NovelProject, chapter_number: int) -> ChapterDraft:
        chapter = self._latest_chapter(project, chapter_number)
        pending_tasks = [
            task
            for task in project.revision_tasks
            if task.target_chapter == chapter_number and not task.completed
        ]
        payload = self._project_payload(project, "revise_chapter")
        payload["chapter"] = self._chapter_payload(chapter)
        payload["revision_tasks"] = [task.__dict__ for task in pending_tasks]
        payload["requirements"] = {
            "language": "中文",
            "must_return": [
                "summary",
                "content",
                "referenced_characters",
                "narrative_contract",
            ],
            "content_rule": "必须重写正文并解决 revision_tasks，不允许只追加审稿说明。",
        }
        result = self.client.generate_json(
            system_prompt=SYSTEM_PROMPT,
            user_payload=payload,
        )
        revised = ChapterDraft(
            number=chapter.number,
            title=chapter.title,
            summary=str(result.get("summary", chapter.summary)),
            scenes=chapter.scenes,
            content=str(result.get("content", chapter.content)),
            referenced_characters=list(result.get("referenced_characters", chapter.referenced_characters)),
            revision=chapter.revision + 1,
            source_plan_number=chapter.source_plan_number,
            narrative_contract=dict(result.get("narrative_contract", chapter.narrative_contract)),
        )
        for task in pending_tasks:
            task.completed = True
        project.chapters.append(revised)
        project.save()
        return revised

    def _next_undrafted_plan(self, project: NovelProject) -> ChapterPlan:
        drafted = {chapter.number for chapter in project.chapters}
        for plan in sorted(project.chapter_plans, key=lambda item: item.number):
            if plan.number not in drafted:
                return plan
        return self.plan_next_chapter(project)

    def _latest_chapter(self, project: NovelProject, chapter_number: int) -> ChapterDraft:
        matches = [chapter for chapter in project.chapters if chapter.number == chapter_number]
        if not matches:
            raise ValueError(f"找不到第 {chapter_number} 章。")
        return max(matches, key=lambda chapter: chapter.revision)

    def _project_payload(self, project: NovelProject, task: str) -> dict[str, Any]:
        return {
            "task": task,
            "project": {
                "title": project.title,
                "premise": project.premise,
                "genre": project.genre,
                "style": project.style,
                "story_bible": project.story_bible.__dict__,
                "characters": [item.__dict__ for item in project.characters],
                "world_rules": [item.__dict__ for item in project.world_rules],
                "plot_threads": [item.__dict__ for item in project.plot_threads],
                "timeline": [item.__dict__ for item in project.timeline],
                "recent_chapters": [self._chapter_payload(item) for item in project.chapters[-3:]],
            },
        }

    def _plan_payload(self, plan: ChapterPlan) -> dict[str, Any]:
        return {
            "number": plan.number,
            "title": plan.title,
            "goal": plan.goal,
            "scenes": plan.scenes,
            "beats": plan.beats,
            "required_characters": plan.required_characters,
            "plot_threads": plan.plot_threads,
            "narrative_contract": plan.narrative_contract,
        }

    def _chapter_payload(self, chapter: ChapterDraft) -> dict[str, Any]:
        return {
            "number": chapter.number,
            "title": chapter.title,
            "summary": chapter.summary,
            "scenes": chapter.scenes,
            "content": chapter.content,
            "referenced_characters": chapter.referenced_characters,
            "revision": chapter.revision,
            "source_plan_number": chapter.source_plan_number,
            "narrative_contract": chapter.narrative_contract,
        }

    def _apply_plan_state(self, project: NovelProject, plan: ChapterPlan) -> None:
        for progression in plan.narrative_contract.get("plot_thread_progression", []):
            if not isinstance(progression, dict):
                continue
            code = progression.get("thread_code")
            for thread in project.plot_threads:
                if thread.code == code:
                    thread.status = self._progression_status(progression, thread.status)
                    if plan.number not in thread.related_chapters:
                        thread.related_chapters.append(plan.number)

    def _progression_status(self, progression: dict[str, Any], fallback: str) -> str:
        explicit = progression.get("new_status") or progression.get("status")
        if explicit:
            return str(explicit)
        if any(
            progression.get(key)
            for key in ("current_state", "evidence", "next_step_hint", "new_question")
        ):
            return "developed"
        return fallback

    def _timeline_event(
        self,
        *,
        chapter_number: int,
        title: str,
        summary: str,
        characters: list[str],
        contract: dict[str, Any],
    ):
        from .models import TimelineEvent

        causal = [
            item for item in contract.get("timeline_causality", []) if isinstance(item, dict)
        ]
        if causal:
            first = causal[0]
            summary = f"因为{first.get('cause', '')}，所以{first.get('effect', summary)}"
        return TimelineEvent(
            chapter_number=chapter_number,
            title=title,
            summary=summary,
            characters=characters,
        )
