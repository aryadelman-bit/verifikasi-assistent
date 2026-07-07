from __future__ import annotations

from typing import Any

from src.storage.models import ValidationFinding
from src.validation.utils import first_number, first_value, is_food_report, section, sum_numbers


def _finding(rule_id: str, severity: str, description: str, value: str, calculation: str, question: str) -> ValidationFinding:
    return ValidationFinding(
        rule_id=rule_id,
        nama_rule="Kewajaran data limbah",
        kategori_data="Limbah",
        severity=severity,
        status="FAIL" if severity in {"HIGH", "CRITICAL"} else "WARNING",
        deskripsi_temuan=description,
        nilai_terdeteksi=value,
        dasar_perhitungan=calculation,
        rekomendasi_tindak_lanjut="Jangan menyimpulkan pelanggaran; gunakan sebagai dasar klarifikasi kewajaran data lingkungan.",
        pertanyaan_klarifikasi_ke_perusahaan=question,
    )


def run(report: dict[str, Any], context: dict[str, Any]) -> list[ValidationFinding]:
    thresholds = context.get("thresholds", {})
    findings: list[ValidationFinding] = []
    production_kg = sum_numbers(
        section(report, "produksi_penjualan"),
        ["jumlah_produksi_satuan_standar", "jumlah_dalam_kilogram", "jumlah_kg", "produksi_kg"],
    )
    solid = section(report, "limbah_padat")
    b3 = section(report, "limbah_b3")
    liquid = section(report, "limbah_cair")

    if production_kg > 0 and not solid and not b3:
        findings.append(
            _finding(
                "WASTE_NO_SOLID_DATA_WITH_PRODUCTION",
                "MEDIUM",
                "Produksi ada tetapi data limbah padat/B3 tidak terbaca.",
                f"produksi={production_kg:g} kg",
                "Aktivitas produksi umumnya menghasilkan catatan limbah atau pernyataan nihil.",
                "Mohon klarifikasi apakah memang tidak ada limbah padat/B3 atau data belum diisi.",
            )
        )

    if production_kg > 0 and is_food_report(report) and not liquid:
        findings.append(
            _finding(
                "WASTE_NO_LIQUID_DATA_FOOD",
                "MEDIUM",
                "Produksi pangan terdeteksi tetapi data limbah cair tidak terbaca.",
                f"produksi={production_kg:g} kg",
                "Untuk pangan/olah pangan, data limbah cair sering relevan dan perlu pernyataan nihil bila tidak ada.",
                "Mohon klarifikasi apakah proses produksi menghasilkan limbah cair dan bagaimana pencatatannya.",
            )
        )

    for row in liquid:
        cod_in = first_number(row, ["cod_inlet", "cod_in"])
        cod_out = first_number(row, ["cod_outlet", "cod_out"])
        debit_in = first_number(row, ["debit_limbah_cair_inlet", "debit_inlet", "debit"])
        sludge = first_number(row, ["sludge_removed", "sludge"])
        label = str(first_value(row, ["jenis_limbah", "keterangan", "periode"]) or "limbah cair")
        if cod_out > cod_in > 0:
            severity = "CRITICAL" if cod_out > cod_in * 1.5 else "HIGH"
            findings.append(
                _finding(
                    "WASTE_COD_OUTLET_OVER_INLET",
                    severity,
                    "COD outlet lebih tinggi daripada COD inlet setelah pengolahan.",
                    f"{label}: COD inlet={cod_in:g}; COD outlet={cod_out:g}",
                    "COD outlet seharusnya tidak lebih tinggi dari COD inlet pada proses pengolahan yang tercatat.",
                    "Mohon cek kembali angka COD inlet/outlet atau jelaskan kondisi proses pengolahan.",
                )
            )
        if cod_in == 0 and cod_out > 0:
            findings.append(
                _finding(
                    "WASTE_COD_INLET_ZERO_OUTLET_POSITIVE",
                    "HIGH",
                    "COD inlet nol tetapi COD outlet positif.",
                    f"{label}: COD inlet=0; COD outlet={cod_out:g}",
                    "Kombinasi ini tidak wajar untuk data inlet/outlet pada periode yang sama.",
                    "Mohon cek kembali apakah kolom inlet dan outlet tertukar atau ada salah input.",
                )
            )
        if debit_in > float(thresholds.get("max_reasonable_liquid_waste_m3_per_second", 10)):
            findings.append(
                _finding(
                    "WASTE_DEBIT_TOO_LARGE",
                    "HIGH",
                    "Debit limbah cair sangat besar dan mungkin salah satuan.",
                    f"{label}: debit={debit_in:g} m3/detik",
                    "Threshold default debit limbah cair m3/detik digunakan sebagai sanity check.",
                    "Mohon pastikan apakah satuan yang dimaksud m3/detik, m3/hari, atau satuan lain.",
                )
            )
        if debit_in == 0 and sludge > 0:
            findings.append(
                _finding(
                    "WASTE_SLUDGE_WITH_ZERO_DEBIT",
                    "MEDIUM",
                    "Sludge removed ada tetapi debit limbah cair nol.",
                    f"{label}: debit={debit_in:g}; sludge={sludge:g}",
                    "Sludge umumnya berkaitan dengan proses pengolahan limbah cair yang memiliki debit.",
                    "Mohon klarifikasi periode, satuan, atau sumber sludge removed.",
                )
            )

    return findings
