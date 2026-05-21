from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .models import (
    ChapterPlan,
    ChapterDraft,
    CharacterCard,
    OutlineItem,
    PlotThread,
    ReviewIssue,
    ReviewReport,
    RevisionTask,
    StoryBible,
    TimelineEvent,
    WorldRule,
    dataclass_to_dict,
)


def _slugify(title: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", title.strip().lower()).strip("-")
    return slug or "novel"


@dataclass
class NovelProject:
    title: str
    premise: str
    genre: str
    style: str
    path: Path | None
    story_bible: StoryBible = field(
        default_factory=lambda: StoryBible(logline="", themes=[], rules=[], style_notes=[])
    )
    characters: list[CharacterCard] = field(default_factory=list)
    volume_outline: list[OutlineItem] = field(default_factory=list)
    chapter_outlines: list[OutlineItem] = field(default_factory=list)
    world_rules: list[WorldRule] = field(default_factory=list)
    timeline: list[TimelineEvent] = field(default_factory=list)
    plot_threads: list[PlotThread] = field(default_factory=list)
    chapter_plans: list[ChapterPlan] = field(default_factory=list)
    chapters: list[ChapterDraft] = field(default_factory=list)
    reviews: list[ReviewReport] = field(default_factory=list)
    revision_tasks: list[RevisionTask] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        root: Path,
        title: str,
        premise: str,
        genre: str,
        style: str,
    ) -> "NovelProject":
        project_dir = root / _slugify(title)
        return cls(
            title=title,
            premise=premise,
            genre=genre,
            style=style,
            path=project_dir / "novel_project.json",
        )

    def save(self) -> None:
        if self.path is None:
            raise ValueError("没有项目路径，无法保存小说项目。")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: Path) -> "NovelProject":
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_dict(data, path)

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "premise": self.premise,
            "genre": self.genre,
            "style": self.style,
            "story_bible": dataclass_to_dict(self.story_bible),
            "characters": [dataclass_to_dict(item) for item in self.characters],
            "volume_outline": [dataclass_to_dict(item) for item in self.volume_outline],
            "chapter_outlines": [dataclass_to_dict(item) for item in self.chapter_outlines],
            "world_rules": [dataclass_to_dict(item) for item in self.world_rules],
            "timeline": [dataclass_to_dict(item) for item in self.timeline],
            "plot_threads": [dataclass_to_dict(item) for item in self.plot_threads],
            "chapter_plans": [dataclass_to_dict(item) for item in self.chapter_plans],
            "chapters": [dataclass_to_dict(item) for item in self.chapters],
            "reviews": [dataclass_to_dict(item) for item in self.reviews],
            "revision_tasks": [dataclass_to_dict(item) for item in self.revision_tasks],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], path: Path | None = None) -> "NovelProject":
        return cls(
            title=data["title"],
            premise=data["premise"],
            genre=data["genre"],
            style=data["style"],
            path=path,
            story_bible=StoryBible(**data.get("story_bible", {})),
            characters=[CharacterCard(**item) for item in data.get("characters", [])],
            volume_outline=[OutlineItem(**item) for item in data.get("volume_outline", [])],
            chapter_outlines=[OutlineItem(**item) for item in data.get("chapter_outlines", [])],
            world_rules=[WorldRule(**item) for item in data.get("world_rules", [])],
            timeline=[TimelineEvent(**item) for item in data.get("timeline", [])],
            plot_threads=[PlotThread(**item) for item in data.get("plot_threads", [])],
            chapter_plans=[ChapterPlan(**item) for item in data.get("chapter_plans", [])],
            chapters=[ChapterDraft(**item) for item in data.get("chapters", [])],
            reviews=[_review_from_dict(item) for item in data.get("reviews", [])],
            revision_tasks=[RevisionTask(**item) for item in data.get("revision_tasks", [])],
        )


def _review_from_dict(data: dict[str, Any]) -> ReviewReport:
    issues = [ReviewIssue(**item) for item in data.get("issues", [])]
    return ReviewReport(
        target=data["target"],
        passed=data["passed"],
        summary=data["summary"],
        issues=issues,
    )
