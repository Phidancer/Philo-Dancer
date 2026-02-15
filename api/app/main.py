from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response

from .generator import generate_step
from .renderers import render_midi_bytes, render_musicxml_string
from .schemas import ArtifactResponse, Project, ProjectCreate, RenderRequest
from .storage import latest_artifact, save_artifact

app = FastAPI(title="Schenker Composer API")
PROJECTS: dict[str, Project] = {}


@app.get('/health')
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post('/projects', response_model=Project)
def create_project(payload: ProjectCreate) -> Project:
    pid = str(uuid.uuid4())
    project = Project(id=pid, created_at=datetime.now(timezone.utc), **payload.model_dump())
    PROJECTS[pid] = project
    return project


@app.post('/projects/{project_id}/generate/step/{step}', response_model=ArtifactResponse)
def generate(project_id: str, step: int) -> ArtifactResponse:
    project = PROJECTS.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail='Project not found')
    previous = latest_artifact(project_id)
    artifact = generate_step(project, step=step, previous=previous)
    save_artifact(artifact)
    return ArtifactResponse(artifact=artifact)


@app.get('/projects/{project_id}/artifacts/latest', response_model=ArtifactResponse)
def get_latest(project_id: str) -> ArtifactResponse:
    artifact = latest_artifact(project_id)
    if not artifact:
        raise HTTPException(status_code=404, detail='No artifacts found')
    return ArtifactResponse(artifact=artifact)


@app.post('/projects/{project_id}/render/midi')
def render_midi(project_id: str, req: RenderRequest) -> Response:
    artifact = latest_artifact(project_id)
    if not artifact:
        raise HTTPException(status_code=404, detail='No artifacts found')
    blob = render_midi_bytes(artifact, req.layers)
    return Response(content=blob, media_type='audio/midi')


@app.post('/projects/{project_id}/render/musicxml')
def render_musicxml(project_id: str, req: RenderRequest) -> Response:
    artifact = latest_artifact(project_id)
    if not artifact:
        raise HTTPException(status_code=404, detail='No artifacts found')
    xml = render_musicxml_string(artifact, req.layers)
    return Response(content=xml, media_type='application/vnd.recordare.musicxml+xml')


@app.post('/projects/{project_id}/play/preview')
def preview(project_id: str, req: RenderRequest) -> dict:
    return {"message": "Use client-side Tone.js playback for preview.", "layers": req.layers}
