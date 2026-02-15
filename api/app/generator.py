from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from random import Random

from .schemas import Artifact, Project
from .validators import run_validators


def _ruleset_hash() -> str:
    payload = "schenker-composer:background-middleground-foreground-surface:v1"
    return hashlib.sha256(payload.encode()).hexdigest()[:12]


def _base_template(project: Project) -> dict:
    return {
        "meta": {
            "key": project.key,
            "bars": project.bars,
            "meter": project.meter,
            "style": project.style,
            "seed": project.seed,
        },
        "background": {
            "urlinie_targets": [
                {"degree": 3, "bar": 1},
                {"degree": 2, "bar": 8},
                {"degree": 3, "bar": 9, "return": True},
                {"degree": 1, "bar": 16},
            ],
            "bassbrechung_pillars": [
                {"rn": "i", "bar": 1, "layer": "background"},
                {"rn": "V", "bar": 8, "layer": "background"},
                {"rn": "i", "bar": 16, "layer": "background"},
            ],
            "interruption": {"enabled": True, "at_bar": 8, "notation": "2^/V // broken_beam"},
        },
        "middleground": {"harmonic_pillars": [], "phrase_mapping": []},
        "foreground": {"ornaments": [], "texture_policy": {"pattern": "continuous_16ths", "imitation_delay": "1 beat"}},
        "surface": {"events": [], "musicxml_snapshot": ""},
    }


def generate_step(project: Project, step: int, previous: Artifact | None = None) -> Artifact:
    rng = Random(project.seed + step)
    data = _base_template(project) if previous is None else previous.model_dump()
    logs = [] if previous is None else list(previous.explanation_log)

    if step >= 2:
        data["middleground"]["harmonic_pillars"] = [
            {"bar": 1, "rn": "i"},
            {"bar": 4, "rn": "iv"},
            {"bar": 8, "rn": "V"},
            {"bar": 9, "rn": "i"},
            {"bar": 12, "rn": "iiø6"},
            {"bar": 16, "rn": "V-i"},
        ]
        data["middleground"]["phrase_mapping"] = [{"range": "1-8", "cadence": "HC"}, {"range": "9-16", "cadence": "PAC"}]
        logs.append("Step B/C: mapped interruption form (8+8) and harmonic pillars.")
    if step >= 3:
        data["foreground"]["ornaments"] = [
            {"type": "passing", "bar": 2},
            {"type": "neighbor", "bar": 6},
            {"type": "suspension_4_3", "bar": 15},
        ]
        logs.append("Step D/E: injected two-voice voice-leading ornaments.")
    if step >= 4:
        events = []
        for bar in range(1, project.bars + 1):
            base = (bar - 1) * 4
            for i in range(4):
                start = base + i
                top = 62 + ((bar + i) % 5)
                low = 50 + ((bar + i * 2) % 4)
                events.append({"pitch": top, "start": float(start), "duration": 0.95, "velocity": 88, "layer": "surface", "voice": "upper"})
                events.append({"pitch": low, "start": float(start), "duration": 0.95, "velocity": 72, "layer": "surface", "voice": "lower"})
        data["surface"]["events"] = events
        data["surface"]["musicxml_snapshot"] = "<score-partwise version='4.0'></score-partwise>"
        logs.append("Step F: rendered surface events for audio/export.")

    created_at = datetime.now(timezone.utc)
    artifact = Artifact(
        project_id=project.id,
        step=step,
        created_at=created_at,
        ruleset_hash=_ruleset_hash(),
        explanation_log=logs,
        meta=data["meta"],
        background=data["background"],
        middleground=data["middleground"],
        foreground=data["foreground"],
        surface=data["surface"],
        validation=run_validators(data),
    )
    return artifact
