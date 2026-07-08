from __future__ import annotations

from typing import Any

from src.storage.models import ValidationFinding
from src.parser.number_normalizer import normalize_number
from src.validation.utils import approx_equal, canonical_key, first_number, percent_change, section, sum_numbers


def _finding(rule_id: str, severity: str, description: str, value: str, calculation: str, question: str) -> ValidationFinding:
    return ValidationFinding(
        rule_id=rule_id,
        nama_rule="Investasi dan komponen modal",
        kategori_data="Investasi",
        severity=severity,
        status="FAIL" if severity in {"HIGH", "CRITICAL"} else "WARNING",
        deskripsi_temuan=description,
        nilai_terdeteksi=value,
        dasar_perhitungan=calculation,
        rekomendasi_tindak_lanjut="Periksa total investasi, komponen tanah/bangunan/mesin/lainnya/modal kerja, serta perubahan dari periode sebelumnya.",
        pertanyaan_klarifikasi_ke_perusahaan=question,
    )


def _total_investment(rows: list[dict[str, Any]]) -> float:
    return sum_numbers(rows, ["total_investasi", "nilai_investasi", "investasi_pp_7", "investasi_tanpa_tanah"])


def _component_sum(rows: list[dict[str, Any]]) -> float:
    return sum_numbers(rows, ["tanah", "bangunan", "mesin", "lainnya", "modal_kerja"])


def _ownership_percentages(rows: list[dict[str, Any]]) -> list[tuple[str, float]]:
    ownerships: list[tuple[str, float]] = []
    ownership_labels = {
        "swasta_nasional",
        "pemerintah_pusat",
        "pemerintah_daerah",
        "asing",
    }
    for row in rows:
        items = list(row.items())
        if not items:
            continue

        first_key, first_value = items[0]
        first_key_canonical = canonical_key(first_key)
        first_value_canonical = canonical_key(first_value)
        label = str(first_value or first_key).strip()

        # IntraNEW often renders this as a two-column table:
        # first row header "Persentase Kepemilikan", following rows are
        # "Swasta Nasional | 100.00 %", etc. Investment rupiah rows can share
        # the same first-column header after parsing, so only values marked
        # with % are treated as percentages in this layout.
        if first_key_canonical == "persentase_kepemilikan" and first_value_canonical in ownership_labels:
            for _, value in items[1:]:
                text = str(value or "")
                if "%" not in text:
                    continue
                number = normalize_number(text)
                if number is not None:
                    ownerships.append((label, float(number)))
                    break
            continue

        for key, value in items:
            key_canonical = canonical_key(key)
            text = str(value or "")
            if "persentase" in key_canonical and "kepemilikan" in key_canonical:
                if key_canonical == "persentase_kepemilikan" and "%" not in text:
                    continue
                number = normalize_number(text)
                if number is not None and ("%" in text or 0 <= float(number) <= 100):
                    ownerships.append((str(key), float(number)))
    return ownerships


def run(report: dict[str, Any], context: dict[str, Any]) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    rows = section(report, "investasi")
    if not rows:
        return findings

    total = _total_investment(rows)
    components = _component_sum(rows)
    if total > 0 and components > 0 and not approx_equal(total, components, 5):
        findings.append(
            _finding(
                "INV_TOTAL_COMPONENT_MISMATCH",
                "MEDIUM",
                "Total investasi tidak mendekati penjumlahan komponen investasi.",
                f"total={total:g}; komponen={components:g}",
                "total investasi dibandingkan dengan tanah + bangunan + mesin + lainnya + modal kerja.",
                "Mohon cek apakah total investasi termasuk/mengecualikan tanah dan bangunan sesuai definisi kolom.",
            )
        )

    if total > 0 and components == 0:
        findings.append(
            _finding(
                "INV_TOTAL_WITHOUT_COMPONENTS",
                "MEDIUM",
                "Nilai total investasi ada tetapi komponen investasi kosong.",
                f"total={total:g}; komponen={components:g}",
                "Komponen investasi kosong membuat perubahan investasi sulit diverifikasi.",
                "Mohon lengkapi komponen tanah, bangunan, mesin, lainnya, dan/atau modal kerja bila tersedia.",
            )
        )

    previous = context.get("previous_report") or {}
    previous_total = _total_investment(section(previous, "investasi")) if previous else 0
    if previous_total > 0 and total > 0:
        change = percent_change(total, previous_total)
        if change is not None and change < -float(context.get("thresholds", {}).get("qoq_high_percent", 50)):
            findings.append(
                _finding(
                    "INV_DRASTIC_DROP",
                    "HIGH",
                    "Nilai investasi turun drastis dibanding periode sebelumnya.",
                    f"sebelumnya={previous_total:g}; sekarang={total:g}; perubahan={change:.1f}%",
                    "perubahan QoQ investasi dihitung dari database lokal/periode sebelumnya.",
                    "Mohon jelaskan penyebab penurunan nilai investasi atau cek kesalahan input.",
                )
            )

    ownerships = _ownership_percentages(rows)
    for label, ownership in ownerships:
        if ownership > 100:
            findings.append(
                _finding(
                    "INV_OWNERSHIP_OVER_100",
                    "HIGH",
                    "Persentase kepemilikan modal melebihi 100%.",
                    f"{label}: kepemilikan={ownership:g}%",
                    "Total persentase kepemilikan tidak boleh melebihi 100%.",
                    "Mohon cek kembali persentase kepemilikan modal dan negara asal investasi.",
                )
            )
    total_ownership = sum(value for _, value in ownerships)
    if ownerships and total_ownership > 100.5:
        findings.append(
            _finding(
                "INV_TOTAL_OWNERSHIP_OVER_100",
                "HIGH",
                "Total persentase kepemilikan modal melebihi 100%.",
                f"total_kepemilikan={total_ownership:g}%; rincian={ownerships}",
                "Total persentase kepemilikan dijumlahkan dari baris Swasta Nasional/Pemerintah/Asing.",
                "Mohon cek kembali pembagian persentase kepemilikan modal.",
            )
        )

    return findings
