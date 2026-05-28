import tempfile
import unittest
from pathlib import Path

from novelagent import NovelRequest, NovelWorkflow


class NovelWorkflowTests(unittest.TestCase):
    def test_seed_workflow_generates_first_chapter_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            request = NovelRequest(
                title="星诊所",
                premise="一名神经科医生发现震颤中藏着记忆。",
                genre="医疗科幻",
                style="安静悬疑",
            )

            project = NovelWorkflow().run_seed_project(request, Path(tmp))

            self.assertEqual(project.title, "星诊所")
            self.assertIn("震颤", project.story_bible.logline)
            self.assertGreaterEqual(len(project.characters), 3)
            self.assertEqual(len(project.volume_outline), 3)
            self.assertEqual(len(project.chapter_outlines), 3)
            self.assertEqual(len(project.chapters), 1)
            self.assertEqual(project.chapters[0].number, 1)
            self.assertIn("危险", project.chapters[0].title)
            self.assertNotIn("林澈", project.chapters[0].content)
            self.assertTrue(project.reviews[0].passed)
            self.assertTrue(project.path.exists())

    def test_plan_next_chapter_creates_reusable_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            request = NovelRequest(
                title="星诊所",
                premise="一名神经科医生发现震颤中藏着记忆。",
                genre="医疗科幻",
                style="安静悬疑",
            )
            workflow = NovelWorkflow()
            project = workflow.run_seed_project(request, Path(tmp))

            first_plan = workflow.plan_next_chapter(project)
            second_plan = workflow.plan_next_chapter(project)

            self.assertEqual(first_plan.number, 2)
            self.assertEqual(second_plan.number, 2)
            self.assertEqual(len(project.chapter_plans), 1)
            self.assertIn("主角", first_plan.required_characters)
            self.assertIn("引路者", first_plan.required_characters)
            self.assertTrue(project.path.exists())

    def test_draft_next_chapter_uses_plan_and_records_timeline(self):
        with tempfile.TemporaryDirectory() as tmp:
            request = NovelRequest(
                title="星诊所",
                premise="一名神经科医生发现震颤中藏着记忆。",
                genre="医疗科幻",
                style="安静悬疑",
            )
            workflow = NovelWorkflow()
            project = workflow.run_seed_project(request, Path(tmp))
            workflow.plan_next_chapter(project)

            chapter = workflow.draft_next_chapter(project)

            self.assertEqual(chapter.number, 2)
            self.assertEqual(chapter.source_plan_number, 2)
            self.assertIn("光接触证据", chapter.content)
            self.assertEqual(project.chapters[-1].number, 2)
            self.assertEqual(project.timeline[-1].chapter_number, 2)

    def test_review_issues_create_revision_tasks_and_revise_chapter(self):
        with tempfile.TemporaryDirectory() as tmp:
            request = NovelRequest(
                title="星诊所",
                premise="一名神经科医生发现震颤中藏着记忆。",
                genre="医疗科幻",
                style="安静悬疑",
            )
            workflow = NovelWorkflow()
            project = workflow.run_seed_project(request, Path(tmp))
            workflow.plan_next_chapter(project)
            chapter = workflow.draft_next_chapter(project)
            chapter.content = "林澈追查记录。"

            report = workflow.review_chapter(project, chapter.number)
            tasks = workflow.create_revision_tasks(project, report)
            revised = workflow.revise_chapter(project, chapter.number)

            self.assertFalse(report.passed)
            self.assertGreaterEqual(len(tasks), 1)
            self.assertTrue(all(task.completed for task in project.revision_tasks))
            self.assertEqual(revised.number, chapter.number)
            self.assertEqual(revised.revision, 1)
            self.assertIn("重排场景", revised.content)
            self.assertNotIn("修订补充", revised.content)


if __name__ == "__main__":
    unittest.main()
