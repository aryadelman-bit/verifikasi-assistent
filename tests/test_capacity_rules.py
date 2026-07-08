from src.validation.rules_capacity import run


def test_capacity_flags_production_over_installed():
    report = {
        "general": {"status_berproduksi": "Buka/berproduksi"},
        "sections": {
            "kapasitas": [
                {"produk": "Roti", "kapasitas_terpasang_standar_kg": "100.000", "kapasitas_produksi_standar_kg": "100.000"}
            ],
            "produksi_penjualan": [{"produk": "Roti", "jumlah_dalam_kilogram": "150.000"}],
        },
    }
    findings = run(report, {"thresholds": {"max_utilization_percent": 100, "critical_utilization_percent": 120}})
    assert any(f.rule_id == "CAP_PRODUCTION_OVER_INSTALLED" and f.severity == "CRITICAL" for f in findings)


def test_capacity_ton_to_kg_conversion():
    report = {
        "sections": {
            "kapasitas": [
                {
                    "produk": "Bumbu",
                    "satuan_asli": "ton",
                    "kapasitas_terpasang_satuan_asli": "100",
                    "kapasitas_terpasang_standar_kg": "10.000",
                }
            ],
            "produksi_penjualan": [],
        }
    }
    findings = run(report, {"thresholds": {}})
    assert any(f.rule_id == "CAP_TON_TO_KG_CONVERSION" for f in findings)


def test_capacity_uses_standard_kilogram_before_original_unit():
    report = {
        "general": {"status_berproduksi": "Buka/berproduksi"},
        "sections": {
            "kapasitas": [
                {
                    "Produk": "Sosis",
                    "Kapasitas Produksi Dalam Satuan Asli": "100 ton",
                    "Kapasitas Terpasang Dalam Satuan Asli": "166,7 ton",
                    "Kapasitas Produksi Dalam Satuan Standar": "100.000 Kilogram",
                    "Kapasitas Terpasang Dalam Satuan Standar": "166.670 Kilogram",
                }
            ],
            "produksi_penjualan": [
                {
                    "Produk": "Sosis",
                    "Jumlah Produksi Satuan Asli": "6,00",
                    "Jumlah Produksi Satuan Standar (Kilogram)": "60,00",
                }
            ],
        },
    }
    findings = run(report, {"thresholds": {"low_utilization_percent": 5}})
    assert not any(f.rule_id == "CAP_TON_TO_KG_CONVERSION" for f in findings)
    low = [f for f in findings if f.rule_id == "CAP_VERY_LOW_UTILIZATION"]
    assert low and "0.04%" in low[0].nilai_terdeteksi
