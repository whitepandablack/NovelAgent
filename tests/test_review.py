import unittest

from novelagent import ChapterDraft, CharacterCard, ContinuityChecker, NovelProject
from novelagent import ChapterPlan


class ContinuityCheckerTests(unittest.TestCase):
    def test_review_flags_unknown_character_references(self):
        project = NovelProject(
            title="星诊所",
            premise="一名神经科医生发现震颤中藏着记忆。",
            genre="医疗科幻",
            style="安静悬疑",
            path=None,
            characters=[
                CharacterCard(
                    name="林澈",
                    role="主角",
                    goal="解读震颤中的记忆。",
                    conflict="他不信任自己的诊断。",
                    arc="从抽离的观察者变成负责的见证者。",
                )
            ],
        )
        chapter = ChapterDraft(
            number=1,
            title="第一次震颤",
            summary="林澈听见一个不可能的名字。",
            scenes=["诊所接诊"],
            content="林澈向米拉询问扫描结果。",
            referenced_characters=["林澈", "米拉"],
        )

        report = ContinuityChecker().review_chapter(project, chapter)

        self.assertFalse(report.passed)
        self.assertEqual(report.issues[0].category, "unknown_character")
        self.assertIn("米拉", report.issues[0].message)
        self.assertIn("未知人物", report.issues[0].message)

    def test_review_flags_missing_plan_beats(self):
        project = NovelProject(
            title="星诊所",
            premise="一名神经科医生发现震颤中藏着记忆。",
            genre="医疗科幻",
            style="安静悬疑",
            path=None,
            characters=[
                CharacterCard(
                    name="林澈",
                    role="主角",
                    goal="解读震颤中的记忆。",
                    conflict="他不信任自己的诊断。",
                    arc="从抽离的观察者变成负责的见证者。",
                )
            ],
            chapter_plans=[
                ChapterPlan(
                    number=2,
                    title="米拉的警告",
                    goal="第二位见证者出现。",
                    beats=["第二位见证者", "矛盾记忆"],
                    required_characters=["林澈"],
                )
            ],
        )
        chapter = ChapterDraft(
            number=2,
            title="米拉的警告",
            summary="林澈追查记录。",
            scenes=["走廊相遇"],
            content="林澈追查记录，但还没有形成新的矛盾。",
            referenced_characters=["林澈"],
            source_plan_number=2,
        )

        report = ContinuityChecker().review_chapter(project, chapter)

        self.assertFalse(report.passed)
        self.assertEqual(report.issues[0].category, "missing_beat")
        self.assertIn("第二位见证者", report.issues[0].message)

    def test_review_flags_duplicate_chapter_number(self):
        existing = ChapterDraft(
            number=2,
            title="旧第二章",
            summary="旧稿。",
            scenes=["旧场景"],
            content="旧稿内容。",
            referenced_characters=[],
        )
        project = NovelProject(
            title="星诊所",
            premise="一名神经科医生发现震颤中藏着记忆。",
            genre="医疗科幻",
            style="安静悬疑",
            path=None,
            chapters=[existing],
        )
        chapter = ChapterDraft(
            number=2,
            title="新第二章",
            summary="新稿。",
            scenes=["新场景"],
            content="新稿内容。",
            referenced_characters=[],
        )

        report = ContinuityChecker().review_chapter(project, chapter)

        self.assertFalse(report.passed)
        self.assertEqual(report.issues[0].category, "duplicate_chapter")


if __name__ == "__main__":
    unittest.main()
