from __future__ import annotations

import argparse
from pathlib import Path

from .models import NovelRequest
from .project import NovelProject
from .workflow import NovelWorkflow


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="novelagent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    seed = subparsers.add_parser("seed", help="创建种子小说项目。")
    seed.add_argument("--root", required=True, help="用于创建项目的目录。")
    seed.add_argument("--title", required=True, help="小说标题。")
    seed.add_argument("--premise", required=True, help="核心设定。")
    seed.add_argument("--genre", required=True, help="题材或市场分类。")
    seed.add_argument("--style", required=True, help="写作风格偏好。")

    status = subparsers.add_parser("status", help="查看小说项目状态。")
    status.add_argument("--project", required=True, help="novel_project.json 路径。")

    plan_next = subparsers.add_parser("plan-next", help="规划下一章。")
    plan_next.add_argument("--project", required=True, help="novel_project.json 路径。")

    draft_next = subparsers.add_parser("draft-next", help="起草下一章。")
    draft_next.add_argument("--project", required=True, help="novel_project.json 路径。")

    review = subparsers.add_parser("review", help="审稿指定章节。")
    review.add_argument("--project", required=True, help="novel_project.json 路径。")
    review.add_argument("--chapter", required=True, type=int, help="章节号。")

    revise = subparsers.add_parser("revise", help="根据审稿任务修订指定章节。")
    revise.add_argument("--project", required=True, help="novel_project.json 路径。")
    revise.add_argument("--chapter", required=True, type=int, help="章节号。")

    export = subparsers.add_parser("export", help="导出正文 Markdown。")
    export.add_argument("--project", required=True, help="novel_project.json 路径。")
    export.add_argument("--out", required=True, help="导出文件路径。")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "seed":
        request = NovelRequest(
            title=args.title,
            premise=args.premise,
            genre=args.genre,
            style=args.style,
        )
        NovelWorkflow().run_seed_project(request, Path(args.root))
        return 0

    workflow = NovelWorkflow()
    try:
        project = _load_project(Path(args.project))
        if args.command == "status":
            pending = len([task for task in project.revision_tasks if not task.completed])
            print(
                f"《{project.title}》：{len(project.chapters)} 个章节稿，"
                f"{len(project.chapter_plans)} 个章节计划，{pending} 个未完成修订任务。"
            )
            return 0
        if args.command == "plan-next":
            plan = workflow.plan_next_chapter(project)
            print(f"已规划第 {plan.number} 章：{plan.title}")
            return 0
        if args.command == "draft-next":
            chapter = workflow.draft_next_chapter(project)
            print(f"已起草第 {chapter.number} 章：{chapter.title}")
            return 0
        if args.command == "review":
            report = workflow.review_chapter(project, args.chapter)
            print(report.summary)
            return 0 if report.passed else 1
        if args.command == "revise":
            chapter = workflow.revise_chapter(project, args.chapter)
            print(f"已生成第 {chapter.number} 章修订版 r{chapter.revision}。")
            return 0
        if args.command == "export":
            out_path = Path(args.out)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(workflow.export_manuscript(project), encoding="utf-8")
            print(f"已导出正文：{out_path}")
            return 0
    except (OSError, ValueError) as exc:
        print(f"错误：{exc}")
        return 1

    parser.error(f"未知命令：{args.command}")
    return 2


def _load_project(path: Path) -> NovelProject:
    if not path.exists():
        raise ValueError(f"项目文件不存在：{path}")
    return NovelProject.load(path)
