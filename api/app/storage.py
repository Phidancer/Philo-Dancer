from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .schemas import Artifact

BASE = Path("artifacts")


@dataclass
class PersistedPath:
    project_id: str
    timestamp: str
    path: Path


def artifact_path(project_id: str, ts: datetime, step: int) -> PersistedPath:
    timestamp = ts.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    folder = BASE / project_id / timestamp
    folder.mkdir(parents=True, exist_ok=True)
    return PersistedPath(project_id=project_id, timestamp=timestamp, path=folder / f"step_{step}.json")


def save_artifact(artifact: Artifact) -> Path:
    p = artifact_path(artifact.project_id, artifact.created_at, artifact.step)
    p.path.write_text(artifact.model_dump_json(indent=2), encoding="utf-8")
    return p.path


def latest_artifact(project_id: str) -> Artifact | None:
    root = BASE / project_id
    if not root.exists():
        return None
    files = sorted(root.glob("*/step_*.json"))
    if not files:
        return None
    return Artifact.model_validate_json(files[-1].read_text(encoding="utf-8"))
