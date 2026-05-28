from __future__ import annotations

import argparse
from pathlib import Path

from .llm import OpenAICompatibleClient
from .llm_workflow import LLMNovelWorkflow
from .models import ChapterDraft, NovelRequest, TimelineEvent
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
    plan_next.add_argument("--llm", action="store_true", help="使用大模型规划下一章。")

    draft_next = subparsers.add_parser("draft-next", help="起草下一章。")
    draft_next.add_argument("--project", required=True, help="novel_project.json 路径。")
    draft_next.add_argument("--llm", action="store_true", help="使用大模型起草下一章。")

    write = subparsers.add_parser("write", help="手动保存一段故事正文。")
    write.add_argument("--project", required=True, help="novel_project.json 路径。")
    write.add_argument("--title", required=True, help="本段或章节标题。")
    write.add_argument("--content", help="直接传入正文。")
    write.add_argument("--from-file", help="从文本/Markdown 文件读取正文。")
    write.add_argument("--chapter", type=int, help="章节号；默认使用下一章。")
    write.add_argument("--summary", default="", help="本段摘要；默认取正文前 80 字。")

    review = subparsers.add_parser("review", help="审稿指定章节。")
    review.add_argument("--project", required=True, help="novel_project.json 路径。")
    review.add_argument("--chapter", required=True, type=int, help="章节号。")
    review.add_argument("--llm", action="store_true", help="使用大模型审稿。")

    revise = subparsers.add_parser("revise", help="根据审稿任务修订指定章节。")
    revise.add_argument("--project", required=True, help="novel_project.json 路径。")
    revise.add_argument("--chapter", required=True, type=int, help="章节号。")
    revise.add_argument("--llm", action="store_true", help="使用大模型修订章节。")

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

    try:
        project = _load_project(Path(args.project))
        workflow = _build_workflow(getattr(args, "llm", False))
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
        if args.command == "write":
            chapter, out_path = _save_manual_story_text(project, args)
            print(f"已保存第 {chapter.number} 章 r{chapter.revision}：{out_path}")
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


def _build_workflow(use_llm: bool):
    if use_llm:
        return LLMNovelWorkflow(OpenAICompatibleClient())
    return NovelWorkflow()


def _save_manual_story_text(project: NovelProject, args) -> tuple[ChapterDraft, Path]:
    content = _read_manual_content(args)
    number = args.chapter or _next_manual_chapter_number(project)
    revision = _next_revision(project, number)
    summary = args.summary or content[:80]
    chapter = ChapterDraft(
        number=number,
        title=args.title,
        summary=summary,
        scenes=[],
        content=content,
        referenced_characters=_referenced_known_characters(project, content),
        revision=revision,
        source_plan_number=None,
        narrative_contract={
            "source": "manual_write",
            "saved_as": f"chapter-{number:03d}-r{revision}.md",
        },
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
    out_path = _manual_write_path(project, number, revision)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(_manual_markdown(project, chapter), encoding="utf-8")
    return chapter, out_path


def _read_manual_content(args) -> str:
    if args.content and args.from_file:
        raise ValueError("--content 和 --from-file 只能使用一个。")
    if args.from_file:
        content = Path(args.from_file).read_text(encoding="utf-8")
    else:
        content = args.content or ""
    if not content.strip():
        raise ValueError("正文不能为空；请传入 --content 或 --from-file。")
    return content.strip()


def _next_manual_chapter_number(project: NovelProject) -> int:
    return max([chapter.number for chapter in project.chapters], default=0) + 1


def _next_revision(project: NovelProject, number: int) -> int:
    revisions = [chapter.revision for chapter in project.chapters if chapter.number == number]
    return max(revisions) + 1 if revisions else 0


def _manual_write_path(project: NovelProject, number: int, revision: int) -> Path:
    if project.path is None:
        raise ValueError("没有项目路径，无法保存手写正文。")
    return project.path.parent / "writing" / f"chapter-{number:03d}-r{revision}.md"


def _manual_markdown(project: NovelProject, chapter: ChapterDraft) -> str:
    return (
        f"# {project.title}\n\n"
        f"## 第 {chapter.number} 章：{chapter.title}\n\n"
        f"{chapter.content.rstrip()}\n"
    )


def _referenced_known_characters(project: NovelProject, content: str) -> list[str]:
    return [character.name for character in project.characters if character.name in content]
