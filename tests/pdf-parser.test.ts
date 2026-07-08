import { describe, expect, it } from "vitest";
import * as XLSX from "xlsx";
import { DEFAULT_PRICE_LIMITS } from "../lib/defaultPriceLimits";
import { buildIntraNewImportText, csvToSectionText, htmlToPlainText, workbookToCsvSources } from "../lib/intranewImport";
import { parsePriceLimits } from "../lib/priceLimits";
import { parseReportFromText } from "../lib/reportParser";
import { validateReport } from "../lib/validator";

const reportText = `
PT Agro Makmur Raya
NIB 1234567890123
Perizinan Izin Usaha Industri
Bidang Usaha KBLI 10437
Buka
Data Umum
Periode Laporan Triwulan 2 Tahun 2026
Status Berproduksi
Buka
Nama Penanda Tangan Laporan Budi Santoso
Jabatan Direktur
Buka
Persediaan
Nilai persediaan bahan baku 1.000.000 2.000.000
Buka
Kapasitas Produksi Kapasitas Sebelum OSS
1. RBD Olein 10437 15119037 73.000 ton 73.000 ton 73.000.000 Kilogram 73.000.000 Kilogram
Buka
Produksi dan Penjualan
1. RBD OLEIN 10437 15119037 kilogram 6.755.001,00 6.755.001,00 300.000.000.000 8.620.969,00 8.620.969,00 138.662.986.173 Ya 0,00%
Buka
Bahan Baku
1 CPO 15131190 kilogram 8.702.975,00 8.702.975,00 100.000.000.000 0,00 0,00 0 10437 0,00 0
Buka
Bahan Penolong
1 Bleaching Earth 25081000 kilogram 123.456,00 123.456,00 1.000.000.000 0,00 0,00 0 10437 0,00 0
Buka
Investasi
Persentase Kepemilikan
Swasta Nasional 0.01 %
Pemerintah Pusat 0.00 %
Pemerintah Daerah 0.00 %
Asing 99.99 %
Buka
Tenaga Kerja
Laki-Laki 104 45 16 18
Wanita 1 0 15 0
0 0 4 154 3 38 0 0
Buka
Prakerin
Buka
Penggunaan Air Baku Untuk Proses Produksi
1. Air tanah 2.327 2.611.440
Buka
Penggunaan Bahan Bakar
Penggunaan tenaga listrik untuk produksi
Dari PLN 867.360 kWh Rp. 548.049.790
Buka
Pengeluaran Perusahaan
Upah/gaji untuk pekerja produksi Rp. 2.395.614.223
Upah/gaji untuk pekerja lainnya Rp. 930.646.565
Memiliki unit litbang Tidak
Jumlah researcher / periset dari unit litbang 0 Orang
Buka
Rencana Produksi
Buka
Mesin Produksi
1. Mesin Refinery 2020 2021 Jepang
Buka
Pengelolaan Limbah Padat
1. Spent bleaching earth 12
Buka
Pengelolaan Limbah B3
1 Oli bekas 1
Buka
Pengelolaan Limbah Cair
Debit limbah cair di inlet 0.00
Debit limbah cair di outlet 875.00
COD pada saluran inlet (sebelum diolah di IPAL) 1797.56
COD pada saluran outlet (titik pemetaan) 43.97
Sludge removed 0
Indi 4.0
Bagian ini harus diabaikan parser section.
`;

const limitText = `
10437 Industri minyak goreng kelapa sawit 10.761 23.750 13.383 28.500 13.413 17.939
10423 Industri minyak goreng bukan kelapa sawit 13.500 35.150 0 0 0 0
`;

