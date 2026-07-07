from src.validation.rules_waste import run


def test_waste_cod_outlet_over_inlet_flagged():
    report = {
        "sections": {
            "produksi_penjualan": [{"produk": "Roti", "jumlah_dalam_kilogram": "10.000"}],
            "limbah_cair": [{"cod_inlet": "100", "cod_outlet": "180"}],
        }
    }
    findings = run(report, {"thresholds": {}})
    assert any(f.rule_id == "WASTE_COD_OUTLET_OVER_INLET" and f.severity == "CRITICAL" for f in findings)


def test_waste_large_debit_flagged():
    report = {"sections": {"limbah_cair": [{"debit_limbah_cair_inlet": "20"}]}}
    findings = run(report, {"thresholds": {"max_reasonable_liquid_waste_m3_per_second": 10}})
    assert any(f.rule_id == "WASTE_DEBIT_TOO_LARGE" for f in findings)

