from __future__ import annotations

from typing import Any

from src.storage.models import ValidationFinding
from src.validation.utils import (
    first_value,
    has_records,
    hs_code,
    kbli_code,
    metadata,
    product_name,
    section,
    sum_numbers,
)


def _finding(rule_id: str, name: str, severity: str, description: str, value: str, recommendation: str) -> ValidationFinding:
    return ValidationFinding(
        rule_id=rule_id,
        nama_rule=name,
        kategori_data="Kelengkapan Data",
        severity=severity,
        status="WARNING" if severity in {"INFO", "LOW", "MEDIUM"} else "FAIL",
        deskripsi_temuan=description,
        nilai_terdeteksi=value,
        dasar_perhitungan="Pemeriksaan kelengkapan section dan field kunci laporan.",
        rekomendasi_tindak_lanjut=recommendation,
        pertanyaan_klarifikasi_ke_perusahaan="Mohon lengkapi atau klarifikasi bagian data yang masih kosong/tidak terbaca.",
    )


def run(report: dict[str, Any], context: dict[str, Any]) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    required_sections = context.get("rule_config", {}).get("required_sections", [])
    for section_name in required_sections:
        records = section(report, section_name)
        if section_name in {"identitas", "umum"}:
            present = bool(report.get("identity") or report.get("general"))
        elif section_name == "surat_pernyataan":
            present = bool(metadata(report, "surat_pernyataan", "link_surat_pernyataan")) or has_records(records)
        else:
            present = has_records(records)
        if not present:
            findings.append(
                _finding(
                    f"COMP_EMPTY_{section_name.upper()}",
                    "Bagian wajib kosong/tidak terbaca",
                    "MEDIUM",
                    f"Bagian {section_name.replace('_', ' ')} tidak memiliki data terstruktur.",
                    section_name,
                    "Buka detail laporan, pastikan tombol Buka sudah diklik, dan minta perusahaan melengkapi jika memang kosong.",
                )
            )

    production = section(report, "produksi_penjualan")
    materials = section(report, "bahan_baku")
    inventory = section(report, "persediaan")
    energy = section(report, "air_energi", "energi")
    water = section(report, "air", "penggunaan_air")
    status_produksi = str(metadata(report, "status_berproduksi", "status produksi", "berproduksi")).lower()
    producing_status = any(token in status_produksi for token in ["buka", "berproduksi", "produksi", "aktif"])
    production_kg = sum_numbers(production, ["kg", "kilogram", "jumlah_dalam_kilogram", "jumlah_produksi"])

    if producing_status and not has_records(production):
        findings.append(
            _finding(
                "COMP_PRODUCING_WITHOUT_PRODUCTION",
                "Status berproduksi tetapi produksi kosong",
                "HIGH",
                "Laporan menyatakan perusahaan berproduksi, namun tabel produksi/penjualan kosong.",
                f"status={status_produksi}",
                "Minta perusahaan mengisi data produksi atau memperbaiki status berproduksi.",
            )
        )

    if has_records(production) and not has_records(materials):
        findings.append(
            _finding(
                "COMP_PRODUCTION_WITHOUT_MATERIAL",
                "Produksi ada tetapi bahan baku kosong",
                "HIGH",
                "Data produksi tersedia, namun bahan baku tidak terisi atau tidak terbaca.",
                f"total_produksi_kg={production_kg:g}",
                "Minta rincian bahan baku dalam negeri/impor yang digunakan selama periode laporan.",
            )
        )

    energy_total = sum_numbers(energy, ["kwh", "mmbtu", "jumlah", "volume", "nilai"]) + sum_numbers(water, ["m3", "volume", "biaya"])
    if production_kg > 0 and energy_total == 0:
        findings.append(
            _finding(
                "COMP_PRODUCTION_WITHOUT_UTILITY",
                "Produksi ada tetapi air/energi nol",
                "HIGH",
                "Produksi tercatat lebih dari nol, namun data listrik, bahan bakar, dan air semuanya nol/tidak terbaca.",
                f"produksi_kg={production_kg:g}; utilitas={energy_total:g}",
                "Minta perusahaan memeriksa kembali pemakaian listrik, bahan bakar, dan/atau air.",
            )
        )

    surat = str(metadata(report, "surat_pernyataan", "link_surat_pernyataan") or "")
    if not surat and not has_records(section(report, "surat_pernyataan")):
        findings.append(
            _finding(
                "COMP_MISSING_STATEMENT_LETTER",
                "Surat pernyataan tidak ditemukan",
                "HIGH",
                "Link/file surat pernyataan belum tersedia pada data yang terbaca.",
                "kosong",
                "Minta perusahaan mengunggah surat pernyataan sesuai ketentuan sebelum validasi.",
            )
        )

    signer = metadata(report, "nama_penanda_tangan", "penanda_tangan")
    signer_role = metadata(report, "jabatan_penanda_tangan", "jabatan")
    if not signer or not signer_role:
        findings.append(
            _finding(
                "COMP_MISSING_SIGNER",
                "Penanda tangan atau jabatan kosong",
                "MEDIUM",
                "Nama penanda tangan laporan atau jabatannya belum lengkap.",
                f"nama={signer or '-'}; jabatan={signer_role or '-'}",
                "Minta perusahaan melengkapi identitas penanda tangan laporan.",
            )
        )

    if production:
        main_product = production[0]
        missing = []
        if not product_name(main_product):
            missing.append("produk")
        if not kbli_code(main_product):
            missing.append("KBLI")
        if not hs_code(main_product):
            missing.append("HS")
        if missing:
            findings.append(
                _finding(
                    "COMP_MISSING_MAIN_PRODUCT_CODES",
                    "Produk utama belum lengkap KBLI/HS",
                    "HIGH",
                    "Produk utama tidak memiliki identitas produk, KBLI, atau HS yang lengkap.",
                    ", ".join(missing),
                    "Minta perusahaan melengkapi KBLI dan kode HS produk utama.",
                )
            )

    inventory_total = sum_numbers(inventory, ["nilai_awal", "nilai_akhir", "awal", "akhir"])
    if production_kg > 0 and has_records(materials) and inventory_total == 0:
        findings.append(
            _finding(
                "COMP_ZERO_INVENTORY_WITH_ACTIVITY",
                "Persediaan nol padahal ada aktivitas produksi/bahan baku",
                "MEDIUM",
                "Persediaan awal dan akhir terbaca nol/kosong sementara produksi atau bahan baku tersedia.",
                f"produksi_kg={production_kg:g}; persediaan={inventory_total:g}",
                "Klarifikasi apakah seluruh persediaan memang habis pada awal dan akhir periode atau ada bagian yang belum diisi.",
            )
        )

    return findings

