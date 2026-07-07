from src.parser.number_normalizer import normalize_number, parse_number_with_unit


def test_normalize_indonesian_currency_and_grouping():
    assert normalize_number("Rp. 501.807.017") == 501807017
    assert normalize_number("IDR 21.636.456.226") == 21636456226
    assert normalize_number("60.000,00") == 60000
    assert normalize_number("1.800") == 1800
    assert normalize_number("0,00") == 0


def test_normalize_system_decimal_dot():
    assert normalize_number("60000.00000") == 60000


def test_parse_number_with_unit():
    assert parse_number_with_unit("734 MMBTU").value == 734
    assert parse_number_with_unit("734 MMBTU").unit == "MMBTU"
    assert parse_number_with_unit("162.601 kWh").value == 162601
    assert parse_number_with_unit("162.601 kWh").unit == "kWh"
    assert parse_number_with_unit("100 ton").value == 100
    assert parse_number_with_unit("100 ton").unit == "ton"
    assert parse_number_with_unit("100.000 Kilogram").value == 100000
    assert parse_number_with_unit("100.000 Kilogram").unit == "Kilogram"