const overlappingInventoryCapacityText = `
PT Contoh Overlap
NIB 1234567890123
Perizinan Izin Usaha Industri
Bidang Usaha KBLI 10437
Kapasitas Produksi - KBLI 10437 (RBD OLEIN) (292000.00000 TNE) (Dit. IMHLP)
Buka
Data Umum
Periode Laporan Triwulan 2 Tahun 2026
Status Berproduksi
Buka
Nama Penanda Tangan Laporan Budi Santoso
Jabatan Direktur
Buka
Persediaan
Jenis Persediaan Awal (Rp.) Akhir (Rp.)
Nilai persediaan bahan baku, bahan penolong, bahan bakar, bahan pembungkus, dan lain-lain 38.785.000.000 105.970.000.000
Nilai persediaan barang jadi yang dihasilkan 134.022.000.000 0
Kapasitas Produksi
Kapasitas Sebelum OSS Kapasitas OSS 1.1
1. RBD Olein 10437 15119037 73.000 ton 73.000 ton 73.000.000 Kilogram 73.000.000 Kilogram
Buka
Produksi dan Penjualan
1. RBD OLEIN 10437 15119037 kilogram 6.755.001,00 6.755.001,00 300.000.000.000 8.620.969,00 8.620.969,00 138.662.986.173 Ya 0,00%
Buka
Bahan Baku
1 CPO 15131190 kilogram 8.702.975,00 8.702.975,00 100.000.000.000 0,00 0,00 0 10437 0,00 0
Buka
Pengelolaan Limbah Cair
Debit limbah cair di inlet 0.00
Debit limbah cair di outlet 0.00
COD pada saluran inlet (sebelum diolah di IPAL) 0
COD pada saluran outlet (titik pemetaan) 0
Sludge removed 0
Indi 4.0
`;

const commaSolidWasteText = reportText.replace("1. Spent bleaching earth 12", "Limbah padat organik 0,9 ton");
const salesOverProductionWithoutStockText = reportText.replace(
  "8.620.969,00 8.620.969,00 138.662.986.173 Ya 0,00%",
  "8.620.969,00 8.620.969,00 138.662.986.173 Tidak 0,00%"
);

const intranewProductionCsv = `No.,Produk,KBLI,"Kode HS",Spesifikasi,Merk,Tipe,"Sertifikat Halal","Satuan Asli","Jumlah Produksi Satuan Asli","Jumlah Produksi Satuan Standar (Kilogram)","Nilai Produksi (Rp.)","Jumlah Penjualan Satuan Asli","Jumlah Penjualan Satuan Standar (Kilogram)","Nilai Penjualan","Terdapat Stok Yang Dijual","Persentase Ekspor Penjualan (%)","Negara Tujuan Ekspor"
1.,Sosis,10130,16010010,"Daging olahan frozen food",,,,CT,"6,00","60,00",2.400.000.000,"5,00","50,00",2.150.000.000,Ya,"0,00%",
`;

const intranewMaterialCsv = `No,"Nama Bahan Baku",Spesifikasi,"Kode HS","Satuan Asli","Jumlah Dalam Negeri (Satuan Asli)","Jumlah Dalam Negeri (Kilogram)","Nilai Dalam Negeri (Rp.)","Jumlah Luar Negeri (Satuan Asli)","Jumlah Luar Negeri (Kilogram)","Nilai Luar Negeri (Rp.)","Negara Asal Impor","KBLI Produk Yang Dihasilkan","Nama Produk Yang Dihasilkan","Jumlah Persediaan (Kilogram)","Nilai Persediaan (Rp.)"
1.,"Daging Sapi","Daging Sapi",02011000,kilogram,"5,00","5,00",500.000.000,"0,00","0,00",0,,10130,"Andy Sosis Bakar","500,00","50.000.000,00"
`;

