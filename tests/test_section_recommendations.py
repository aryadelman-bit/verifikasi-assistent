from src.insight.narrative import generate_copy_note, generate_section_recommendation, section_recommendations_table
from src.storage.models import ValidationFinding, ValidationResult


def _finding(category: str, severity: str = "HIGH") -> ValidationFinding:
    return ValidationFinding(
        rule_id="TEST_RULE",
        nama_rule="Rule Uji",
        kategori_data=category,
        severity=severity,
        status="FAIL",
        deskripsi_temuan="Data perlu dicek",
        nilai_terdeteksi="nilai uji",
        rekomendasi_tindak_lanjut="Minta klarifikasi.",
    )


def test_section_recommendation_uses_related_categories():
    text = generate_section_recommendation("Bahan Baku", [_finding("Bahan Baku")])
    assert "Rekomendasi bagian Bahan Baku" in text
    assert "Perlu klarifikasi/perbaikan data" in text
    assert "Data perlu dicek" in text


def test_section_table_contains_identity_to_indi():
    rows = section_recommendations_table([_finding("INDI 4.0", "LOW")])
    sections = [row["Bagian"] for row in rows]
    assert sections[0] == "Identitas dan Perizinan"
    assert sections[-1] == "INDI 4.0"


def test_copy_note_includes_overall_recommendation():
    result = ValidationResult(
        findings=[_finding("Bahan Baku", "CRITICAL")],
        risk_score=25,
        recommendation="Jangan divalidasi dulu / kembalikan untuk perbaikan",
        severity_counts={"CRITICAL": 1, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0},
    )
    assert "Rekomendasi aplikasi" in generate_copy_note(result)
