import tempfile
import unittest
from pathlib import Path

from novelagent.cli import main


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


if __name__ == "__main__":
    unittest.main()
