from __future__ import annotations

from .models import ChapterDraft, ReviewIssue, ReviewReport
from .project import NovelProject


class ContinuityChecker:
    def review_chapter(self, project: NovelProject, chapter: ChapterDraft) -> ReviewReport:
        known_names = {character.name for character in project.characters}
        issues: list[ReviewIssue] = []

        for name in chapter.referenced_characters:
            if name not in known_names:
                issues.append(
                    ReviewIssue(
                        category="unknown_character",
                        message=f"第 {chapter.number} 章引用了未知人物：{name}。",
                        severity="error",
                    )
                )

        for existing in project.chapters:
            if (
                existing is not chapter
                and existing.number == chapter.number
                and existing.revision == chapter.revision
            ):
                issues.append(
                    ReviewIssue(
                        category="duplicate_chapter",
                        message=f"第 {chapter.number} 章存在重复稿件版本。",
                        severity="error",
                    )
                )
                break

        plan = next(
            (
                item
                for item in project.chapter_plans
                if item.number == chapter.source_plan_number or item.number == chapter.number
            ),
            None,
        )
        if plan is not None:
            for beat in plan.beats:
                if beat and beat not in chapter.content and beat not in chapter.summary:
                    issues.append(
                        ReviewIssue(
                            category="missing_beat",
                            message=f"第 {chapter.number} 章未覆盖计划节拍：{beat}。",
                            severity="warning",
                        )
                    )

        if issues:
            return ReviewReport(
                target=f"chapter:{chapter.number}",
                passed=False,
                summary=f"发现 {len(issues)} 个连续性问题。",
                issues=issues,
            )

        return ReviewReport(
            target=f"chapter:{chapter.number}",
            passed=True,
            summary="已知人物引用未发现连续性问题。",
            issues=[],
        )
