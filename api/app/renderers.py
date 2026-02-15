from __future__ import annotations

from io import BytesIO

import mido
from .schemas import Artifact, LayerName


def render_midi_bytes(artifact: Artifact, layers: list[LayerName]) -> bytes:
    mid = mido.MidiFile(ticks_per_beat=480)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    selected = {l.value if hasattr(l, 'value') else str(l) for l in layers}
    events = [e for e in artifact.surface.get("events", []) if e.get("layer") in selected]
    events.sort(key=lambda x: x["start"])
    current_ticks = 0
    for e in events:
        start_ticks = int(e["start"] * 480)
        delta = max(0, start_ticks - current_ticks)
        track.append(mido.Message("note_on", note=e["pitch"], velocity=e.get("velocity", 80), time=delta))
        track.append(mido.Message("note_off", note=e["pitch"], velocity=0, time=int(e["duration"] * 480)))
        current_ticks = start_ticks + int(e["duration"] * 480)
    output = BytesIO()
    mid.save(file=output)
    return output.getvalue()


def render_musicxml_string(artifact: Artifact, layers: list[LayerName]) -> str:
    return artifact.surface.get("musicxml_snapshot", "<score-partwise version='4.0'></score-partwise>")
