from __future__ import annotations

from typing import Any

from src.storage.models import ValidationFinding
from src.validation.utils import first_value, hs_code, kbli_code, product_name, section


def _finding(rule_id: str, severity: str, description: str, value: str, calculation: str, question: str) -> ValidationFinding:
    return ValidationFinding(
        rule_id=rule_id,
        nama_rule="Konsistensi identitas, KBLI, dan HS",
        kategori_data="Identitas/KBLI/HS",
        severity=severity,
        status="FAIL" if severity in {"HIGH", "CRITICAL"} else "WARNING",
        deskripsi_temuan=description,
        nilai_terdeteksi=value,
        dasar_perhitungan=calculation,
        rekomendasi_tindak_lanjut="Periksa nama produk, KBLI, dan kode HS. Mapping awal dapat diperluas melalui config/kbli_hs_mapping.csv.",
        pertanyaan_klarifikasi_ke_perusahaan=question,
    )


def run(report: dict[str, Any], context: dict[str, Any]) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    rows = section(report, "produksi_penjualan") + section(report, "kapasitas") + section(report, "rencana_produksi")
    mappings = context.get("mappings", []) or []

    for row in rows:
        product = product_name(row)
        kbli = kbli_code(row)
        raw_hs = str(first_value(row, ["kode_hs", "hs"]) or "").strip()
        normalized_hs = hs_code(row)
        if raw_hs and normalized_hs:
            digits = "".join(ch for ch in raw_hs if ch.isdigit())
            if len(digits) != 8:
                findings.append(
                    _finding(
                        "ID_HS_NORMALIZED_TO_8_DIGITS",
                        "LOW",
                        "Kode HS tidak berformat 8 digit dan perlu normalisasi.",
                        f"{product or '-'}: HS asli={raw_hs}; normalisasi={normalized_hs}",
                        "Kode HS dinormalisasi dengan mengambil digit dan melengkapi ke 8 digit.",
                        "Mohon pastikan kode HS 8 digit yang benar untuk produk tersebut.",
                    )
                )

        if not product or not kbli or not normalized_hs:
            continue

        product_lower = product.lower()
        for mapping in mappings:
            map_kbli = str(mapping.get("kbli", "")).strip()
            keyword = str(mapping.get("keyword", "")).strip().lower()
            hs_prefix = str(mapping.get("expected_hs_prefix", "")).strip()
            if not hs_prefix:
                continue
            mapping_applies = (map_kbli and map_kbli == kbli) or (keyword and keyword in product_lower)
            if mapping_applies and not normalized_hs.startswith(hs_prefix):
                findings.append(
                    _finding(
                        "ID_HS_KBLI_MAPPING_MISMATCH",
                        "MEDIUM",
                        "Kode HS tidak sesuai dengan mapping awal KBLI/produk.",
                        f"produk={product}; KBLI={kbli}; HS={normalized_hs}; expected_prefix={hs_prefix}",
                        "Mapping sederhana membaca KBLI/keyword produk dan prefix HS yang diharapkan.",
                        "Mohon cek kembali kode HS atau perluas mapping konfigurasi bila produk memang pengecualian.",
                    )
                )
                break

    return findings
