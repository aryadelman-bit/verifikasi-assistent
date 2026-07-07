from __future__ import annotations

from typing import Any

from src.storage.models import ValidationFinding
from src.validation.utils import first_number, is_food_report, section, sum_numbers


def _finding(rule_id: str, severity: str, description: str, value: str, calculation: str, question: str) -> ValidationFinding:
    return ValidationFinding(
        rule_id=rule_id,
        nama_rule="Air, energi, dan intensitas",
        kategori_data="Air & Energi",
        severity=severity,
        status="FAIL" if severity in {"HIGH", "CRITICAL"} else "WARNING",
        deskripsi_temuan=description,
        nilai_terdeteksi=value,
        dasar_perhitungan=calculation,
        rekomendasi_tindak_lanjut="Periksa kembali kWh, MMBTU, volume air, biaya, dan periode pencatatan utilitas.",
        pertanyaan_klarifikasi_ke_perusahaan=question,
    )


def run(report: dict[str, Any], context: dict[str, Any]) -> list[ValidationFinding]:
    thresholds = context.get("thresholds", {})
    findings: list[ValidationFinding] = []
    production_kg = sum_numbers(
        section(report, "produksi_penjualan"),
        ["jumlah_produksi_satuan_standar", "jumlah_dalam_kilogram", "jumlah_kg", "produksi_kg"],
    )
    energy_rows = section(report, "air_energi", "energi")
    water_rows = section(report, "air", "penggunaan_air")

    electricity_kwh = sum_numbers(energy_rows, ["kwh", "penggunaan_listrik", "listrik_pln", "listrik_non_pln"])
    electricity_value = sum_numbers(energy_rows, ["nilai_listrik", "biaya_listrik"])
    fuel_mmbtu = sum_numbers(energy_rows, ["mmbtu", "bahan_bakar", "gas"])
    fuel_value = sum_numbers(energy_rows, ["nilai_bahan_bakar", "nilai_gas", "biaya_gas"])
    water_m3 = sum_numbers(water_rows + energy_rows, ["m3", "volume_air", "air_permukaan", "air_tanah", "air_daur_ulang"])

    if production_kg > 0 and electricity_kwh == 0 and fuel_mmbtu == 0:
        findings.append(
            _finding(
                "UTIL_PRODUCTION_WITHOUT_ENERGY",
                "HIGH",
                "Produksi ada tetapi listrik dan bahan bakar nol/tidak terbaca.",
                f"produksi={production_kg:g} kg; listrik={electricity_kwh:g} kWh; bahan_bakar={fuel_mmbtu:g} MMBTU",
                "Produksi umumnya membutuhkan energi langsung atau tidak langsung.",
                "Mohon klarifikasi sumber energi produksi dan pastikan data utilitas sudah diisi.",
            )
        )

    if production_kg > 0 and is_food_report(report) and water_m3 == 0:
        findings.append(
            _finding(
                "UTIL_FOOD_WITHOUT_WATER",
                "MEDIUM",
                "Produksi pangan/olah pangan terdeteksi tetapi penggunaan air nol/tidak terbaca.",
                f"produksi={production_kg:g} kg; air={water_m3:g} m3",
                "Air sering relevan pada proses pangan/olah pangan, meski tidak selalu digunakan langsung.",
                "Mohon klarifikasi apakah proses menggunakan air atau terdapat data air yang belum dilaporkan.",
            )
        )

    if electricity_kwh > 0 and electricity_value > 0:
        cost = electricity_value / electricity_kwh
        min_cost = float(thresholds.get("electricity_cost_min_per_kwh", 500))
        max_cost = float(thresholds.get("electricity_cost_max_per_kwh", 5000))
        if cost < min_cost or cost > max_cost:
            findings.append(
                _finding(
                    "UTIL_ELECTRICITY_COST_OUTLIER",
                    "MEDIUM",
                    "Biaya listrik per kWh di luar rentang kewajaran konfigurasi.",
                    f"nilai=Rp{electricity_value:,.0f}; kWh={electricity_kwh:g}; biaya=Rp{cost:,.0f}/kWh".replace(",", "."),
                    f"biaya listrik per kWh = nilai listrik / kWh; rentang {min_cost:g}-{max_cost:g}.",
                    "Mohon cek nilai tagihan, kWh, atau satuan pelaporan listrik.",
                )
            )

    if fuel_mmbtu > 0 and fuel_value > 0:
        cost = fuel_value / fuel_mmbtu
        min_cost = float(thresholds.get("gas_cost_min_per_mmbtu", 20_000))
        max_cost = float(thresholds.get("gas_cost_max_per_mmbtu", 500_000))
        if cost < min_cost or cost > max_cost:
            findings.append(
                _finding(
                    "UTIL_GAS_COST_OUTLIER",
                    "MEDIUM",
                    "Biaya gas/bahan bakar per MMBTU di luar rentang kewajaran konfigurasi.",
                    f"nilai=Rp{fuel_value:,.0f}; MMBTU={fuel_mmbtu:g}; biaya=Rp{cost:,.0f}/MMBTU".replace(",", "."),
                    f"biaya gas per MMBTU = nilai gas / MMBTU; rentang {min_cost:g}-{max_cost:g}.",
                    "Mohon cek nilai bahan bakar, MMBTU, atau satuan energi yang digunakan.",
                )
            )

    return findings
