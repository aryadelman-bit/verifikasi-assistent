from __future__ import annotations

from typing import Any

from src.storage.models import ValidationFinding
from src.validation.utils import approx_equal, first_number, first_value, percent_change, product_name, section, sum_numbers


def _finding(rule_id: str, severity: str, description: str, value: str, calculation: str, question: str) -> ValidationFinding:
    return ValidationFinding(
        rule_id=rule_id,
        nama_rule="Produksi, penjualan, dan persediaan",
        kategori_data="Produksi & Persediaan",
        severity=severity,
        status="FAIL" if severity in {"HIGH", "CRITICAL"} else "WARNING",
        deskripsi_temuan=description,
        nilai_terdeteksi=value,
        dasar_perhitungan=calculation,
        rekomendasi_tindak_lanjut="Periksa hubungan produksi, penjualan, persediaan awal/akhir, dan nilai produk.",
        pertanyaan_klarifikasi_ke_perusahaan=question,
    )


def _qty_kg(row: dict[str, Any]) -> float:
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


def _sales_kg(row: dict[str, Any]) -> float:
    standard = first_number(
        row,
        [
            "jumlah_penjualan_satuan_standar",
            "penjualan_satuan_standar_kilogram",
            "penjualan_kg",
            "jumlah_penjualan_kg",
            "domestik_kg",
            "ekspor_kg",
            "terjual_kg",
        ],
    )
    if standard > 0:
        return standard
    return first_number(row, ["jumlah_penjualan"])


def _value(row: dict[str, Any]) -> float:
    return first_number(row, ["nilai_produksi", "nilai_penjualan", "nilai_produk", "nilai"])


def run(report: dict[str, Any], context: dict[str, Any]) -> list[ValidationFinding]:
    thresholds = context.get("thresholds", {})
    tolerance = float(thresholds.get("inventory_balance_tolerance_percent", 15))
    findings: list[ValidationFinding] = []
    production_rows = section(report, "produksi_penjualan")
    inventory_rows = section(report, "persediaan")
    plan_rows = section(report, "rencana_produksi")

    total_production = sum(_qty_kg(row) for row in production_rows)
    total_sales = sum(_sales_kg(row) for row in production_rows)
    inventory_start = sum_numbers(inventory_rows, ["nilai_awal", "persediaan_awal", "awal"])
    inventory_end = sum_numbers(inventory_rows, ["nilai_akhir", "persediaan_akhir", "akhir"])

    if inventory_rows and total_production > 0:
        expected_end = inventory_start + total_production - total_sales
        if total_sales > 0 and not approx_equal(expected_end, inventory_end, tolerance):
            findings.append(
                _finding(
                    "PROD_INV_BALANCE_MISMATCH",
                    "MEDIUM",
                    "Hubungan persediaan awal + produksi - penjualan tidak mendekati persediaan akhir.",
                    f"awal={inventory_start:g}; produksi={total_production:g}; penjualan={total_sales:g}; akhir={inventory_end:g}; ekspektasi={expected_end:g}",
                    "persediaan akhir kira-kira = persediaan awal + produksi - penjualan +/- penyesuaian.",
                    "Mohon jelaskan penyesuaian stok, retur, barang rusak, atau perbedaan satuan jika ada.",
                )
            )

    if inventory_start == 0 and inventory_end == 0 and (total_production > 0 or total_sales > 0):
        findings.append(
            _finding(
                "PROD_ZERO_INVENTORY_WITH_VOLUME",
                "MEDIUM",
                "Persediaan awal dan akhir nol meskipun produksi/penjualan tersedia.",
                f"produksi={total_production:g} kg; penjualan={total_sales:g} kg",
                "Persediaan nol pada awal dan akhir periode perlu klarifikasi bila volume aktivitas besar.",
                "Apakah perusahaan menerapkan produksi sesuai pesanan tanpa stok, atau ada persediaan yang belum dilaporkan?",
            )
        )

    for row in production_rows:
        product = product_name(row) or "produk"
        qty = _qty_kg(row)
        value = _value(row)
        if qty > 0 and value > 0:
            price = value / qty
            if price > float(thresholds.get("price_per_kg_warning_high", 1_000_000)):
                findings.append(
                    _finding(
                        "PROD_HIGH_PRICE_PER_KG",
                        "MEDIUM",
                        "Harga rata-rata produk per kg tinggi dan perlu dicek.",
                        f"{product}: nilai=Rp{value:,.0f}; jumlah={qty:g} kg; harga=Rp{price:,.0f}/kg".replace(",", "."),
                        "harga rata-rata produk = nilai produk / jumlah kg.",
                        "Mohon pastikan nilai produk dan konversi kilogram sudah sesuai.",
                    )
                )

    if plan_rows and total_production > 0:
        planned_qty = sum_numbers(plan_rows, ["jumlah_produk", "jumlah", "rencana"])
        if planned_qty > 0:
            change = percent_change(planned_qty, total_production)
            if change is not None and abs(change) > float(thresholds.get("product_plan_change_warning_percent", 50)):
                findings.append(
                    _finding(
                        "PROD_PLAN_FAR_FROM_ACTUAL",
                        "LOW",
                        "Rencana produksi jauh berbeda dari produksi aktual periode ini.",
                        f"aktual={total_production:g}; rencana={planned_qty:g}; selisih={change:.1f}%",
                        "perbandingan indikatif rencana produksi dengan produksi aktual.",
                        "Mohon jelaskan alasan perubahan rencana produksi bila relevan dengan validasi.",
                    )
                )

    return findings
