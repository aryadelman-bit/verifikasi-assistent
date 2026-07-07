from __future__ import annotations

from typing import Any

from src.storage.models import ValidationFinding
from src.validation.utils import first_number, first_value, is_food_report, product_name, row_text, section, sum_numbers


def _finding(rule_id: str, severity: str, description: str, value: str, calculation: str, question: str) -> ValidationFinding:
    return ValidationFinding(
        rule_id=rule_id,
        nama_rule="Bahan baku dan rasio input-output",
        kategori_data="Bahan Baku",
        severity=severity,
        status="FAIL" if severity in {"HIGH", "CRITICAL"} else "WARNING",
        deskripsi_temuan=description,
        nilai_terdeteksi=value,
        dasar_perhitungan=calculation,
        rekomendasi_tindak_lanjut="Periksa kembali jumlah, satuan, nilai rupiah, dan konversi kilogram bahan baku.",
        pertanyaan_klarifikasi_ke_perusahaan=question,
    )


def _material_qty_kg(row: dict[str, Any]) -> float:
    domestic = first_number(row, ["jumlah_dalam_negeri_kilogram", "dalam_negeri_kg", "jumlah_dn_kg"])
    imported = first_number(row, ["jumlah_impor_kilogram", "impor_kg", "jumlah_import_kg"])
    explicit_total = first_number(row, ["jumlah_dalam_kilogram", "jumlah_kg", "total_kg", "kilogram"])
    return domestic + imported + explicit_total


def _material_value(row: dict[str, Any]) -> float:
    domestic = first_number(row, ["nilai_dalam_negeri", "nilai_dn"])
    imported = first_number(row, ["nilai_impor", "nilai_import"])
    explicit_total = first_number(row, ["nilai_total", "nilai_bahan", "nilai"])
    return domestic + imported + explicit_total


