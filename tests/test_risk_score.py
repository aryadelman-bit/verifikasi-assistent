from src.insight.recommendation import calculate_risk_score, decision_recommendation
from src.storage.models import ValidationFinding


def finding(severity: str) -> ValidationFinding:
    return ValidationFinding(
        rule_id=f"R_{severity}",
        nama_rule="Rule",
        kategori_data="Test",
        severity=severity,
        status="FAIL",
        deskripsi_temuan="Temuan",
    )


def test_risk_score_is_capped_at_100():
    findings = [finding("CRITICAL") for _ in range(10)]
    assert calculate_risk_score(findings) == 100


def test_decision_recommendations():
    assert decision_recommendation([], 0) == "Layak divalidasi"
    assert decision_recommendation([finding("MEDIUM")], 8) == "Dapat divalidasi dengan catatan"
    assert decision_recommendation([finding("HIGH")], 15) == "Perlu klarifikasi/perbaikan data"
    assert decision_recommendation([finding("CRITICAL")], 25) == "Jangan divalidasi dulu / kembalikan untuk perbaikan"

