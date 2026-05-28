from __future__ import annotations

from pathlib import Path

from .models import (
    ChapterDraft,
    ChapterPlan,
    CharacterCard,
    NovelRequest,
    OutlineItem,
    PlotThread,
    ReviewReport,
    RevisionTask,
    StoryBible,
    TimelineEvent,
    WorldRule,
)
from .project import NovelProject
from .review import ContinuityChecker


class NovelWorkflow:
    """本地 deterministic baseline，只保留通用结构，不内置旧项目人物。"""

    def run_seed_project(self, request: NovelRequest, root: Path) -> NovelProject:
        project = NovelProject.create(
            root=root,
            title=request.title,
            premise=request.premise,
            genre=request.genre,
            style=request.style,
        )
        project.story_bible = self._build_story_bible(request)
        project.characters = self._build_characters(request)
        project.volume_outline = self._build_volume_outline(request)
        project.chapter_outlines = self._build_chapter_outlines(request)
        project.world_rules = self._build_world_rules(request)
        project.plot_threads = self._build_plot_threads(request)
        project.chapters = [self._build_first_chapter(request, project.characters)]
        project.timeline = [
            TimelineEvent(
                chapter_number=1,
                title=project.chapters[0].title,
                summary=project.chapters[0].summary,
                characters=project.chapters[0].referenced_characters,
            )
        ]
        project.reviews = [ContinuityChecker().review_chapter(project, project.chapters[0])]
        project.save()
        return project

    def plan_next_chapter(self, project: NovelProject) -> ChapterPlan:
        next_number = self._next_chapter_number(project)
        for plan in project.chapter_plans:
            if plan.number == next_number:
                return plan
        outline = self._outline_for_chapter(project, next_number)
        required_characters = self._required_characters_for_outline(project, outline)
        plot_threads = [thread.code for thread in project.plot_threads if thread.status == "open"]
        plan = ChapterPlan(
            number=next_number,
            title=outline.title,
            goal=outline.summary,
            scenes=[f"场景：{beat}" for beat in outline.beats],
            beats=outline.beats,
            required_characters=required_characters,
            plot_threads=plot_threads[:2],
        )
        project.chapter_plans.append(plan)
        project.save()
        return plan

    def draft_next_chapter(self, project: NovelProject) -> ChapterDraft:
        plan = self._next_undrafted_plan(project)
        chapter = ChapterDraft(
            number=plan.number,
            title=plan.title,
            summary=plan.goal,
            scenes=plan.scenes,
            content=self._draft_scene_from_plan(plan),
            referenced_characters=plan.required_characters,
            source_plan_number=plan.number,
        )
        project.chapters.append(chapter)
        project.timeline.append(
            TimelineEvent(
                chapter_number=chapter.number,
                title=chapter.title,
                summary=chapter.summary,
                characters=chapter.referenced_characters,
            )
        )
        project.save()
        return chapter

    def review_chapter(self, project: NovelProject, chapter_number: int) -> ReviewReport:
        chapter = self._latest_chapter(project, chapter_number)
        report = ContinuityChecker().review_chapter(project, chapter)
        project.reviews.append(report)
        project.save()
        return report

    def create_revision_tasks(
        self, project: NovelProject, report: ReviewReport
    ) -> list[RevisionTask]:
        target_chapter = self._chapter_number_from_target(report.target)
        tasks: list[RevisionTask] = []
        for issue in report.issues:
            task = RevisionTask(
                target_chapter=target_chapter,
                category=issue.category,
                instruction=issue.message,
                severity=issue.severity,
            )
            project.revision_tasks.append(task)
            tasks.append(task)
        project.save()
        return tasks

    def revise_chapter(self, project: NovelProject, chapter_number: int) -> ChapterDraft:
        original = self._latest_chapter(project, chapter_number)
        pending_tasks = [
            task
            for task in project.revision_tasks
            if task.target_chapter == chapter_number and not task.completed
        ]
        if not pending_tasks:
            report = self.review_chapter(project, chapter_number)
            pending_tasks = self.create_revision_tasks(project, report)
        plan = self._plan_for_chapter(project, chapter_number)
        revised = ChapterDraft(
            number=original.number,
            title=original.title,
            summary=original.summary,
            scenes=original.scenes,
            content=self._rewrite_scene_for_revision(original, plan, pending_tasks),
            referenced_characters=original.referenced_characters,
            revision=original.revision + 1,
            source_plan_number=original.source_plan_number,
        )
        for task in pending_tasks:
            task.completed = True
        project.chapters.append(revised)
        project.reviews.append(ContinuityChecker().review_chapter(project, revised))
        project.save()
        return revised

    def export_manuscript(self, project: NovelProject) -> str:
        latest_by_number: dict[int, ChapterDraft] = {}
        for chapter in project.chapters:
            current = latest_by_number.get(chapter.number)
            if current is None or chapter.revision > current.revision:
                latest_by_number[chapter.number] = chapter
        lines = [f"# {project.title}", ""]
        for number in sorted(latest_by_number):
            chapter = latest_by_number[number]
            lines.extend([f"## 第 {chapter.number} 章：{chapter.title}", "", chapter.content, ""])
        return "\n".join(lines).rstrip() + "\n"

    def _build_story_bible(self, request: NovelRequest) -> StoryBible:
        return StoryBible(
            logline=f"{request.title}: {request.premise}",
            themes=["危险开场", "真相倒推", "从逃避到主动选择"],
            rules=[
                "重大揭示必须由场景证据铺垫。",
                "人物选择必须符合目标、冲突和弧线。",
                "每章至少改变一组关系、线索或时间线状态。",
            ],
            style_notes=[
                f"主要文风：{request.style}。",
                f"题材期待：{request.genre}。",
                "优先写具体场景行动，避免抽象说明堆叠。",
            ],
        )

    def _build_characters(self, request: NovelRequest) -> list[CharacterCard]:
        return [
            CharacterCard(
                name="主角",
                role="视角人物",
                goal="理解核心设定造成的危险，并活过第一轮选择。",
                conflict="害怕开启自己的人生，因此习惯把决定推迟。",
                arc="从不敢开启人生，走向主动接受别人给予的感情。",
            ),
            CharacterCard(
                name="引路者",
                role="情感与真相的触发者",
                goal="让主角看见被隐藏的事实。",
                conflict="越靠近主角，越可能把危险带给主角。",
                arc="从远处提醒变成愿意被主角接受的人。",
            ),
            CharacterCard(
                name="守门者",
                role="阻止真相扩散的人",
                goal="维持现有秩序和安全版本。",
                conflict="保护秩序的行为会加速危险显形。",
                arc="从秩序代表变成危险机制的证明。",
            ),
        ]

    def _build_volume_outline(self, request: NovelRequest) -> list[OutlineItem]:
        return [
            OutlineItem(
                title="第一卷：倒着开始",
                summary="故事从最危险处开场，再倒推危险为何发生。",
                beats=["危险现场", "错误安全感", "第一次选择"],
            ),
            OutlineItem(
                title="第二卷：光接触之后",
                summary="人物发现远距离光接触和文明退变之间的因果。",
                beats=["光的证据", "关系改变", "无法回头"],
            ),
            OutlineItem(
                title="第三卷：接受感情",
                summary="主角必须在文明返退中主动接受他人的感情。",
                beats=["最终倒转", "主动选择", "新的起点"],
            ),
        ]

    def _build_chapter_outlines(self, request: NovelRequest) -> list[OutlineItem]:
        return [
            OutlineItem(
                title="第一章：最危险的一刻",
                summary="主角在倒序危险现场第一次看见核心设定。",
                beats=["危险开场", "核心异常", "不再逃避"],
            ),
            OutlineItem(
                title="第二章：光的回信",
                summary="远距离光接触留下证据，文明退变开始显形。",
                beats=["光接触证据", "信任破裂", "主动靠近"],
            ),
            OutlineItem(
                title="第三章：倒退的城市",
                summary="人物关系和世界规则同时发生不可逆变化。",
                beats=["城市返退", "情感压力", "危险选择"],
            ),
        ]

    def _build_world_rules(self, request: NovelRequest) -> list[WorldRule]:
        return [
            WorldRule(code="WR-001", description=request.premise, source="用户设定"),
            WorldRule(
                code="WR-002",
                description="每次重大揭示都需要可回溯的场景证据。",
                source="故事规则",
            ),
        ]

    def _build_plot_threads(self, request: NovelRequest) -> list[PlotThread]:
        return [
            PlotThread(
                code="PT-001",
                title="核心设定的真实原因",
                status="open",
                related_chapters=[1],
                payoff="解释核心设定如何改变人物和文明的命运。",
            )
        ]

    def _build_first_chapter(
        self, request: NovelRequest, characters: list[CharacterCard]
    ) -> ChapterDraft:
        protagonist = characters[0].name
        guide = characters[1].name
        content = (
            f"{protagonist}在最危险的一刻醒来，周围的一切都像熟悉世界的倒影。"
            f"街道、窗光、人的呼吸都与地球相似，却正按相反的方向退回某个起点。"
            f"他试图把这一切解释成普通事故，但{request.premise}"
            f"{guide}留下的信号迫使他承认：安全只是延迟选择的借口。"
            f"他第一次没有转身离开，而是把那道信号收进掌心，决定继续走下去。"
        )
        return ChapterDraft(
            number=1,
            title="最危险的一刻",
            summary="主角在倒序危险现场遭遇核心设定，并第一次停止逃避。",
            scenes=["危险开场", "核心异常", "第一次主动选择"],
            content=content,
            referenced_characters=[protagonist, guide],
        )

    def _next_chapter_number(self, project: NovelProject) -> int:
        drafted_numbers = [chapter.number for chapter in project.chapters]
        return max(drafted_numbers, default=0) + 1

    def _outline_for_chapter(self, project: NovelProject, number: int) -> OutlineItem:
        index = number - 1
        if index < len(project.chapter_outlines):
            return project.chapter_outlines[index]
        return OutlineItem(
            title=f"第{number}章：新的压力",
            summary="已有线索带来新的行动压力。",
            beats=["后果显现", "关系变化", "新的选择"],
        )

    def _required_characters_for_outline(
        self, project: NovelProject, outline: OutlineItem
    ) -> list[str]:
        names = [character.name for character in project.characters]
        required = names[:2]
        required.extend(
            name
            for name in names
            if name not in required and (name in outline.title or name in outline.summary)
        )
        return required

    def _next_undrafted_plan(self, project: NovelProject) -> ChapterPlan:
        drafted_numbers = {chapter.number for chapter in project.chapters}
        for plan in sorted(project.chapter_plans, key=lambda item: item.number):
            if plan.number not in drafted_numbers:
                return plan
        return self.plan_next_chapter(project)

    def _draft_scene_from_plan(self, plan: ChapterPlan) -> str:
        protagonist = plan.required_characters[0] if plan.required_characters else "主角"
        witness = plan.required_characters[1] if len(plan.required_characters) > 1 else protagonist
        thread = plan.plot_threads[0] if plan.plot_threads else "主线"
        beats = "、".join(plan.beats)
        return (
            f"{protagonist}在新的场景里重新确认了{thread}的证据。"
            f"{witness}没有替他选择，只把能够被验证的细节递到他面前。"
            f"这一章推进的 beat 是：{beats}。"
            f"{protagonist}因此必须决定继续逃避，还是主动承担关系和真相带来的后果。"
        )

    def _plan_for_chapter(
        self, project: NovelProject, chapter_number: int
    ) -> ChapterPlan | None:
        for plan in project.chapter_plans:
            if plan.number == chapter_number:
                return plan
        return None

    def _rewrite_scene_for_revision(
        self,
        original: ChapterDraft,
        plan: ChapterPlan | None,
        pending_tasks: list[RevisionTask],
    ) -> str:
        if plan is None:
            return original.content
        rewritten = self._draft_scene_from_plan(plan)
        if pending_tasks:
            task_categories = "、".join(sorted({task.category for task in pending_tasks}))
            return f"{rewritten}这一次修订针对{task_categories}重排场景，让缺失信息进入人物行动。"
        return rewritten

    def _latest_chapter(self, project: NovelProject, chapter_number: int) -> ChapterDraft:
        matches = [chapter for chapter in project.chapters if chapter.number == chapter_number]
        if not matches:
            raise ValueError(f"找不到第 {chapter_number} 章。")
        return max(matches, key=lambda chapter: chapter.revision)

    def _chapter_number_from_target(self, target: str) -> int:
        prefix = "chapter:"
        if not target.startswith(prefix):
            raise ValueError(f"无法识别审稿目标：{target}")
        return int(target.removeprefix(prefix))
