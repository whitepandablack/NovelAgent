from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class NovelRequest:
    title: str
    premise: str
    genre: str
    style: str


@dataclass
class StoryBible:
    logline: str
    themes: list[str] = field(default_factory=list)
    rules: list[str] = field(default_factory=list)
    style_notes: list[str] = field(default_factory=list)


@dataclass
class CharacterCard:
    name: str
    role: str
    goal: str
    conflict: str
    arc: str


@dataclass
class OutlineItem:
    title: str
    summary: str
    beats: list[str] = field(default_factory=list)


@dataclass
class ChapterDraft:
    number: int
    title: str
    summary: str
    scenes: list[str]
    content: str
    referenced_characters: list[str] = field(default_factory=list)
    revision: int = 0
    source_plan_number: int | None = None
    narrative_contract: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorldRule:
    code: str
    description: str
    source: str
    status: str = "active"


@dataclass
class TimelineEvent:
    chapter_number: int
    title: str
    summary: str
    characters: list[str] = field(default_factory=list)


@dataclass
class PlotThread:
    code: str
    title: str
    status: str = "open"
    related_chapters: list[int] = field(default_factory=list)
    payoff: str = ""


@dataclass
class ChapterPlan:
    number: int
    title: str
    goal: str
    scenes: list[str] = field(default_factory=list)
    beats: list[str] = field(default_factory=list)
    required_characters: list[str] = field(default_factory=list)
    plot_threads: list[str] = field(default_factory=list)
    narrative_contract: dict[str, Any] = field(default_factory=dict)


@dataclass
class RevisionTask:
    target_chapter: int
    category: str
    instruction: str
    severity: str = "warning"
    completed: bool = False


@dataclass
class ReviewIssue:
    category: str
    message: str
    severity: str = "warning"


@dataclass
class ReviewReport:
    target: str
    passed: bool
    summary: str
    issues: list[ReviewIssue] = field(default_factory=list)


def dataclass_to_dict(value):
    return asdict(value)
