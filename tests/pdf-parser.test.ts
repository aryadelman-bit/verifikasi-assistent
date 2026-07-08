import { describe, expect, it } from "vitest";
import { DEFAULT_PRICE_LIMITS } from "../lib/defaultPriceLimits";
import { buildIntraNewImportText, csvToSectionText, htmlToPlainText } from "../lib/intranewImport";
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

  it("converts saved IntraNEW HTML into readable section text", () => {
    const text = htmlToPlainText("<html><body><h1>PT Contoh</h1><div>Data Umum</div><table><tr><td>Periode Laporan</td><td>Triwulan 1 Tahun 2026</td></tr></table></body></html>");
    expect(text).toContain("PT Contoh");
    expect(text).toContain("Data Umum");
    expect(csvToSectionText("unknown.csv", "A,B\n1,2").warning).toContain("belum dikenali");
  });
});
