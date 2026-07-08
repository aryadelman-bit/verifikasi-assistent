from src.parser.section_mapper import canonical_section


def test_capacity_oss_heading_maps_to_capacity_not_identity():
    assert canonical_section("Kapasitas Sebelum OSS 1.1") == "kapasitas_referensi"
    assert canonical_section("Kapasitas Produksi") == "kapasitas"
    assert canonical_section("Data OSS") == "identitas"
