import tempfile
import unittest
from pathlib import Path

from novelagent.cli import main
from novelagent.cli import _build_workflow
from novelagent import LLMNovelWorkflow, NovelProject, NovelWorkflow


class CliTests(unittest.TestCase):
    def test_seed_command_creates_project_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            exit_code = main(
                [
                    "seed",
                    "--root",
                    tmp,
                    "--title",
                    "星诊所",
                    "--premise",
                    "一名神经科医生发现震颤中藏着记忆。",
                    "--genre",
                    "医疗科幻",
                    "--style",
                    "安静悬疑",
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertTrue((Path(tmp) / "novel" / "novel_project.json").exists())

    def test_workbench_commands_operate_on_project_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            main(
                [
                    "seed",
                    "--root",
                    tmp,
                    "--title",
                    "星诊所",
                    "--premise",
                    "一名神经科医生发现震颤中藏着记忆。",
                    "--genre",
                    "医疗科幻",
                    "--style",
                    "安静悬疑",
                ]
            )
            project_path = Path(tmp) / "novel" / "novel_project.json"
            export_path = Path(tmp) / "manuscript.md"

            self.assertEqual(main(["status", "--project", str(project_path)]), 0)
            self.assertEqual(main(["plan-next", "--project", str(project_path)]), 0)
            self.assertEqual(main(["draft-next", "--project", str(project_path)]), 0)
            self.assertEqual(
                main(["review", "--project", str(project_path), "--chapter", "2"]),
                0,
            )
            self.assertEqual(
                main(["revise", "--project", str(project_path), "--chapter", "2"]),
                0,
            )
            self.assertEqual(
                main(["export", "--project", str(project_path), "--out", str(export_path)]),
                0,
            )

            exported = export_path.read_text(encoding="utf-8")
            self.assertIn("# 星诊所", exported)
            self.assertIn("## 第 2 章", exported)

    def test_status_returns_error_for_missing_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing.json"

            exit_code = main(["status", "--project", str(missing)])

            self.assertEqual(exit_code, 1)

    def test_build_workflow_can_select_llm_workflow(self):
        self.assertIsInstance(_build_workflow(False), NovelWorkflow)
        self.assertIsInstance(_build_workflow(True), LLMNovelWorkflow)

    def test_seed_command_accepts_llm_flag(self):
        parser = __import__("novelagent.cli", fromlist=["build_parser"]).build_parser()
        args = parser.parse_args(
            [
                "seed",
                "--root",
                "tmp",
                "--title",
                "走马灯星球",
                "--premise",
                "文明整体返退",
                "--genre",
                "文明退变悬疑",
                "--style",
                "危险倒叙",
                "--llm",
            ]
        )

        self.assertTrue(args.llm)

    def test_write_command_saves_manual_story_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            main(
                [
                    "seed",
                    "--root",
                    tmp,
                    "--title",
                    "星诊所",
                    "--premise",
                    "病历会提前写下尚未发生的症状",
                    "--genre",
                    "近未来悬疑",
                    "--style",
                    "克制",
                ]
            )
            project_path = Path(tmp) / "novel" / "novel_project.json"

            exit_code = main(
                [
                    "write",
                    "--project",
                    str(project_path),
                    "--title",
                    "走廊里的纸条",
                    "--content",
                    "林澈把纸条夹进病历本，决定暂时不交给系统。",
                ]
            )

            project = NovelProject.load(project_path)
            saved_path = Path(tmp) / "novel" / "writing" / "chapter-002-r0.md"
            self.assertEqual(exit_code, 0)
            self.assertTrue(saved_path.exists())
            self.assertIn("走廊里的纸条", saved_path.read_text(encoding="utf-8"))
            self.assertEqual(project.chapters[-1].title, "走廊里的纸条")
            self.assertIn("纸条", project.chapters[-1].content)


if __name__ == "__main__":
    unittest.main()
