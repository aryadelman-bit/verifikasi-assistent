from __future__ import annotations

from datetime import datetime
from typing import Any

from src.storage.models import ValidationFinding
from src.validation.utils import first_number, first_value, section


def _finding(rule_id: str, severity: str, description: str, value: str, calculation: str, question: str) -> ValidationFinding:
    return ValidationFinding(
        rule_id=rule_id,
        nama_rule="Mesin produksi",
        kategori_data="Mesin",
        severity=severity,
        status="FAIL" if severity in {"HIGH", "CRITICAL"} else "WARNING",
        deskripsi_temuan=description,
        nilai_terdeteksi=value,
        dasar_perhitungan=calculation,
        rekomendasi_tindak_lanjut="Periksa detail mesin/peralatan, tahun, negara pembuat, teknologi, merek, tipe, dan jumlah operator.",
        pertanyaan_klarifikasi_ke_perusahaan=question,
    )


def run(report: dict[str, Any], context: dict[str, Any]) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    rows = section(report, "mesin")
    current_year = datetime.now().year
    old_age = float(context.get("thresholds", {}).get("old_machine_age_years", 25))
    missing_brand_or_tech = 0

    for row in rows:
        name = str(first_value(row, ["nama_mesin", "mesin", "peralatan"]) or "mesin")
        made_year = first_number(row, ["tahun_pembuatan"])
        acquired_year = first_number(row, ["tahun_perolehan"])
        country = first_value(row, ["negara_pembuat", "negara"])
        brand_type = first_value(row, ["merek", "tipe", "merek_dan_tipe"])
        technology = first_value(row, ["teknologi"])

        if made_year == 0:
            findings.append(
                _finding(
                    "MACH_MISSING_MANUFACTURE_YEAR",
                    "MEDIUM",
                    "Tahun pembuatan mesin kosong atau nol.",
                    name,
                    "Tahun pembuatan diperlukan untuk membaca umur mesin.",
                    "Mohon lengkapi tahun pembuatan mesin/peralatan.",
                )
            )
        if made_year > 0 and acquired_year > 0 and acquired_year < made_year:
            findings.append(
                _finding(
                    "MACH_ACQUIRED_BEFORE_MADE",
                    "HIGH",
                    "Tahun perolehan lebih awal daripada tahun pembuatan.",
                    f"{name}: tahun_pembuatan={made_year:g}; tahun_perolehan={acquired_year:g}",
                    "tahun perolehan tidak boleh lebih kecil dari tahun pembuatan.",
                    "Mohon cek kembali tahun pembuatan dan tahun perolehan mesin.",
                )
            )
        if not country:
            findings.append(
                _finding(
                    "MACH_MISSING_COUNTRY",
                    "LOW",
                    "Negara pembuat mesin kosong.",
                    name,
                    "Negara pembuat digunakan untuk membaca asal teknologi/peralatan.",
                    "Mohon lengkapi negara pembuat bila tersedia.",
                )
            )
        if not brand_type or not technology:
            missing_brand_or_tech += 1
        if made_year > 0:
            age = current_year - made_year
            if age > old_age:
                findings.append(
                    _finding(
                        "MACH_OLD_MACHINE_INFO",
                        "INFO",
                        "Umur mesin sangat tua secara indikatif.",
                        f"{name}: umur={age:g} tahun",
                        f"umur mesin = tahun berjalan - tahun pembuatan; threshold info {old_age:g} tahun.",
                        "Tidak harus invalid; gunakan sebagai catatan konteks kapasitas dan produktivitas.",
                    )
                )

    if rows and missing_brand_or_tech / len(rows) >= 0.5:
        findings.append(
            _finding(
                "MACH_MANY_MISSING_BRAND_TECH",
                "MEDIUM",
                "Banyak mesin belum memiliki merek/tipe atau teknologi.",
                f"{missing_brand_or_tech} dari {len(rows)} mesin",
                "Lebih dari separuh baris mesin tidak lengkap pada merek/tipe/teknologi.",
                "Mohon lengkapi merek, tipe, dan teknologi mesin utama.",
            )
        )

    return findings

