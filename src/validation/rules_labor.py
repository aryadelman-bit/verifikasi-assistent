from __future__ import annotations

from typing import Any

from src.storage.models import ValidationFinding
from src.validation.utils import first_number, percent_change, section, sum_numbers


def _finding(rule_id: str, severity: str, description: str, value: str, calculation: str, question: str) -> ValidationFinding:
    return ValidationFinding(
        rule_id=rule_id,
        nama_rule="Tenaga kerja dan produktivitas",
        kategori_data="Tenaga Kerja",
        severity=severity,
        status="FAIL" if severity in {"HIGH", "CRITICAL"} else "WARNING",
        deskripsi_temuan=description,
        nilai_terdeteksi=value,
        dasar_perhitungan=calculation,
        rekomendasi_tindak_lanjut="Periksa jumlah pekerja, pendidikan, sertifikasi, dan konsistensinya dengan volume produksi.",
        pertanyaan_klarifikasi_ke_perusahaan=question,
    )


def _labor_total(rows: list[dict[str, Any]]) -> float:
    patterns = [
        "produksi_tetap_laki",
        "produksi_tetap_perempuan",
        "produksi_tidak_tetap_laki",
        "produksi_tidak_tetap_perempuan",
        "lainnya_tetap_laki",
        "lainnya_tetap_perempuan",
        "lainnya_tidak_tetap_laki",
        "lainnya_tidak_tetap_perempuan",
        "rata_rata_pekerja",
        "total_pekerja",
    ]
    total = sum_numbers(rows, patterns)
    if total == 0:
        total = sum(first_number(row, ["jumlah"]) for row in rows)
    return total


def run(report: dict[str, Any], context: dict[str, Any]) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    rows = section(report, "tenaga_kerja")
    previous = context.get("previous_report") or {}
    production_kg = sum_numbers(
        section(report, "produksi_penjualan"),
        ["jumlah_produksi_satuan_standar", "jumlah_dalam_kilogram", "jumlah_kg", "produksi_kg"],
    )
    total_labor = _labor_total(rows)

    if production_kg > 0 and total_labor == 0:
        findings.append(
            _finding(
                "LAB_PRODUCTION_WITH_ZERO_LABOR",
                "HIGH",
                "Produksi besar terdeteksi tetapi tenaga kerja nol/tidak terbaca.",
                f"produksi={production_kg:g} kg; tenaga_kerja={total_labor:g}",
                "Produksi dengan tenaga kerja nol perlu klarifikasi, kecuali seluruh proses dialihkan/maklon/otomasi khusus.",
                "Mohon klarifikasi jumlah tenaga kerja atau mekanisme produksi pada periode laporan.",
            )
        )

    education_total = sum_numbers(rows, ["sd", "smp", "sma", "smk", "diploma", "sarjana", "s1", "s2", "s3"])
    if total_labor > 0 and education_total > 0 and abs(education_total - total_labor) > max(total_labor * 0.1, 5):
        findings.append(
            _finding(
                "LAB_EDUCATION_TOTAL_MISMATCH",
                "MEDIUM",
                "Total pendidikan berbeda signifikan dari total pekerja.",
                f"total_pekerja={total_labor:g}; total_pendidikan={education_total:g}",
                "total tingkat pendidikan seharusnya mendekati total pekerja.",
                "Mohon cek apakah seluruh pekerja sudah dikelompokkan menurut pendidikan.",
            )
        )

    if production_kg > 0 and total_labor > 0:
        productivity = production_kg / total_labor
        if productivity > 1_000_000:
            findings.append(
                _finding(
                    "LAB_PRODUCTIVITY_OUTLIER",
                    "LOW",
                    "Produktivitas kg per pekerja sangat tinggi secara indikatif.",
                    f"produksi={production_kg:g} kg; pekerja={total_labor:g}; produktivitas={productivity:g} kg/pekerja",
                    "produktivitas = produksi kg / total tenaga kerja.",
                    "Mohon cek apakah jumlah pekerja rata-rata dan produksi kg sudah benar.",
                )
            )

    previous_labor = _labor_total(section(previous, "tenaga_kerja")) if previous else 0
    if previous_labor > 0 and total_labor > 0:
        change = percent_change(total_labor, previous_labor)
        if change is not None and abs(change) > float(context.get("thresholds", {}).get("qoq_high_percent", 50)):
            findings.append(
                _finding(
                    "LAB_QOQ_EXTREME_CHANGE",
                    "HIGH",
                    "Jumlah tenaga kerja berubah ekstrem dibanding periode sebelumnya.",
                    f"sebelumnya={previous_labor:g}; sekarang={total_labor:g}; perubahan={change:.1f}%",
                    "perubahan QoQ = (sekarang - sebelumnya) / sebelumnya.",
                    "Mohon jelaskan perubahan tenaga kerja yang signifikan pada periode ini.",
                )
            )

    return findings