def run(report: dict[str, Any], context: dict[str, Any]) -> list[ValidationFinding]:
    thresholds = context.get("thresholds", {})
    max_food_price = float(thresholds.get("max_food_material_price_per_kg", 5_000_000))
    low_ratio = float(thresholds.get("material_ratio_low_food", 0.2))
    high_ratio = float(thresholds.get("material_ratio_high_food", 5))

    findings: list[ValidationFinding] = []
    material_rows = section(report, "bahan_baku")
    helper_rows = section(report, "bahan_penolong")
    production_rows = section(report, "produksi_penjualan")
    total_material_kg = sum(_material_qty_kg(row) for row in material_rows)
    total_production_kg = sum_numbers(
        production_rows,
        ["jumlah_produksi_satuan_standar", "jumlah_dalam_kilogram", "jumlah_kg", "produksi_kg"],
    )

    for row in material_rows:
        name = str(first_value(row, ["nama_bahan_baku", "bahan_baku", "nama"]) or "bahan baku")
        qty = _material_qty_kg(row)
        value = _material_value(row)
        price = value / qty if qty > 0 else None
        if qty > 0 and value == 0:
            findings.append(
                _finding(
                    "MAT_QTY_WITH_ZERO_VALUE",
                    "HIGH",
                    "Jumlah bahan baku ada tetapi nilai rupiah nol.",
                    f"{name}: jumlah={qty:g} kg; nilai=0",
                    "nilai per kg tidak dapat dihitung karena nilai nol.",
                    "Mohon pastikan nilai bahan baku sudah diisi sesuai realisasi pembelian/pemakaian.",
                )
            )
        if qty == 0 and value > 0:
            findings.append(
                _finding(
                    "MAT_VALUE_WITH_ZERO_QTY",
                    "HIGH",
                    "Nilai bahan baku ada tetapi jumlah kilogram nol.",
                    f"{name}: jumlah=0 kg; nilai={value:g}",
                    "jumlah nol dengan nilai positif menunjukkan kemungkinan salah satuan/kolom.",
                    "Mohon pastikan jumlah bahan baku dan konversi kilogram sudah benar.",
                )
            )
        if price is not None and price > max_food_price:
            findings.append(
                _finding(
                    "MAT_EXTREME_PRICE_PER_KG",
                    "CRITICAL",
                    "Harga bahan baku per kg sangat tidak wajar.",
                    f"{name}: {qty:g} kg; nilai=Rp{value:,.0f}; harga=Rp{price:,.0f}/kg".replace(",", "."),
                    f"harga per kg = nilai / jumlah kg; threshold default Rp{max_food_price:,.0f}/kg".replace(",", "."),
                    "Mohon periksa apakah jumlah, satuan, atau nilai bahan baku salah input.",
                )
            )
        elif price is not None and price > float(thresholds.get("price_per_kg_warning_high", 1_000_000)):
            findings.append(
                _finding(
                    "MAT_HIGH_PRICE_PER_KG",
                    "HIGH",
                    "Harga bahan baku per kg tinggi dan perlu klarifikasi.",
                    f"{name}: harga=Rp{price:,.0f}/kg".replace(",", "."),
                    "harga per kg = nilai / jumlah kg.",
                    "Mohon jelaskan komoditas, kualitas, atau satuan yang menyebabkan harga per kg tinggi.",
                )
            )

    for row in helper_rows:
        name = str(first_value(row, ["nama_bahan_penolong", "bahan_penolong", "nama"]) or "bahan penolong")
        qty = _material_qty_kg(row)
        value = _material_value(row)
        raw_unit = str(first_value(row, ["satuan_asli", "satuan"]) or "").lower()
        if value > 0 and qty > 0 and value / qty > float(thresholds.get("price_per_kg_warning_high", 1_000_000)):
            findings.append(
                ValidationFinding(
                    rule_id="HELPER_HIGH_PRICE_PER_KG",
                    nama_rule="Bahan penolong",
                    kategori_data="Bahan Penolong",
                    severity="MEDIUM",
                    status="WARNING",
                    deskripsi_temuan="Nilai bahan penolong besar dibanding jumlah kilogram yang dilaporkan.",
                    nilai_terdeteksi=f"{name}: jumlah={qty:g} kg; nilai=Rp{value:,.0f}; harga=Rp{value / qty:,.0f}/kg".replace(",", "."),
                    dasar_perhitungan="harga per kg = nilai / jumlah kg.",
                    rekomendasi_tindak_lanjut="Periksa satuan, nilai, dan konversi kg bahan penolong.",
                    pertanyaan_klarifikasi_ke_perusahaan="Mohon klarifikasi satuan dan nilai bahan penolong tersebut.",
                )
            )
        if value > 0 and qty == 0 and not any(unit in raw_unit for unit in ["pcs", "piece", "karton", "box", "buah"]):
            findings.append(
                ValidationFinding(
                    rule_id="HELPER_VALUE_WITHOUT_KG_CONVERSION",
                    nama_rule="Bahan penolong",
                    kategori_data="Bahan Penolong",
                    severity="MEDIUM",
                    status="WARNING",
                    deskripsi_temuan="Bahan penolong memiliki nilai tetapi konversi kg kosong/tidak terbaca.",
                    nilai_terdeteksi=f"{name}: nilai=Rp{value:,.0f}; satuan={raw_unit or '-'}".replace(",", "."),
                    dasar_perhitungan="Konversi kg dicek hanya bila satuan bukan kemasan seperti karton/piece/box.",
                    rekomendasi_tindak_lanjut="Lengkapi konversi kg bila memang relevan untuk bahan penolong tersebut.",
                    pertanyaan_klarifikasi_ke_perusahaan="Apakah bahan penolong ini memiliki konversi kilogram atau hanya dilaporkan dalam satuan kemasan?",
                )
            )

    if total_production_kg > 0 and total_material_kg <= 0:
        findings.append(
            _finding(
                "MAT_PRODUCTION_WITHOUT_MATERIAL_KG",
                "CRITICAL",
                "Produksi lebih dari nol tetapi total bahan baku kg nol.",
                f"produksi={total_production_kg:g} kg; bahan_baku={total_material_kg:g} kg",
                "total bahan baku kg dijumlahkan dari bahan baku dalam negeri dan impor.",
                "Mohon isi atau koreksi jumlah bahan baku yang digunakan.",
            )
        )

    if total_production_kg > 0 and total_material_kg > 0:
        ratio = total_material_kg / total_production_kg
        food_context = is_food_report(report) or any(
            keyword in row_text(row)
            for row in production_rows + material_rows
            for keyword in ["daging", "ayam", "sapi", "roti", "kue", "bumbu", "pangan"]
        )
        if food_context and ratio < low_ratio:
            findings.append(
                _finding(
                    "MAT_LOW_INPUT_OUTPUT_RATIO",
                    "HIGH",
                    "Rasio bahan baku terhadap produksi terlalu rendah untuk produk pangan olahan.",
                    f"bahan_baku={total_material_kg:g} kg; produksi={total_production_kg:g} kg; rasio={ratio:.3f}",
                    f"rasio = total bahan baku kg / total produksi kg; threshold rendah {low_ratio:g}.",
                    "Mohon klarifikasi apakah seluruh bahan baku utama sudah dilaporkan dan satuan kilogram sudah benar.",
                )
            )
        if ratio > high_ratio:
            findings.append(
                _finding(
                    "MAT_HIGH_INPUT_OUTPUT_RATIO",
                    "HIGH",
                    "Rasio bahan baku terhadap produksi terlalu tinggi.",
                    f"bahan_baku={total_material_kg:g} kg; produksi={total_production_kg:g} kg; rasio={ratio:.3f}",
                    f"rasio = total bahan baku kg / total produksi kg; threshold tinggi {high_ratio:g}.",
                    "Mohon klarifikasi stok, pemakaian bahan baku, retur, atau salah satuan.",
                )
            )

    return findings
