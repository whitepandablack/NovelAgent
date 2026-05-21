import tempfile
import unittest
from pathlib import Path

from novelagent import (
    ChapterDraft,
    ChapterPlan,
    CharacterCard,
    NovelProject,
    PlotThread,
    RevisionTask,
    TimelineEvent,
    WorldRule,
)


class NovelProjectTests(unittest.TestCase):
    def test_project_saves_and_loads_structured_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = NovelProject.create(
                root=Path(tmp),
                title="星诊所",
                premise="一名神经科医生发现震颤中藏着记忆。",
                genre="医疗科幻",
                style="安静悬疑",
            )
            project.characters.append(
                CharacterCard(
                    name="林澈",
                    role="主角",
                    goal="解读震颤中的记忆。",
                    conflict="他不信任自己的诊断。",
                    arc="从抽离的观察者变成负责的见证者。",
                )
            )
            project.chapters.append(
                ChapterDraft(
                    number=1,
                    title="第一次震颤",
                    summary="林澈遇见改变案件的病人。",
                    scenes=["诊所接诊", "深夜扫描"],
                    content="林澈写下第一条不可能的记录。",
                    referenced_characters=["林澈"],
                )
            )

            project.save()

            loaded = NovelProject.load(project.path)

            self.assertEqual(loaded.title, "星诊所")
            self.assertEqual(loaded.genre, "医疗科幻")
            self.assertEqual(loaded.characters[0].name, "林澈")
            self.assertEqual(loaded.chapters[0].referenced_characters, ["林澈"])

    def test_project_saves_and_loads_long_form_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = NovelProject.create(
                root=Path(tmp),
                title="星诊所",
                premise="一名神经科医生发现震颤中藏着记忆。",
                genre="医疗科幻",
                style="安静悬疑",
            )
            project.world_rules.append(
                WorldRule(
                    code="WR-001",
                    description="震颤可以携带被删除的短期记忆。",
                    source="核心设定",
                )
            )
            project.timeline.append(
                TimelineEvent(
                    chapter_number=1,
                    title="第一次震颤",
                    summary="林澈发现异常记录。",
                    characters=["林澈"],
                )
            )
            project.plot_threads.append(
                PlotThread(
                    code="PT-001",
                    title="震颤记忆",
                    status="open",
                    related_chapters=[1],
                    payoff="第三卷揭示记忆来源。",
                )
            )
            project.chapter_plans.append(
                ChapterPlan(
                    number=2,
                    title="米拉的警告",
                    goal="让第二位见证者打破安全解释。",
                    scenes=["走廊相遇", "调阅扫描"],
                    beats=["第二位见证者", "矛盾记忆"],
                    required_characters=["林澈", "米拉"],
                    plot_threads=["PT-001"],
                )
            )
            project.revision_tasks.append(
                RevisionTask(
                    target_chapter=2,
                    category="missing_beat",
                    instruction="补上矛盾记忆的场景证据。",
                    severity="warning",
                )
            )

            project.save()
            loaded = NovelProject.load(project.path)

            self.assertEqual(loaded.world_rules[0].code, "WR-001")
            self.assertEqual(loaded.timeline[0].characters, ["林澈"])
            self.assertEqual(loaded.plot_threads[0].related_chapters, [1])
            self.assertEqual(loaded.chapter_plans[0].required_characters, ["林澈", "米拉"])
            self.assertFalse(loaded.revision_tasks[0].completed)


if __name__ == "__main__":
    unittest.main()
