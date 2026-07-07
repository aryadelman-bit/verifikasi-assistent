from __future__ import annotations

import re
from typing import Any


SECTION_KEYWORDS: dict[str, list[str]] = {
    "identitas": ["identitas", "legalitas", "alamat kantor", "alamat pabrik", "nib", "perizinan", "oss"],
    "umum": ["data umum", "periode laporan", "verifikator", "validator", "penanda tangan", "status berproduksi"],
    "investasi": ["investasi", "kepemilikan modal", "negara asal investasi"],
    "kapasitas": ["kapasitas produksi", "kapasitas terpasang", "kapasitas"],
    "produksi_penjualan": ["produksi dan penjualan", "produksi", "penjualan", "ekspor", "domestik"],
    "bahan_baku": ["bahan baku", "material utama"],
    "bahan_penolong": ["bahan penolong", "material penolong"],
    "tenaga_kerja": ["tenaga kerja", "pekerja", "pendidikan", "skkni", "sertifikasi kompetensi"],
    "prakerin": ["prakerin", "praktek kerja", "praktik kerja", "magang"],
    "air": ["penggunaan air", "air permukaan", "air tanah", "air daur ulang"],
    "energi": ["energi", "bahan bakar", "listrik", "pln", "mmbtu", "kwh"],
    "air_energi": ["air & energi", "air dan energi"],
    "pengeluaran": ["pengeluaran perusahaan", "upah", "gaji", "logistik", "litbang", "r&d"],
    "rencana_produksi": ["rencana produksi"],
    "mesin": ["mesin produksi", "mesin/peralatan", "peralatan produksi"],
    "persediaan": ["persediaan", "stok"],
    "limbah_padat": ["limbah padat"],
    "limbah_b3": ["limbah b3"],
    "limbah_cair": ["limbah cair", "cod inlet", "cod outlet", "sludge"],
    "indi_4_0": ["indi 4.0", "industri 4.0", "indi"],
    "surat_pernyataan": ["surat pernyataan"],
    "catatan_validasi": ["catatan validasi", "catatan", "permintaan data"],
}


def normalize_label(text: Any) -> str:
    value = str(text or "").strip().lower()
    value = value.replace("&", " dan ")
    value = re.sub(r"\s+", " ", value)
    return value


def canonical_section(label: Any) -> str:
    normalized = normalize_label(label)
    if not normalized:
        return "unknown"
    if normalized.startswith("kapasitas sebelum oss") or normalized.startswith("kapasitas oss"):
        return "kapasitas_referensi"
    best_section = ""
    best_score = 0
    for canonical, keywords in SECTION_KEYWORDS.items():
        matches = [keyword for keyword in keywords if keyword in normalized]
        if not matches:
            continue
        score = max(len(keyword) for keyword in matches)
        if score > best_score:
            best_section = canonical
            best_score = score
    if best_section:
        return best_section
    return re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")[:60] or "unknown"


def merge_section_records(target: dict[str, list[dict[str, Any]]], section: str, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    target.setdefault(section, []).extend(rows)
