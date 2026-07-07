from __future__ import annotations

from collections import Counter
from typing import Any

from src.insight.recommendation import DEFAULT_WEIGHTS
from src.storage.models import ValidationFinding, ValidationResult


SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
SECTION_CATEGORIES: dict[str, list[str]] = {
    "Identitas dan Perizinan": ["Kelengkapan Data", "Identitas/KBLI/HS"],
    "Investasi": ["Investasi", "Kelengkapan Data"],
    "Kapasitas": ["Kapasitas Produksi", "Identitas/KBLI/HS", "Kelengkapan Data"],
    "Produksi & Penjualan": ["Produksi & Persediaan", "Identitas/KBLI/HS", "Kelengkapan Data"],
    "Bahan Baku": ["Bahan Baku", "Kelengkapan Data"],
    "Bahan Penolong": ["Bahan Penolong"],
    "Tenaga Kerja": ["Tenaga Kerja", "Kelengkapan Data"],
    "Air & Energi": ["Air & Energi", "Kelengkapan Data"],
    "Pengeluaran": ["Pengeluaran", "Kelengkapan Data"],
    "Rencana Produksi": ["Produksi & Persediaan", "Identitas/KBLI/HS"],
    "Mesin": ["Mesin"],
    "Persediaan": ["Produksi & Persediaan", "Kelengkapan Data"],
    "Limbah": ["Limbah"],
    "INDI 4.0": ["INDI 4.0"],
}


def top_findings(findings: list[ValidationFinding], limit: int = 5) -> list[ValidationFinding]:
    actionable = [finding for finding in findings if finding.status in {"WARNING", "FAIL"}]
    return sorted(actionable, key=lambda item: (SEVERITY_ORDER.get(item.severity, 99), item.rule_id))[:limit]


def actionable_findings(findings: list[ValidationFinding]) -> list[ValidationFinding]:
    return [finding for finding in findings if finding.status in {"WARNING", "FAIL"}]


def section_findings(section_name: str, findings: list[ValidationFinding]) -> list[ValidationFinding]:
    categories = set(SECTION_CATEGORIES.get(section_name, [section_name]))
    return [finding for finding in findings if finding.kategori_data in categories]


def _section_score(findings: list[ValidationFinding]) -> int:
    score = sum(DEFAULT_WEIGHTS.get(finding.severity, 0) for finding in actionable_findings(findings))
    return min(score, 100)


def _section_decision(findings: list[ValidationFinding]) -> str:
    active = actionable_findings(findings)
    if not active:
        return "Tidak ada catatan utama"
    counts = Counter(finding.severity for finding in active)
    score = _section_score(active)
    if counts["CRITICAL"] > 0 or counts["HIGH"] >= 3 or score >= 61:
        return "Perlu perbaikan sebelum validasi"
    if counts["HIGH"] > 0 or score >= 41:
        return "Perlu klarifikasi/perbaikan data"
    if counts["MEDIUM"] > 0 or counts["LOW"] > 0:
        return "Dapat diterima dengan catatan"
    return "Tidak ada catatan utama"


def generate_section_recommendation(section_name: str, findings: list[ValidationFinding]) -> str:
    related = section_findings(section_name, findings)
    active = actionable_findings(related)
    decision = _section_decision(related)
    score = _section_score(related)
    counts = Counter(finding.severity for finding in active)
    lines = [
        f"Rekomendasi bagian {section_name}: {decision}",
        f"Skor risiko bagian: {score}/100",
        "Temuan bagian: "
        + ", ".join(f"{severity}={counts.get(severity, 0)}" for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]),
    ]
    if active:
        lines.append("Catatan utama:")
        for index, finding in enumerate(top_findings(related, 5), start=1):
            lines.append(f"{index}. [{finding.severity}] {finding.deskripsi_temuan}")
            if finding.nilai_terdeteksi:
                lines.append(f"   Data: {finding.nilai_terdeteksi}")
            if finding.rekomendasi_tindak_lanjut:
                lines.append(f"   Tindak lanjut: {finding.rekomendasi_tindak_lanjut}")
    else:
        lines.append("Tidak ada warning/fail pada bagian ini berdasarkan rule yang sudah berjalan.")
    return "\n".join(lines)


def section_recommendations_table(findings: list[ValidationFinding]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for section_name in SECTION_CATEGORIES:
        related = section_findings(section_name, findings)
        active = actionable_findings(related)
        counts = Counter(finding.severity for finding in active)
        top = top_findings(related, 3)
        rows.append(
            {
                "Bagian": section_name,
                "Rekomendasi": _section_decision(related),
                "Risk Score Bagian": _section_score(related),
                "Critical": counts.get("CRITICAL", 0),
                "High": counts.get("HIGH", 0),
                "Medium": counts.get("MEDIUM", 0),
                "Low": counts.get("LOW", 0),
                "Temuan Utama": " | ".join(f"[{finding.severity}] {finding.deskripsi_temuan}" for finding in top),
            }
        )
    return rows


def generate_summary(report: dict[str, Any], result: ValidationResult) -> str:
    company = report.get("company_name") or "Perusahaan"
    counts = Counter(finding.severity for finding in result.findings if finding.status in {"WARNING", "FAIL"})
    important = top_findings(result.findings, 5)
    lines = [
        "A. Ringkasan Validasi",
        f"Perusahaan: {company}",
        f"Status rekomendasi: {result.recommendation}",
        f"Risk score: {result.risk_score}/100",
        "Jumlah temuan: "
        + ", ".join(f"{severity}={counts.get(severity, 0)}" for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]),
    ]
    if important:
        lines.append("Temuan paling penting:")
        for index, finding in enumerate(important, start=1):
            lines.append(f"{index}. [{finding.severity}] {finding.deskripsi_temuan} ({finding.nilai_terdeteksi})")
    else:
        lines.append("Tidak ada temuan warning/fail dari rule yang berjalan.")
    return "\n".join(lines)


