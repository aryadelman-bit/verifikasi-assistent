from src.validation.rules_investment import run


def test_ownership_percentage_ignores_investment_rupiah_rows():
    report = {
        "sections": {
            "investasi": [
                {"Persentase Kepemilikan": "Swasta Nasional", "kolom_2": "100.00 %"},
                {"Persentase Kepemilikan": "Pemerintah Pusat", "kolom_2": "0.00 %"},
                {"Persentase Kepemilikan": "Investasi Laporan Sebelumnya Triwulan 4 2025", "kolom_2": "Investasi Laporan Triwulan"},
                {
                    "Persentase Kepemilikan": "IDR 7.387.200.000 (Tanah) IDR 7.134.322.249 (Bangunan)",
                    "kolom_2": "IDR 7.387.200.000 (Tanah) IDR 7.134.322.249 (Bangunan)",
                },
            ]
        }
    }
    findings = run(report, {"thresholds": {}})
    assert not any(f.rule_id in {"INV_OWNERSHIP_OVER_100", "INV_TOTAL_OWNERSHIP_OVER_100"} for f in findings)
