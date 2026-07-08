from __future__ import annotations

from typing import Any

from src.storage.models import ValidationFinding
from src.validation.utils import row_text, section


PILLAR_KEYWORDS = {
    "Manajemen & Organisasi": ["strategi", "manajemen", "investasi", "tim", "organisasi"],
    "Orang & Budaya": ["budaya", "kompetensi", "pelatihan", "sdm", "karyawan"],
    "Produk & Layanan": ["produk", "layanan", "inovasi", "desain"],
    "Teknologi": ["erp", "server", "database", "cloud", "iot", "sensor", "teknologi"],
    "Operasi Pabrik": ["otomasi", "maintenance", "rantai pasok", "produksi", "digitalisasi"],
}


def _finding(rule_id: str, severity: str, description: str, value: str, calculation: str, question: str) -> ValidationFinding:
    return ValidationFinding(
        rule_id=rule_id,
        nama_rule="Ringkasan indikatif INDI 4.0",
        kategori_data="INDI 4.0",
        severity=severity,
        status="WARNING",
        deskripsi_temuan=description,
        nilai_terdeteksi=value,
        dasar_perhitungan=calculation,
        rekomendasi_tindak_lanjut="Gunakan sebagai insight indikatif; jangan samakan dengan skor resmi INDI 4.0.",
        pertanyaan_klarifikasi_ke_perusahaan=question,
    )


def run(report: dict[str, Any], context: dict[str, Any]) -> list[ValidationFinding]:
    rows = section(report, "indi_4_0", "indi")
    findings: list[ValidationFinding] = []
    if not rows:
        return findings

    all_text = " ".join(row_text(row) for row in rows)
    lacks_strategy = any(token in all_text for token in ["belum ada strategi", "tidak ada strategi", "belum memiliki strategi"])
    has_tech_stack = any(token in all_text for token in ["erp", "server internal", "database", "analisis data", "iot", "otomasi"])
    if lacks_strategy and has_tech_stack:
        findings.append(
            _finding(
                "INDI_STRATEGY_TECH_CONTRADICTION",
                "LOW",
                "Jawaban INDI menunjukkan potensi kontradiksi ringan antara strategi dan implementasi teknologi.",
                "Belum ada strategi/tim/investasi tetapi ada ERP/server/database/analisis data.",
                "Pencarian kata kunci pada seluruh jawaban INDI 4.0.",
                "Mohon klarifikasi tingkat implementasi teknologi dan apakah sudah ada strategi formal atau masih ad hoc.",
            )
        )

    pillar_scores: list[str] = []
    for pillar, keywords in PILLAR_KEYWORDS.items():
        hits = sum(1 for keyword in keywords if keyword in all_text)
        score = min(5, hits)
        pillar_scores.append(f"{pillar}: {score}/5")
    findings.append(
        _finding(
            "INDI_INDICATIVE_PILLAR_SUMMARY",
            "INFO",
            "Skor indikatif sederhana per pilar INDI 4.0 berhasil dibuat.",
            "; ".join(pillar_scores),
            "Skor dihitung dari kemunculan kata kunci pada jawaban, bukan metodologi resmi INDI 4.0.",
            "",
        )
    )
    return findings