const kbaHtmlWithTopIndiMenu = `
<html>
<head><title>Intranet Kemenperin</title></head>
<body>
<nav><a>INDI 4.0</a></nav>
<h3 class="box-title"><b>PT KEBON AGUNG</b></h3>
<table>
<tr><td>Alamat Kantor</td><td>Jl. Raya Margorejo Indah Kav. A 131-132</td></tr>
<tr><td>NIB</td><td>8120105802939</td></tr>
<tr><td>Bidang Usaha</td><td>- KBLI 10721 (Industri Gula Pasir)</td></tr>
<tr><td>Verifikator</td><td>Donni Ansyari</td></tr>
<tr><td>Validator</td><td>Arya Wibisono Manifestoputra</td></tr>
</table>
<h3 class="box-title">Data Umum</h3>
<table>
<tr><td>Periode Laporan</td><td>Triwulan 1 Tahun 2026 | Tanggal Kirim 2026-06-30 18:41:52</td></tr>
<tr><td>Nilai Investasi (PP No 7/Tanpa Tanah dan Bangunan)</td><td>IDR 9.450.000.000</td></tr>
<tr><td>Status</td><td>Berproduksi</td></tr>
<tr><td>Menggunakan Maklon</td><td>Tidak</td></tr>
<tr><td>Menyediakan Maklon</td><td>Tidak</td></tr>
<tr><td>Nama Penanda Tangan Laporan</td><td>Arifin</td></tr>
<tr><td>Jabatan</td><td>Kadiv SDM &amp; Umum</td></tr>
</table>
<h3 class="box-title">Persediaan</h3>
<table>
<tr><td>Nilai persediaan bahan baku, bahan penolong, bahan bakar, bahan pembungkus, dan lain-lain</td><td>0</td><td>0</td></tr>
<tr><td>Nilai persediaan barang produksi setengah jadi (dinilai sesuai dengan nilai bahan baku ditambah nilai pekerjaan yang dilakukan)</td><td>0</td><td>0</td></tr>
<tr><td>Nilai persediaan barang jadi yang dihasilkan</td><td>0</td><td>0</td></tr>
</table>
<h3 class="box-title">Kapasitas Produksi</h3><table><tr><td>1.</td><td>Gula Kristal putih</td><td>10721</td><td>17011400</td><td>13.000 ton</td><td>13.000 ton</td><td>13.000.000 Kilogram</td><td>13.000.000 Kilogram</td></tr></table>
<h3 class="box-title">Produksi dan Penjualan</h3><table><tr><td>Download CSV</td></tr></table>
<h3 class="box-title">Bahan Baku</h3><table><tr><td>Download CSV</td></tr></table>
<h3 class="box-title">Bahan Penolong</h3><table><tr><td align="center">Tidak ada data</td></tr></table>
<h3 class="box-title">Investasi</h3><table><tr><td>Swasta Nasional</td><td>100,00 %</td></tr></table>
<h3 class="box-title"><i></i> Tenaga Kerja</h3>
<table>
<tr><td>Laki-Laki</td><td>64</td><td>196</td><td>59</td><td>34</td></tr>
<tr><td>Wanita</td><td>2</td><td>0</td><td>7</td><td>0</td></tr>
<tr><td>0</td><td>0</td><td>0</td><td>291</td><td>60</td><td>11</td><td>0</td><td>0</td></tr>
</table>
<h3 class="box-title">Prakerin</h3><table><tr><td>Tidak ada data</td></tr></table>
<h3 class="box-title">Penggunaan Air Baku Untuk Proses Produksi</h3>
<table>
<tr><td>1.</td><td>Air permukaan (sungai, danau, mata air, dan laut)</td><td>0</td><td>0</td></tr>
<tr><td>2.</td><td>Air tanah</td><td>0</td><td>0</td></tr>
<tr><td>3.</td><td>Perusahaan Penyedia Air</td><td>0</td><td>0</td></tr>
<tr><td>4.</td><td>Air Daur Ulang Dari Proses di Industri</td><td>0</td><td>0</td></tr>
</table>
<h3 class="box-title">Penggunaan Bahan Bakar</h3>
<table>
<tr><td>Tidak Ada Data</td></tr>
<tr><td>Penggunaan tenaga listrik untuk produksi</td></tr>
<tr><td>Dari PLN</td><td>640.320 kWh</td><td>Rp. 12.840.966</td></tr>
<tr><td>Bukan dari PLN</td><td>69.502 kWh</td><td>Rp. 62.944.542</td></tr>
</table>
<h3 class="box-title">Pengeluaran Perusahaan</h3>
<table>
<tr><td>Upah/gaji untuk pekerja produksi</td><td>Rp. 3.905.819.671</td></tr>
<tr><td>Upah/gaji untuk pekerja lainnya</td><td>Rp. 1.831.198.044</td></tr>
<tr><td>Memiliki unit litbang</td><td>Ya</td></tr>
<tr><td>Jumlah <i>researcher</i> / periset dari unit litbang</td><td>4 Orang</td></tr>
<tr><td>Biaya <i>research</i> and development</td><td>Rp. 39.876.120</td></tr>
</table>
<h3 class="box-title">Rencana Produksi</h3><table><tr><td>Tidak ada data</td></tr></table>
<h3 class="box-title">Mesin Produksi</h3>
<table><tr><td>1.</td><td>Decanter</td><td>GEA 55000</td><td>Centrifuge</td><td>2025</td><td>2025</td><td>INDIA</td><td>6 Unit</td></tr></table>
<h3 class="box-title">Persediaan</h3>
<table>
<tr><td>Nilai persediaan bahan baku, bahan penolong, bahan bakar, bahan pembungkus, dan lain-lain</td><td>0</td><td>0</td></tr>
<tr><td>Nilai persediaan barang produksi setengah jadi (dinilai sesuai dengan nilai bahan baku ditambah nilai pekerjaan yang dilakukan)</td><td>0</td><td>0</td></tr>
<tr><td>Nilai persediaan barang jadi yang dihasilkan</td><td>0</td><td>0</td></tr>
</table>
<h3 class="box-title">Pengelolaan Limbah Padat</h3>
<table><tr><td>1.</td><td>Blothong</td><td>0</td></tr></table>
<h3 class="box-title">Pengelolaan Limbah B3</h3><table><tr><td>Tidak ada data</td></tr></table>
<h3 class="box-title">Pengelolaan Limbah Cair</h3>
<table>
<tr><td>Debit limbah cair di inlet</td><td>0,00 m<sup>3</sup>/detik</td></tr>
<tr><td>Debit limbah cair di outlet</td><td>0,00 m<sup>3</sup>/detik</td></tr>
<tr><td>COD pada saluran inlet (sebelum diolah di IPAL)</td><td>0,00 mg/liter</td></tr>
<tr><td>COD pada saluran outlet (titik pemetaan)</td><td>0,00 mg/liter</td></tr>
<tr><td>Sludge removed </td><td>0,00 kg</td></tr>
</table>
<h3 class="box-title">Indi 4.0</h3>
</body>
</html>`;