def generate_findings_narrative(result: ValidationResult) -> str:
    lines = ["B. Temuan Utama"]
    important = top_findings(result.findings, 10)
    if not important:
        lines.append("Tidak ada temuan utama.")
        return "\n".join(lines)
    for index, finding in enumerate(important, start=1):
        lines.extend(
            [
                f"{index}. {finding.nama_rule} [{finding.severity}]",
                f"Apa masalahnya: {finding.deskripsi_temuan}",
                f"Data yang terdeteksi: {finding.nilai_terdeteksi or '-'}",
                f"Kenapa dianggap tidak wajar: {finding.dasar_perhitungan or '-'}",
                f"Dampak terhadap validitas laporan: {finding.rekomendasi_tindak_lanjut or '-'}",
                f"Pertanyaan klarifikasi: {finding.pertanyaan_klarifikasi_ke_perusahaan or '-'}",
                "",
            ]
        )
    return "\n".join(lines).strip()


def generate_copy_note(result: ValidationResult) -> str:
    important = top_findings(result.findings, 3)
    if not important:
        return (
            f"Rekomendasi aplikasi: {result.recommendation}. "
            "Data laporan telah diperiksa dengan aplikasi validasi internal dan tidak ditemukan anomali utama berdasarkan rule yang tersedia."
        )

    first = important[0]
    if first.severity in {"CRITICAL", "HIGH"}:
        prefix = "Mohon klarifikasi/perbaikan data"
    else:
        prefix = "Mohon konfirmasi data"
    details = []
    for finding in important:
        value = f" Data terdeteksi: {finding.nilai_terdeteksi}." if finding.nilai_terdeteksi else ""
        details.append(f"{finding.kategori_data}: {finding.deskripsi_temuan}.{value}")
    return (
        f"Rekomendasi aplikasi: {result.recommendation} dengan risk score {result.risk_score}/100. "
        f"{prefix} pada laporan perusahaan karena terdapat catatan berikut: "
        + " ".join(details)
    )


def generate_overall_validator_recommendation(result: ValidationResult) -> str:
    lines = [
        "Rekomendasi keseluruhan",
        f"Keputusan aplikasi: {result.recommendation}",
        f"Risk score: {result.risk_score}/100",
    ]
    active = actionable_findings(result.findings)
    if not active:
        lines.append("Tidak ada temuan warning/fail dari rule yang berjalan.")
        return "\n".join(lines)

    counts = Counter(finding.severity for finding in active)
    lines.append(
        "Jumlah temuan: "
        + ", ".join(f"{severity}={counts.get(severity, 0)}" for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"])
    )
    risky_sections = [
        row
        for row in section_recommendations_table(result.findings)
        if row["Risk Score Bagian"] > 0 or row["Critical"] or row["High"]
    ]
    if risky_sections:
        lines.append("Bagian yang perlu perhatian:")
        for row in sorted(risky_sections, key=lambda item: item["Risk Score Bagian"], reverse=True)[:6]:
            lines.append(f"- {row['Bagian']}: {row['Rekomendasi']} (score {row['Risk Score Bagian']}/100)")
    lines.append("Temuan prioritas:")
    for index, finding in enumerate(top_findings(result.findings, 5), start=1):
        lines.append(f"{index}. [{finding.severity}] {finding.kategori_data}: {finding.deskripsi_temuan}")
        if finding.nilai_terdeteksi:
            lines.append(f"   Data: {finding.nilai_terdeteksi}")
    return "\n".join(lines)


def findings_table(findings: list[ValidationFinding]) -> list[dict[str, Any]]:
    return [
        {
            "Kategori": finding.kategori_data,
            "Rule": finding.nama_rule,
            "Severity": finding.severity,
            "Status": finding.status,
            "Temuan": finding.deskripsi_temuan,
            "Nilai": finding.nilai_terdeteksi,
            "Rekomendasi": finding.rekomendasi_tindak_lanjut,
        }
        for finding in findings
    ]


def generate_full_narrative(report: dict[str, Any], result: ValidationResult) -> str:
    return "\n\n".join(
        [
            generate_summary(report, result),
            "B. Rekomendasi Per Bagian",
            "\n".join(
                f"- {row['Bagian']}: {row['Rekomendasi']} (score {row['Risk Score Bagian']}/100)"
                for row in section_recommendations_table(result.findings)
            ),
            generate_findings_narrative(result),
            "C. Rekomendasi Keseluruhan",
            generate_overall_validator_recommendation(result),
            "D. Catatan yang Siap Ditempel ke IntraNEW",
            generate_copy_note(result),
        ]
    )
