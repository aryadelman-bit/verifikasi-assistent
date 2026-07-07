from src.validation.rules_material import run


def test_material_extreme_price_examples_are_critical():
    report = {
        "sections": {
            "bahan_baku": [
                {"nama_bahan_baku": "Daging sapi", "jumlah_dalam_kilogram": "5", "nilai_total": "Rp500.000.000"},
                {"nama_bahan_baku": "Daging ayam", "jumlah_dalam_kilogram": "20", "nilai_total": "Rp1.000.000.000"},
            ],
            "produksi_penjualan": [{"produk": "Olahan daging", "jumlah_dalam_kilogram": "100"}],
        }
    }
    findings = run(report, {"thresholds": {"max_food_material_price_per_kg": 5_000_000}})
    critical = [f for f in findings if f.rule_id == "MAT_EXTREME_PRICE_PER_KG"]
    assert len(critical) == 2
    assert all(f.severity == "CRITICAL" for f in critical)


def test_material_ratio_low_food_is_high():
    report = {
        "identity": {"bidang_usaha": "Industri makanan"},
        "sections": {
            "bahan_baku": [{"nama_bahan_baku": "Daging", "jumlah_dalam_kilogram": "10", "nilai_total": "100.000"}],
            "produksi_penjualan": [{"produk": "Olahan daging", "jumlah_dalam_kilogram": "1000"}],
        },
    }
    findings = run(report, {"thresholds": {"material_ratio_low_food": 0.2, "material_ratio_high_food": 5}})
    assert any(f.rule_id == "MAT_LOW_INPUT_OUTPUT_RATIO" and f.severity == "HIGH" for f in findings)