const kbaProductionCsv = `No.,Produk,KBLI,"Kode HS",Spesifikasi,Merk,Tipe,"Sertifikat Halal","Satuan Asli","Jumlah Produksi Satuan Asli","Jumlah Produksi Satuan Standar (Kilogram)","Nilai Produksi (Rp.)","Jumlah Penjualan Satuan Asli","Jumlah Penjualan Satuan Standar (Kilogram)","Nilai Penjualan","Terdapat Stok Yang Dijual","Persentase Ekspor Penjualan (%)","Negara Tujuan Ekspor"
1.,Gula,10721,17011400,"Gula Kristal Putih",KA,"Gula Kristal Putih",,TNE,"12.187,00","12.187.000,00",177.930.200.000,"27.293,00","27.293.000,00",427.591.493,Ya,"0,00%",
`;

const kbaMaterialCsv = `No,"Nama Bahan Baku",Spesifikasi,"Kode HS","Satuan Asli","Jumlah Dalam Negeri (Satuan Asli)","Jumlah Dalam Negeri (Kilogram)","Nilai Dalam Negeri (Rp.)","Jumlah Luar Negeri (Satuan Asli)","Jumlah Luar Negeri (Kilogram)","Nilai Luar Negeri (Rp.)","Negara Asal Impor","KBLI Produk Yang Dihasilkan","Nama Produk Yang Dihasilkan","Jumlah Persediaan (Kilogram)","Nilai Persediaan (Rp.)"
1.,Tebu,Tebu,12129310,ton,"1,00","1.000,00",1.200.000,"0,00","0,00",0,,10721,"Gula Kristal Putih","0,00","0,00"
`;

