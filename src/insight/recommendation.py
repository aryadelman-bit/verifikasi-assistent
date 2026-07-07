from __future__ import annotations

from collections import Counter

from src.storage.models import ValidationFinding


DEFAULT_WEIGHTS = {
    "CRITICAL": 25,
    "HIGH": 15,
    "MEDIUM": 8,
    "LOW": 3,
    "INFO": 0,
}


def calculate_risk_score(findings: list[ValidationFinding], weights: dict[str, int] | None = None) -> int:
    active_weights = {**DEFAULT_WEIGHTS, **(weights or {})}
    score = 0
    for finding in findings:
        if finding.status in {"WARNING", "FAIL"}:
            score += active_weights.get(finding.severity, 0)
    return min(score, 100)


def severity_counts(findings: list[ValidationFinding]) -> dict[str, int]:
    counter = Counter(
        finding.severity for finding in findings if finding.status in {"WARNING", "FAIL"}
    )
    return {severity: counter.get(severity, 0) for severity in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO")}


def decision_recommendation(findings: list[ValidationFinding], risk_score: int) -> str:
    counts = severity_counts(findings)
    if counts["CRITICAL"] > 0 or counts["HIGH"] >= 4 or risk_score >= 81:
        return "Jangan divalidasi dulu / kembalikan untuk perbaikan"
    if counts["HIGH"] > 0 or risk_score >= 41:
        return "Perlu klarifikasi/perbaikan data"
    if counts["MEDIUM"] > 0 or counts["LOW"] > 0 or risk_score >= 21:
        return "Dapat divalidasi dengan catatan"
    return "Layak divalidasi"

