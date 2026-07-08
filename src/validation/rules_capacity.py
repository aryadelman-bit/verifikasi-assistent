from __future__ import annotations

from typing import Any

from src.storage.models import ValidationFinding
from src.validation.utils import first_number, first_value, metadata, product_name, section, sum_numbers


def _finding(rule_id: str, severity: str, description: str, value: str, calculation: str, question: str) -> ValidationFinding:
    return ValidationFinding(
        rule_id=rule_id,
        nama_rule="Kapasitas dan utilisasi produksi",
        kategori_data="Kapasitas Produksi",
        severity=severity,
        status="FAIL" if severity in {"HIGH", "CRITICAL"} else "WARNING",
        deskripsi_temuan=description,
        nilai_terdeteksi=value,
        dasar_perhitungan=calculation,
        rekomendasi_tindak_lanjut="Periksa kembali satuan, konversi kilogram, kapasitas terpasang, dan jumlah produksi pada periode laporan.",
        pertanyaan_klarifikasi_ke_perusahaan=question,
    )


def _capacity_kg(row: dict[str, Any]) -> float:
    standard = first_number(
        row,
        [
            "kapasitas_terpasang_dalam_satuan_standar",
            "kapasitas_terpasang_standar",
            "terpasang_dalam_satuan_standar",
            "kapasitas_terpasang_kg",
            "terpasang_standar",
            "terpasang_kilogram",
        ],
    )
    if standard > 0:
        return standard
    return first_number(
        row,
        [
            "kapasitas_terpasang",
        ],
    )


def _production_capacity_kg(row: dict[str, Any]) -> float:
    standard = first_number(
        row,
        [
            "kapasitas_produksi_dalam_satuan_standar",
            "kapasitas_produksi_standar",
            "produksi_dalam_satuan_standar",
            "kapasitas_produksi_kg",
            "produksi_standar",
        ],
    )
    if standard > 0:
        return standard
    return first_number(
        row,
        [
            "kapasitas_produksi",
        ],
    )


def _production_kg(row: dict[str, Any]) -> float:
    standard = first_number(
        row,
        [
            "jumlah_produksi_satuan_standar",
            "produksi_satuan_standar_kilogram",
            "jumlah_dalam_kilogram",
            "jumlah_kg",
            "produksi_kg",
        ],
    )
    if standard > 0:
        return standard
    return first_number(row, ["jumlah_produksi"])


def _match_production(product: str, production_rows: list[dict[str, Any]]) -> float:
    if not production_rows:
        return 0.0
    if product:
        product_lower = product.lower()
        matched = [
            _production_kg(row)
            for row in production_rows
            if product_lower in product_name(row).lower() or product_name(row).lower() in product_lower
        ]
        if matched:
            return sum(matched)
    return sum(_production_kg(row) for row in production_rows)


def run(report: dict[str, Any], context: dict[str, Any]) -> list[ValidationFinding]:
    thresholds = context.get("thresholds", {})
    max_util = float(thresholds.get("max_utilization_percent", 100))
    critical_util = float(thresholds.get("critical_utilization_percent", 120))
    low_util = float(thresholds.get("low_utilization_percent", 5))
    findings: list[ValidationFinding] = []

    capacity_rows = section(report, "kapasitas")
    production_rows = section(report, "produksi_penjualan")
    status_produksi = str(metadata(report, "status_berproduksi", "status produksi", "berproduksi")).lower()
    producing_status = any(token in status_produksi for token in ["buka", "berproduksi", "produksi", "aktif"])

    if capacity_rows:
        for row in capacity_rows:
            product = product_name(row) or "produk"
            installed = _capacity_kg(row)
            production_capacity = _production_capacity_kg(row)
            production = _match_production(product, production_rows)
            if installed > 0:
                utilization = production / installed * 100
                if production > installed:
                    severity = "CRITICAL" if utilization > critical_util else "HIGH"
                    findings.append(
                        _finding(
                            "CAP_PRODUCTION_OVER_INSTALLED",
                            severity,
                            "Produksi melebihi kapasitas terpasang standar.",
                            f"{product}: produksi={production:g} kg; kapasitas_terpasang={installed:g} kg; utilisasi={utilization:.2f}%",
                            "utilisasi = produksi standar kg / kapasitas terpasang standar kg",
                            "Apakah kapasitas terpasang, realisasi produksi, atau satuan konversi kilogram sudah benar?",
                        )
                    )
                elif producing_status and utilization == 0:
                    findings.append(
                        _finding(
                            "CAP_ZERO_UTILIZATION_WHILE_PRODUCING",
                            "HIGH",
                            "Utilisasi 0% padahal status perusahaan berproduksi.",
                            f"{product}: produksi={production:g} kg; kapasitas={installed:g} kg",
                            "utilisasi = 0 karena produksi kg terbaca nol.",
                            "Mohon klarifikasi apakah tidak ada produksi pada periode ini atau data produksi belum diisi.",
                        )
                    )
                elif 0 < utilization < low_util:
                    findings.append(
                        _finding(
                            "CAP_VERY_LOW_UTILIZATION",
                            "MEDIUM",
                            "Utilisasi kapasitas sangat rendah.",
                            f"{product}: utilisasi={utilization:.2f}%",
                            f"Threshold utilisasi rendah < {low_util:g}%.",
                            "Mohon jelaskan penyebab utilisasi sangat rendah pada periode laporan.",
                        )
                    )

            if production_capacity > 0 and installed > 0 and production_capacity > installed:
                findings.append(
                    _finding(
                        "CAP_PRODUCTION_CAPACITY_OVER_INSTALLED",
                        "HIGH",
                        "Kapasitas produksi lebih besar dari kapasitas terpasang.",
                        f"{product}: kapasitas_produksi={production_capacity:g} kg; kapasitas_terpasang={installed:g} kg",
                        "Kapasitas produksi seharusnya tidak melampaui kapasitas terpasang tanpa penjelasan satuan/periode.",
                        "Mohon cek kembali kolom kapasitas produksi dan kapasitas terpasang.",
                    )
                )

            original_unit = str(first_value(row, ["satuan_asli", "satuan"]) or "").lower()
            original_capacity = first_number(
                row,
                [
                    "kapasitas_terpasang_dalam_satuan_asli",
                    "kapasitas_terpasang_satuan_asli",
                    "kapasitas_satuan_asli",
                ],
            )
            standard_capacity = installed
            if "ton" in original_unit and original_capacity > 0 and standard_capacity > 0:
                expected_kg = original_capacity * 1000
                if abs(expected_kg - standard_capacity) > max(expected_kg * 0.01, 1):
                    findings.append(
                        _finding(
                            "CAP_TON_TO_KG_CONVERSION",
                            "HIGH",
                            "Konversi ton ke kilogram tidak konsisten.",
                            f"{product}: {original_capacity:g} ton terbaca menjadi {standard_capacity:g} kg",
                            "1 ton harus setara 1.000 kg.",
                            "Mohon pastikan konversi satuan asli ke kilogram sudah benar.",
                        )
                    )

    elif production_rows and sum_numbers(production_rows, ["kg", "kilogram", "jumlah_produksi"]) > 0:
        findings.append(
            _finding(
                "CAP_MISSING_CAPACITY_WITH_PRODUCTION",
                "MEDIUM",
                "Produksi tersedia tetapi tabel kapasitas tidak terbaca.",
                "kapasitas kosong",
                "Validasi utilisasi tidak dapat dihitung tanpa kapasitas terpasang.",
                "Mohon lengkapi atau klarifikasi kapasitas produksi/terpasang.",
            )
        )

    return findings
