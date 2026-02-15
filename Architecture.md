# Schenker Composer Architecture

The app models composition as immutable artifacts across six generation steps, grouped into four Schenkerian layers:

1. **Background**: Urlinie targets, Kopfton return, and Bassbrechung deep pillars (I–V–I).
2. **Middleground**: phrase plan, interruption cadence, and harmonic pillars.
3. **Foreground**: two-voice idioms (passing, neighbor, suspensions, cadential patterns).
4. **Surface**: explicit note events for playback + export.

## Validators

- **Interruption validator**: checks 2̂ at interruption bar, return to Kopfton, and notation markers (`//`, broken beam).
- **Bassbrechung validator**: enforces I–V–I at deep layer.
- **Harmony–Urlinie validator**: verifies structural tones align with expected harmony.
- **Counterpoint validator**: flags repeated perfect intervals and unresolved suspension-like behavior in realized events.

## Artifact model

Every step writes an immutable JSON under `artifacts/{project_id}/{timestamp}/step_n.json` with seed, version, ruleset hash, and explanation log.
