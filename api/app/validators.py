from __future__ import annotations

from .schemas import ValidationReport, ValidatorIssue


def interruption_validator(model: dict) -> list[ValidatorIssue]:
    issues: list[ValidatorIssue] = []
    intr = model["background"].get("interruption", {})
    if not intr.get("enabled"):
        return issues
    targets = model["background"].get("urlinie_targets", [])
    has_two = any(t.get("degree") == 2 and t.get("bar") == intr.get("at_bar") for t in targets)
    has_return = any(t.get("return") is True for t in targets)
    notation = intr.get("notation", "")
    if not has_two:
        issues.append(ValidatorIssue(validator="interruption", message="Interruption requires 2̂ at interruption bar over V."))
    if not has_return:
        issues.append(ValidatorIssue(validator="interruption", message="Post-interruption Kopfton return is missing."))
    if "//" not in notation or "broken_beam" not in notation:
        issues.append(ValidatorIssue(validator="interruption", message="Interruption notation must include double slash and broken beam."))
    return issues


def bassbrechung_validator(model: dict) -> list[ValidatorIssue]:
    issues: list[ValidatorIssue] = []
    pillars = [p for p in model["background"].get("bassbrechung_pillars", []) if p.get("layer") == "background"]
    rn_seq = [p.get("rn", "").lower() for p in pillars]
    if rn_seq != ["i", "v", "i"]:
        issues.append(ValidatorIssue(validator="bassbrechung", message="Background bassbrechung must be I–V–I."))
    return issues


def harmony_urlinie_validator(model: dict) -> list[ValidatorIssue]:
    issues: list[ValidatorIssue] = []
    harmonies = {h.get("bar"): h.get("rn", "") for h in model["middleground"].get("harmonic_pillars", [])}
    for t in model["background"].get("urlinie_targets", []):
        if t.get("degree") == 2 and harmonies.get(t.get("bar"), "").upper() != "V":
            issues.append(ValidatorIssue(validator="harmony_urlinie", message="2̂ structural tone should align with V at interruption."))
    return issues


def counterpoint_safety_validator(model: dict) -> list[ValidatorIssue]:
    issues: list[ValidatorIssue] = []
    events = model["surface"].get("events", [])
    by_start = {}
    for e in events:
        by_start.setdefault(e["start"], []).append(e)
    ordered = sorted(by_start.items())
    prev_interval = None
    prev_start = None
    for start, es in ordered:
        if len(es) < 2:
            continue
        upper = max(es, key=lambda x: x["pitch"])
        lower = min(es, key=lambda x: x["pitch"])
        interval = (upper["pitch"] - lower["pitch"]) % 12
        if prev_interval in {0, 7} and interval == prev_interval:
            issues.append(ValidatorIssue(validator="counterpoint", message="Potential parallel perfect interval detected.", location=f"beat {start}"))
        prev_interval = interval
        prev_start = start
    return issues


def run_validators(model: dict) -> ValidationReport:
    issues = []
    issues.extend(interruption_validator(model))
    issues.extend(bassbrechung_validator(model))
    issues.extend(harmony_urlinie_validator(model))
    issues.extend(counterpoint_safety_validator(model))
    return ValidationReport(passed=not issues, issues=issues)
