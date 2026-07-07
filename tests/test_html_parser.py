from src.parser.html_parser import parse_processed_reports, parse_report_detail


def test_parse_processed_reports_mock_table():
    html = """
    <h3>Laporan yang Diproses</h3>
    <table>
      <tr><th>Nama Perusahaan</th><th>Periode</th><th>Tanggal Kirim</th><th>Status</th><th>Validator</th></tr>
      <tr><td><a href="/detail/1">PT Mock</a></td><td>TW I 2026</td><td>2026-04-01</td><td>Diproses</td><td>Ani</td></tr>
    </table>
    """
    reports = parse_processed_reports(html, "https://intranew.kemenperin.go.id")
    assert len(reports) == 1
    assert reports[0]["company_name"] == "PT Mock"
    assert reports[0]["detail_url"] == "https://intranew.kemenperin.go.id/detail/1"


def test_parse_detail_sections_mock_tables():
    html = """
    <h3>Kapasitas Produksi</h3>
    <table>
      <tr><th>Produk</th><th>Kapasitas Terpasang Standar Kg</th></tr>
      <tr><td>Roti</td><td>100.000</td></tr>
    </table>
    <h3>Bahan Baku</h3>
    <table>
      <tr><th>Nama Bahan Baku</th><th>Jumlah Dalam Kilogram</th></tr>
      <tr><td>Tepung</td><td>80.000</td></tr>
    </table>
    <a href="/surat.pdf">Surat Pernyataan</a>
    """
    parsed = parse_report_detail(html, "https://intranew.kemenperin.go.id")
    assert parsed["sections"]["kapasitas"][0]["Produk"] == "Roti"
    assert parsed["sections"]["bahan_baku"][0]["Nama Bahan Baku"] == "Tepung"
    assert parsed["statement_links"] == ["https://intranew.kemenperin.go.id/surat.pdf"]