describe("PDF report parser", () => {
  it("parses the report until liquid waste and ignores sections below it", () => {
    const report = parseReportFromText(reportText, "agro.pdf");
    expect(report.companyName).toBe("PT Agro Makmur Raya");
    expect(report.capacity).toHaveLength(1);
    expect(report.production).toHaveLength(1);
    expect(report.production[0].stockSoldFlag).toBe(true);
    expect(report.materials).toHaveLength(1);
    expect(report.helpers).toHaveLength(1);
    expect(report.liquidWaste.outletDebit).toBe(875);
    expect(report.rawText).toContain("Indi 4.0");
    expect(report.sectionsText.liquidWaste).not.toContain("Indi 4.0");
  });

  it("parses KBLI price limits and validates price outliers without false ownership findings", () => {
    const report = parseReportFromText(reportText, "agro.pdf");
    const limits = parsePriceLimits(limitText);
    const result = validateReport(report, limits);

    expect(limits["10437"]?.upper).toBe(17939);
    expect(limits["10423"]?.upper).toBe(35150);
    expect(result.findings.some((finding) => finding.ruleId === "PRICE_OUTSIDE_KBLI_LIMIT")).toBe(true);
    expect(result.findings.find((finding) => finding.ruleId === "LIQUID_WASTE_DEBIT_TOO_HIGH")?.severity).toBe("MEDIUM");
    expect(result.findings.some((finding) => finding.ruleId === "INLET_ZERO_OUTLET_POSITIVE")).toBe(false);
    expect(result.findings.some((finding) => finding.ruleId === "OWNERSHIP_NOT_100")).toBe(false);
  });

  it("uses bundled KBLI price limits so validators only upload the quarterly report", () => {
    const report = parseReportFromText(reportText, "agro.pdf");
    const result = validateReport(report, DEFAULT_PRICE_LIMITS);

    expect(Object.keys(DEFAULT_PRICE_LIMITS).length).toBeGreaterThan(100);
    expect(DEFAULT_PRICE_LIMITS["10437"]?.upper).toBe(17939);
    expect(result.findings.some((finding) => finding.ruleId === "PRICE_OUTSIDE_KBLI_LIMIT")).toBe(true);
  });

  it("keeps capacity rows out of inventory when section titles overlap", () => {
    const report = parseReportFromText(overlappingInventoryCapacityText, "overlap.pdf");

    expect(report.inventory).toHaveLength(2);
    expect(report.capacity).toHaveLength(1);
    expect(report.sectionsText.inventory).not.toContain("RBD Olein 10437");
    expect(report.sectionsText.capacity).toContain("RBD Olein 10437");
    expect(report.parserWarnings).not.toContain("Bagian Kapasitas Produksi tidak ditemukan pada teks PDF.");
  });

  it("parses decimal ton solid waste and does not mark solid waste as missing", () => {
    const report = parseReportFromText(commaSolidWasteText, "solid-waste.pdf");
    const result = validateReport(report, DEFAULT_PRICE_LIMITS);

    expect(report.solidWasteRows).toHaveLength(1);
    expect(report.solidWasteRows[0].Jumlah).toBe("0,9 ton");
    expect(result.findings.some((finding) => finding.ruleId === "NO_SOLID_WASTE_WITH_PRODUCTION")).toBe(false);
  });

  it("treats sales over production as conditional on stock support", () => {
    const supported = validateReport(parseReportFromText(reportText, "supported-stock.pdf"), DEFAULT_PRICE_LIMITS);
    const unsupported = validateReport(parseReportFromText(salesOverProductionWithoutStockText, "no-stock.pdf"), DEFAULT_PRICE_LIMITS);

    expect(supported.findings.find((finding) => finding.ruleId === "SALES_OVER_PRODUCTION_WITH_STOCK")?.severity).toBe("INFO");
    expect(unsupported.findings.some((finding) => finding.ruleId === "SALES_OVER_PRODUCTION_WITHOUT_STOCK")).toBe(true);
  });

  it("imports IntraNEW CSV files into parser-compatible report text", () => {
    const imported = buildIntraNewImportText([
      { fileName: "Download_CSV_produksi.csv", text: intranewProductionCsv },
      { fileName: "Download_CSV_bahanbaku.csv", text: intranewMaterialCsv }
    ]);
    const report = parseReportFromText(imported.text, "csv-import");
    const result = validateReport(report, DEFAULT_PRICE_LIMITS);

    expect(imported.warnings).toEqual([]);
    expect(report.production).toHaveLength(1);
    expect(report.production[0].product).toBe("Sosis");
    expect(report.production[0].stockSoldFlag).toBe(true);
    expect(report.materials).toHaveLength(1);
    expect(result.findings.some((finding) => finding.ruleId === "PRICE_OUTSIDE_KBLI_LIMIT")).toBe(true);
    expect(result.findings.some((finding) => finding.ruleId === "INPUT_EXTREME_PRICE")).toBe(true);
  });

  it("imports IntraNEW XLSX capacity sheets into parser-compatible report text", () => {
    const workbook = XLSX.utils.book_new();
    const sheet = XLSX.utils.aoa_to_sheet([
      [
        "No.",
        "Produk",
        "KBLI",
        "Kode HS",
        "Kapasitas Produksi Dalam Satuan Asli per Jan - Mar 2026",
        "Kapasitas Terpasang Dalam  Satuan Asli per Jan - Mar 2026",
        "Kapasitas Produksi Dalam Satuan Standar per Jan - Mar 2026",
        "Kapasitas Terpasang Dalam Satuan Standar per Jan - Mar 2026"
      ],
      ["1", "Sosis", "10130", "16010010", "100 ton", "166,7 ton", "100.000 Kilogram", "166.670 Kilogram"],
      ["2", "Bakpao Mini", "10710", "19012010", "8 ton", "25 ton", "8.000 Kilogram", "25.000 Kilogram"]
    ]);
    XLSX.utils.book_append_sheet(workbook, sheet, "Laporan");

    const imported = buildIntraNewImportText(workbookToCsvSources("Download_CSV_laporan.xlsx", workbook));
    const report = parseReportFromText(imported.text, "xlsx-import");

    expect(imported.warnings).toEqual([]);
    expect(report.capacity).toHaveLength(2);
    expect(report.capacity[0].product).toBe("Sosis");
    expect(report.capacity[0].installedKg).toBe(166670);
    expect(report.parserWarnings).not.toContain("Bagian Kapasitas Produksi tidak ditemukan pada teks PDF.");
  });

  it("keeps IntraNEW HTML sections when INDI appears in the top navigation", () => {
    const workbook = XLSX.utils.book_new();
    const sheet = XLSX.utils.aoa_to_sheet([
      [
        "No.",
        "Produk",
        "KBLI",
        "Kode HS",
        "Kapasitas Produksi Dalam Satuan Asli per Jan - Mar 2026",
        "Kapasitas Terpasang Dalam  Satuan Asli per Jan - Mar 2026",
        "Kapasitas Produksi Dalam Satuan Standar per Jan - Mar 2026",
        "Kapasitas Terpasang Dalam Satuan Standar per Jan - Mar 2026"
      ],
      ["1", "Gula Kristal putih", "10721", "17011400", "13.000 ton", "13.000 ton", "13.000.000 Kilogram", "13.000.000 Kilogram"]
    ]);
    XLSX.utils.book_append_sheet(workbook, sheet, "Laporan");

    const imported = buildIntraNewImportText([
      { fileName: "Laporan produksi TW 1 2026 PT KBA.html", text: kbaHtmlWithTopIndiMenu },
      { fileName: "produksi_KEBON AGUNG_triwulan1_2026.csv", text: kbaProductionCsv },
      { fileName: "bahanbaku_KEBON AGUNG_triwulan1_2026.csv", text: kbaMaterialCsv },
      { fileName: "bahanpenolong_KEBON AGUNG_triwulan1_2026.csv", text: 'No,"Nama Bahan Baku"\n' },
      ...workbookToCsvSources("kapasitasproduksi_KEBON_AGUNG.xlsx", workbook)
    ]);
    const report = parseReportFromText(imported.text, "kba-import");

    expect(report.parserWarnings).toEqual([]);
    expect(report.companyName).toBe("PT KEBON AGUNG");
    expect(report.general["Status Berproduksi"]).toBe("Berproduksi");
    expect(report.general["Nama Penanda Tangan Laporan"]).toBe("Arifin");
    expect(report.inventory).toHaveLength(3);
    expect(report.capacity[0].installedKg).toBe(13000000);
    expect(report.production[0].productionKg).toBe(12187000);
    expect(report.materials[0].name).toBe("Tebu");
    expect(report.helpers).toHaveLength(0);
    expect(report.labor.totalWorkers).toBe(362);
    expect(report.waterRows).toHaveLength(4);
    expect(report.sectionsText.energy).toContain("Dari PLN 640.320 kWh Rp. 12.840.966");
    expect(report.expenses["Memiliki unit litbang"]).toBe("Ya");
    expect(report.machineRows).toHaveLength(1);
    expect(report.solidWasteRows).toEqual([{ No: "1.", Uraian: "Blothong", Jumlah: "0", Nilai: "" }]);
    expect(report.liquidWaste.outletDebit).toBe(0);
  });

  it("converts saved IntraNEW HTML into readable section text", () => {
    const text = htmlToPlainText("<html><body><h1>PT Contoh</h1><div>Data Umum</div><table><tr><td>Periode Laporan</td><td>Triwulan 1 Tahun 2026</td></tr></table></body></html>");
    expect(text).toContain("PT Contoh");
    expect(text).toContain("Data Umum");
    expect(csvToSectionText("unknown.csv", "A,B\n1,2").warning).toContain("belum dikenali");
  });
});
