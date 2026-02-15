from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class LayerName(str, Enum):
    background = "background"
    middleground = "middleground"
    foreground = "foreground"
    surface = "surface"


class ProjectCreate(BaseModel):
    key: str = "d minor"
    bars: int = 16
    meter: str = "4/4"
    style: str = "Bach 2-voice"
    seed: int = 1729


class Project(ProjectCreate):
    id: str
    created_at: datetime


class ValidatorIssue(BaseModel):
    validator: str
    severity: Literal["error", "warning"] = "error"
    message: str
    location: str | None = None


class ValidationReport(BaseModel):
    passed: bool
    issues: list[ValidatorIssue] = Field(default_factory=list)


class NoteEvent(BaseModel):
    pitch: int
    start: float
    duration: float
    velocity: int = 80
    layer: LayerName
    voice: Literal["upper", "lower"] = "upper"


class Artifact(BaseModel):
    project_id: str
    step: int
    created_at: datetime
    version: str = "0.1.0"
    ruleset_hash: str
    explanation_log: list[str]
    meta: dict[str, Any]
    background: dict[str, Any]
    middleground: dict[str, Any]
    foreground: dict[str, Any]
    surface: dict[str, Any]
    validation: ValidationReport


class RenderRequest(BaseModel):
    layers: list[LayerName] = Field(default_factory=lambda: list(LayerName))


class ArtifactResponse(BaseModel):
    artifact: Artifact

