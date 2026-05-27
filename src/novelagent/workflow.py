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
        project.plot_threads = self._build_plot_threads()
        project.chapters = [self._build_first_chapter(request, project.characters)]
        project.timeline = [
            TimelineEvent(
                chapter_number=1,
                title=project.chapters[0].title,
                summary=project.chapters[0].summary,
                characters=project.chapters[0].referenced_characters,
            )
        ]
        project.reviews = [
            ContinuityChecker().review_chapter(project, project.chapters[0])
        ]
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
        content = self._draft_scene_from_plan(plan)
        chapter = ChapterDraft(
            number=plan.number,
            title=plan.title,
            summary=plan.goal,
            scenes=plan.scenes,
            content=content,
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
        revised_content = self._rewrite_scene_for_revision(original, plan, pending_tasks)
        revised = ChapterDraft(
            number=original.number,
            title=original.title,
            summary=original.summary,
            scenes=original.scenes,
            content=revised_content,
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
            lines.extend(
                [
                    f"## 第 {chapter.number} 章：{chapter.title}",
                    "",
                    chapter.content,
                    "",
                ]
            )
        return "\n".join(lines).rstrip() + "\n"

    def _build_story_bible(self, request: NovelRequest) -> StoryBible:
        return StoryBible(
            logline=f"{request.title}: {request.premise}",
            themes=[
                "压力下的身份认同",
                "隐秘知识带来的代价",
                "真相显现后的选择",
            ],
            rules=[
                "重大揭示必须由前文场景证据铺垫。",
                "人物选择必须符合已声明的目标与内在冲突。",
                "每一章至少改变一组人物关系或线索状态。",
            ],
            style_notes=[
                f"主要文风：{request.style}。",
                f"题材期待：{request.genre}。",
                "优先使用具体场景行动，避免抽象说明堆叠。",
            ],
        )

    def _build_characters(self, request: NovelRequest) -> list[CharacterCard]:
        return [
            CharacterCard(
                name="林澈",
                role="主角",
                goal="理解核心设定背后的谜团。",
                conflict="职业习惯让他难以面对情感层面的真相。",
                arc="从冷静旁观者转变为主动承担者。",
            ),
            CharacterCard(
                name="米拉",
                role="催化者",
                goal="迫使主角正视第一个不可能的线索。",
                conflict="她知道更多真相，却无法安全地全部说出。",
                arc="从戒备的传信者转变为可信赖的同盟。",
            ),
            CharacterCard(
                name="乔主任",
                role="对抗型导师",
                goal="维持官方版本的完整性。",
                conflict="保护秩序的同时可能摧毁真相。",
                arc="从制度压力的代表转变为矛盾暴露的核心。",
            ),
        ]

    def _build_volume_outline(self, request: NovelRequest) -> list[OutlineItem]:
        return [
            OutlineItem(
                title="第一卷：最初的信号",
                summary="主角以具体事件的形式遭遇核心设定带来的扰动。",
                beats=["开场异常", "第一位同盟", "错误解释"],
            ),
            OutlineItem(
                title="第二卷：隐藏的系统",
                summary="主要人物发现异常背后更深层的结构。",
                beats=["规则显现", "信任破裂", "无法回头的选择"],
            ),
            OutlineItem(
                title="第三卷：真相的代价",
                summary="主角通过牺牲解决核心谜团。",
                beats=["最终反转", "压力下的选择", "新的平衡"],
            ),
        ]

    def _build_chapter_outlines(self, request: NovelRequest) -> list[OutlineItem]:
        return [
            OutlineItem(
                title="第一章：不该存在的记录",
                summary="林澈记录下一个本不该存在的细节。",
                beats=["日常秩序", "异常线索", "私下怀疑"],
            ),
            OutlineItem(
                title="第二章：米拉的警告",
                summary="米拉挑战了看似安全的解释。",
                beats=["第二位见证者", "矛盾记忆", "规则浮现"],
            ),
            OutlineItem(
                title="第三章：乔主任的档案",
                summary="制度压力重新定义了第一次发现。",
                beats=["官方否认", "隐藏档案", "危险选择"],
            ),
        ]

    def _build_world_rules(self, request: NovelRequest) -> list[WorldRule]:
        return [
            WorldRule(
                code="WR-001",
                description=f"核心异常必须围绕设定展开：{request.premise}",
                source="核心设定",
            ),
            WorldRule(
                code="WR-002",
                description="每次重大揭示都需要先出现可回溯的场景证据。",
                source="故事圣经",
            ),
        ]

    def _build_plot_threads(self) -> list[PlotThread]:
        return [
            PlotThread(
                code="PT-001",
                title="核心异常",
                status="open",
                related_chapters=[1],
                payoff="第三卷解释异常的真实来源。",
            )
        ]

    def _build_first_chapter(
        self, request: NovelRequest, characters: list[CharacterCard]
    ) -> ChapterDraft:
        protagonist = characters[0].name
        catalyst = characters[1].name
        title = "不该存在的记录"
        content = (
            f"{protagonist}在一场近乎日常的清晨里开始工作，仍然信任"
            f"{request.genre}世界中那些看似可靠的工具。这个病例原本毫无危险，"
            f"直到一个细节呼应了故事的核心设定：{request.premise}"
            f"{catalyst}在他找到合理解释前赶到，并带来一句警告，"
            "让第一条线索显得像是被人刻意留下。"
        )
        return ChapterDraft(
            number=1,
            title=title,
            summary="主角遭遇第一个异常，并失去日常秩序带来的安全感。",
            scenes=["日常开场", "异常线索", "催化者警告"],
            content=content,
            referenced_characters=[protagonist, catalyst],
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
            summary="既有线索带来新的行动压力。",
            beats=["后果显现", "关系变化", "新的选择"],
        )

    def _required_characters_for_outline(
        self, project: NovelProject, outline: OutlineItem
    ) -> list[str]:
        names = [character.name for character in project.characters]
        required = []
        if names:
            required.append(names[0])
        required.extend(
            name
            for name in names
            if name not in required and (name in outline.title or name in outline.summary)
        )
        if len(names) > 1 and names[1] not in required:
            required.append(names[1])
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
        beat_sentences = self._beat_scene_sentences(plan.beats, protagonist, witness)
        return (
            f"{protagonist}在走廊尽头停下时，{witness}把一份扫描记录递到他手里。"
            f"纸页上的时间戳没有错，震颤曲线却像复写了另一段记忆，"
            f"让{thread}第一次从异常变成可触碰的证据。"
            f"{''.join(beat_sentences)}"
            f"{witness}压低声音说，安全的解释只能保护他们到今晚，"
            f"{protagonist}因此必须决定是上报档案，还是先追查记录背后的规则。"
        )

    def _beat_scene_sentences(
        self, beats: list[str], protagonist: str, witness: str
    ) -> list[str]:
        sentences: list[str] = []
        for beat in beats:
            if beat == "第二位见证者":
                sentences.append(
                    f"第二位见证者不是旁观者，{witness}说自己也看见过同样的颤动记录。"
                )
            elif beat == "矛盾记忆":
                sentences.append(
                    f"{protagonist}翻到病历背面，看见矛盾记忆留下的痕迹：病人写下的童年地址与他的记忆互相冲突。"
                )
            elif beat == "规则浮现":
                sentences.append(
                    "规则浮现得很慢：两份扫描都在同一分钟出现断层，像是在提示震颤只会带回被删除的短期记忆。"
                )
            else:
                sentences.append(f"{beat}不再停留在说明里，而是压进他们眼前的证据。")
        return sentences

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
