# Schenker Composer

Schenker Composer is a full-stack web app for exploring layered generative composition for two voices:

- Background → Middleground → Foreground → Surface pipeline
- Step-by-step artifact generation with audit trails
- Validation reports (interruption, bassbrechung, harmony-urlinie, counterpoint)
- MIDI + MusicXML export

## Stack

- **Backend**: FastAPI, Pydantic, Celery, Redis
- **Frontend**: Next.js (App Router), TypeScript
- **Rendering**: mido (MIDI), MusicXML snapshot export

## Run with Docker

```bash
docker compose up --build
```

- Web UI: `http://localhost:3000`
- API: `http://localhost:8000`

## API

- `POST /projects`
- `POST /projects/{id}/generate/step/{n}`
- `GET /projects/{id}/artifacts/latest`
- `POST /projects/{id}/render/midi`
- `POST /projects/{id}/render/musicxml`
- `POST /projects/{id}/play/preview`

## Auditable artifacts

Every generation step is immutable JSON at:

```text
artifacts/{project_id}/{timestamp}/step_n.json
```

Each artifact includes seed, ruleset hash, version, and transformation explanation log.

## Testing

```bash
pip install -r api/requirements.txt
pytest api/tests
```

## Reference

The Schenkerian notation reference is expected at `docs/SchenkerGUIDE.pdf`.
