import { describe, expect, it } from "vitest";
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

describe("PDF report parser", () => {
  it("parses the report until liquid waste and ignores sections below it", () => {
    const report = parseReportFromText(reportText, "agro.pdf");
    expect(report.companyName).toBe("PT Agro Makmur Raya");
    expect(report.capacity).toHaveLength(1);
    expect(report.production).toHaveLength(1);
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
    expect(result.findings.some((finding) => finding.ruleId === "LIQUID_WASTE_DEBIT_TOO_HIGH")).toBe(true);
    expect(result.findings.some((finding) => finding.ruleId === "OWNERSHIP_NOT_100")).toBe(false);
  });
});
