from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class Evidence:
    source: str
    page: int
    excerpt: str
    confidence: float


@dataclass
class ScoreMeasure:
    index: int
    notation: str
    chord_hint: str | None = None
    fingering_hint: str | None = None


@dataclass
class AnalysisInsight:
    insight_type: str
    title: str
    description: str
    evidence: list[Evidence] = field(default_factory=list)


@dataclass
class LessonSection:
    id: str
    title: str
    objective: str
    measures: list[ScoreMeasure] = field(default_factory=list)
    insights: list[AnalysisInsight] = field(default_factory=list)


@dataclass
class TeachingSystemBundle:
    title: str
    source_pdf: str
    sections: list[LessonSection]
    audit_log: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
