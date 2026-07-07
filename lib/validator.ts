import { formatNumber, formatRupiah, parseIndonesianNumber } from "./number";
import { getPriceLimitForKbli } from "./priceLimits";
import { SECTION_LABELS } from "./reportParser";
import type {
  Finding,
  ParsedReport,
  PriceLimitMap,
  ReportSectionKey,
  SectionSummary,
  Severity,
  ValidationResult
} from "./types";

const WEIGHTS: Record<Severity, number> = {
  CRITICAL: 25,
  HIGH: 15,
  MEDIUM: 8,
  LOW: 3,
  INFO: 0
};

const SECTION_ORDER = Object.keys(SECTION_LABELS) as ReportSectionKey[];

function finding(
  section: ReportSectionKey,
  ruleId: string,
  rule: string,
  severity: Severity,
  message: string,
  detectedValue: string,
  basis: string,
  recommendation: string,
  question: string
): Finding {
  return {
    ruleId,
    section: SECTION_LABELS[section],
    rule,
    severity,
    status: severity === "INFO" ? "WARNING" : severity === "LOW" || severity === "MEDIUM" ? "WARNING" : "FAIL",
    finding: message,
    detectedValue,
    basis,
    recommendation,
    clarificationQuestion: question
  };
}

function sum(values: number[]): number {
  return values.reduce((total, value) => total + value, 0);
}

function riskScore(findings: Finding[]): number {
  return Math.min(
    100,
    findings.filter((item) => item.status === "WARNING" || item.status === "FAIL").reduce((total, item) => total + WEIGHTS[item.severity], 0)
  );
}

function decision(findings: Finding[], score: number): string {
  const critical = findings.filter((item) => item.severity === "CRITICAL").length;
  const high = findings.filter((item) => item.severity === "HIGH").length;
  if (critical > 0 || high >= 4 || score >= 81) return "Jangan divalidasi dulu / kembalikan untuk perbaikan";
  if (high > 0 || score >= 41) return "Perlu klarifikasi/perbaikan data";
  if (score >= 21 || findings.some((item) => ["LOW", "MEDIUM"].includes(item.severity))) return "Dapat divalidasi dengan catatan";
  return "Layak divalidasi";
}

function totalProductionKg(report: ParsedReport): number {
  return sum(report.production.map((row) => row.productionKg));
}

function rowQuantityKg(row: Record<string, string>, defaultUnit: "kg" | "ton" = "kg"): number {
  const raw = `${row.Jumlah ?? ""} ${row.Nilai ?? ""}`.trim();
  const value = parseIndonesianNumber(raw) ?? 0;
  const unit = raw.toLowerCase();
  if (unit.includes("ton")) return value * 1000;
  if (unit.includes("kg") || unit.includes("kilogram")) return value;
  return defaultUnit === "ton" ? value * 1000 : value;
}

function inventoryValue(report: ParsedReport, pattern: RegExp, side: "startValue" | "endValue"): number {
  return sum(report.inventory.filter((row) => pattern.test(row.type)).map((row) => row[side]));
}

function productionValue(report: ParsedReport): number {
  return sum(report.production.map((row) => row.productionValue));
}

function salesValue(report: ParsedReport): number {
  return sum(report.production.map((row) => row.salesValue));
}

function ownershipPercentage(text: string, label: string): number | null {
  const escaped = label.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const match = text.match(new RegExp(`^\\s*${escaped}\\s+(\\d+(?:[.,]\\d+)?)\\s*%\\s*$`, "im"));
  return match ? parseIndonesianNumber(match[1]) : null;
}

export function validateReport(report: ParsedReport, limits: PriceLimitMap): ValidationResult {
  const findings: Finding[] = [];

  for (const [field, value] of Object.entries({
    "Nama Perusahaan": report.companyName,
    NIB: report.identity.NIB,
    Perizinan: report.identity.Perizinan,
    "Bidang Usaha/KBLI": report.identity.KBLI,
    "Periode Laporan": report.general["Periode Laporan"],
    "Nama Penanda Tangan": report.general["Nama Penanda Tangan Laporan"],
    Jabatan: report.general.Jabatan
  })) {
    if (!value || value === "-" || value === "?") {
      findings.push(
        finding(
          field.includes("NIB") || field.includes("Perizinan") || field.includes("KBLI") ? "identity" : "general",
          "REQUIRED_FIELD_EMPTY",
          "Kelengkapan field wajib",
          "MEDIUM",
          `${field} kosong atau tidak terbaca.`,
          String(value ?? ""),
          "Field wajib pada laporan PDF diperiksa dari teks yang diekstrak.",
          "Minta perusahaan melengkapi field tersebut atau pastikan PDF yang diunggah lengkap.",
          `Mohon lengkapi/konfirmasi data ${field}.`
        )
      );
    }
  }

  const productionKg = totalProductionKg(report);

  if (report.capacity.length === 0) {
    findings.push(
      finding(
        "capacity",
        "CAPACITY_TABLE_EMPTY",
        "Kelengkapan kapasitas",
        "HIGH",
        "Tabel kapasitas produksi tidak berhasil terbaca.",
        "0 baris",
        "Bagian Kapasitas Produksi harus memiliki baris produk, KBLI, HS, kapasitas satuan asli, dan kapasitas standar.",
        "Unggah PDF yang lengkap atau cek apakah struktur tabel berubah.",
        "Mohon pastikan data kapasitas produksi dilaporkan dan terbaca lengkap."
      )
    );
  }

  for (const row of report.capacity) {
    if (row.installedKg > 0 && row.productionKg > row.installedKg) {
      findings.push(
        finding(
          "capacity",
          "CAP_PRODUCTION_CAPACITY_OVER_INSTALLED",
          "Kapasitas produksi vs terpasang",
          "HIGH",
          "Kapasitas produksi lebih besar dari kapasitas terpasang.",
          `${row.product}: produksi kapasitas ${formatNumber(row.productionKg)} kg; terpasang ${formatNumber(row.installedKg)} kg`,
          "Kapasitas produksi standar dibandingkan dengan kapasitas terpasang standar.",
          "Cek kembali satuan, periode kapasitas, dan konversi kilogram.",
          `Mohon konfirmasi kapasitas ${row.product}; kapasitas produksi terlihat melebihi kapasitas terpasang.`
        )
      );
    }
  }

  const capacityByKbli = new Map<string, number>();
  const productionByKbli = new Map<string, number>();
  for (const row of report.capacity) {
    capacityByKbli.set(row.kbli, (capacityByKbli.get(row.kbli) ?? 0) + row.installedKg);
  }
  for (const row of report.production) {
    productionByKbli.set(row.kbli, (productionByKbli.get(row.kbli) ?? 0) + row.productionKg);
  }
  for (const [kbli, producedKg] of productionByKbli) {
    const installedKg = capacityByKbli.get(kbli) ?? 0;
    if (producedKg > 0 && installedKg === 0 && report.capacity.length > 0) {
      findings.push(
        finding(
          "capacity",
          "PRODUCTION_WITHOUT_MATCHING_CAPACITY",
          "Relasi produksi-kapasitas per KBLI",
          "MEDIUM",
          `Produksi KBLI ${kbli} ada, tetapi kapasitas untuk KBLI tersebut tidak terbaca.`,
          `produksi ${formatNumber(producedKg)} kg; kapasitas KBLI ${kbli} 0 kg`,
          "Produksi dikelompokkan per KBLI dan dibandingkan dengan kapasitas terpasang per KBLI.",
          "Cek apakah produk/KBLI kapasitas sama dengan produk/KBLI produksi.",
          `Mohon konfirmasi kapasitas produksi untuk KBLI ${kbli}.`
        )
      );
    }
    if (installedKg > 0 && producedKg > installedKg * 1.05) {
      findings.push(
        finding(
          "capacity",
          "PRODUCTION_OVER_INSTALLED_CAPACITY_BY_KBLI",
          "Relasi produksi-kapasitas per KBLI",
          "HIGH",
          `Produksi KBLI ${kbli} melebihi kapasitas terpasang yang terbaca.`,
          `produksi ${formatNumber(producedKg)} kg; kapasitas ${formatNumber(installedKg)} kg`,
          "Total produksi kg per KBLI dibandingkan dengan total kapasitas terpasang kg per KBLI.",
          "Cek satuan, periode kapasitas, dan apakah kapasitas yang dilaporkan bersifat tahunan/triwulanan.",
          `Mohon klarifikasi kapasitas dan produksi KBLI ${kbli}; produksi terlihat melebihi kapasitas terpasang.`
        )
      );
    }
  }

  if (report.production.length === 0) {
    findings.push(
      finding(
        "production",
        "PRODUCTION_TABLE_EMPTY",
        "Kelengkapan produksi",
        "HIGH",
        "Tabel produksi dan penjualan tidak berhasil terbaca.",
        "0 baris",
        "Bagian Produksi dan Penjualan harus memiliki produk, KBLI, HS, jumlah kg, dan nilai.",
        "Cek PDF dan struktur tabel produksi.",
        "Mohon pastikan data produksi dan penjualan telah dilaporkan."
      )
    );
  }

  const openingFinishedGoods = inventoryValue(report, /barang jadi/i, "startValue");
  const endingFinishedGoods = inventoryValue(report, /barang jadi/i, "endValue");
  for (const row of report.production) {
    const productionPrice = row.productionKg > 0 ? row.productionValue / row.productionKg : 0;
    const salesPrice = row.salesKg > 0 ? row.salesValue / row.salesKg : 0;
    const limit = getPriceLimitForKbli(limits, row.kbli);
    if (limit && limit.lower > 0 && limit.upper > 0) {
      for (const [kind, price] of [
        ["produksi", productionPrice],
        ["penjualan", salesPrice]
      ] as const) {
        if (price > 0 && (price < limit.lower || price > limit.upper)) {
          findings.push(
            finding(
              "production",
              "PRICE_OUTSIDE_KBLI_LIMIT",
              "Harga rata-rata per kg vs batas KBLI",
              price > limit.upper * 3 || price < limit.lower / 3 ? "HIGH" : "MEDIUM",
              `Harga ${kind} per kg di luar batas kewajaran KBLI ${row.kbli}.`,
              `${row.product}: ${formatRupiah(price)}/kg; batas ${formatRupiah(limit.lower)}-${formatRupiah(limit.upper)}/kg`,
              `Harga ${kind} = nilai ${kind} / jumlah kg. Batas memakai KBLI ${row.kbli} periode referensi ${limit.sourcePeriod}.`,
              "Minta klarifikasi nilai rupiah, jumlah kg, satuan, atau alasan harga berbeda dari rentang referensi.",
              `Mohon klarifikasi harga ${kind} ${row.product}; nilai per kg berada di luar batas kewajaran KBLI.`
            )
          );
        }
      }
    }
    if (row.productionKg > 0 && row.productionValue === 0) {
      findings.push(
        finding("production", "PROD_QTY_WITH_ZERO_VALUE", "Nilai produksi", "HIGH", "Produksi ada tetapi nilai produksi nol.", row.product, "Jumlah kg > 0 dan nilai = 0.", "Cek pengisian nilai produksi.", "Mohon pastikan nilai produksi sudah diisi.")
      );
    }
    if (row.salesKg > row.productionKg && row.productionKg >= 0) {
      const excessKg = row.salesKg - row.productionKg;
      if (row.stockSoldFlag) {
        findings.push(
          finding(
            "production",
            "SALES_OVER_PRODUCTION_WITH_STOCK",
            "Relasi penjualan-produksi-stok",
            "INFO",
            "Penjualan melebihi produksi, tetapi ditopang flag stok yang dijual.",
            `${row.product}: penjualan ${formatNumber(row.salesKg)} kg; produksi ${formatNumber(row.productionKg)} kg; selisih ${formatNumber(excessKg)} kg`,
            "Juknis: penjualan > produksi tidak otomatis invalid bila ada flag stok/persediaan yang mendukung.",
            "Cek sekilas persediaan awal/akhir barang jadi untuk memastikan stok memang memadai.",
            `Mohon pastikan penjualan ${row.product} yang melebihi produksi berasal dari stok.`
          )
        );
      } else if (openingFinishedGoods > 0) {
        findings.push(
          finding(
            "production",
            "SALES_OVER_PRODUCTION_WITH_INVENTORY_BUT_NO_FLAG",
            "Relasi penjualan-produksi-stok",
            "MEDIUM",
            "Penjualan melebihi produksi tanpa flag stok, tetapi ada persediaan awal barang jadi.",
            `${row.product}: penjualan ${formatNumber(row.salesKg)} kg; produksi ${formatNumber(row.productionKg)} kg; persediaan awal barang jadi ${formatRupiah(openingFinishedGoods)}`,
            "Penjualan lebih besar daripada produksi. Persediaan awal barang jadi dapat menjelaskan sebagian, tetapi flag stok tidak mendukung.",
            "Minta klarifikasi apakah penjualan berasal dari stok awal dan apakah flag stok perlu diperbaiki.",
            `Mohon klarifikasi sumber penjualan ${row.product} yang melebihi produksi dan perbaiki flag stok bila diperlukan.`
          )
        );
      } else {
        findings.push(
          finding(
            "production",
            "SALES_OVER_PRODUCTION_WITHOUT_STOCK",
            "Relasi penjualan-produksi-stok",
            "HIGH",
            "Penjualan melebihi produksi tanpa dukungan flag stok atau persediaan awal barang jadi.",
            `${row.product}: penjualan ${formatNumber(row.salesKg)} kg; produksi ${formatNumber(row.productionKg)} kg`,
            "Juknis: penjualan > produksi harus didukung stok awal, flag stok, atau log persediaan.",
            "Cek produksi, penjualan, stok yang dijual, dan persediaan barang jadi.",
            `Mohon klarifikasi penjualan ${row.product} yang melebihi produksi karena belum terlihat dukungan stok.`
          )
        );
      }
    }
  }

  if (productionKg > 0 && report.materials.length === 0) {
    findings.push(
      finding("materials", "MATERIAL_EMPTY_WITH_PRODUCTION", "Kelengkapan bahan baku", "HIGH", "Produksi ada tetapi bahan baku tidak terbaca.", `${formatNumber(productionKg)} kg`, "Total produksi > 0, tabel bahan baku kosong.", "Minta rincian bahan baku.", "Mohon lengkapi bahan baku yang digunakan.")
    );
  }

  for (const row of [...report.materials, ...report.helpers]) {
    const section: ReportSectionKey = report.materials.includes(row) ? "materials" : "helpers";
    const kg = row.domesticKg + row.importKg;
    const value = row.domesticValue + row.importValue;
    const price = kg > 0 ? value / kg : 0;
    if (kg > 0 && value === 0) {
      findings.push(finding(section, "INPUT_QTY_WITH_ZERO_VALUE", "Nilai input", "HIGH", "Jumlah input ada tetapi nilai nol.", `${row.name}: ${formatNumber(kg)} kg`, "Jumlah kg > 0 dan nilai = 0.", "Cek nilai rupiah input.", `Mohon pastikan nilai ${row.name} sudah diisi.`));
    }
    if (kg === 0 && value > 0) {
      findings.push(finding(section, "INPUT_VALUE_WITH_ZERO_QTY", "Jumlah input", "HIGH", "Nilai input ada tetapi jumlah kg nol.", `${row.name}: ${formatRupiah(value)}`, "Nilai > 0 dan kg = 0.", "Cek jumlah/satuan input.", `Mohon cek jumlah kg ${row.name}.`));
    }
    if (price > 5_000_000) {
      findings.push(finding(section, "INPUT_EXTREME_PRICE", "Harga input per kg", "CRITICAL", "Harga input per kg sangat tidak wajar.", `${row.name}: ${formatRupiah(price)}/kg`, "Harga input = nilai / kg; threshold sanity Rp5.000.000/kg.", "Cek salah satuan, jumlah, atau nilai rupiah.", `Mohon klarifikasi ${row.name}; harga per kg sangat tinggi.`));
    }
  }

  const materialKg = sum(report.materials.map((row) => row.domesticKg + row.importKg));
  if (productionKg > 0 && materialKg > 0) {
    const ratio = materialKg / productionKg;
    if (ratio < 0.2 || ratio > 5) {
      findings.push(
        finding(
          "materials",
          "INPUT_OUTPUT_RATIO_OUTLIER",
          "Rasio bahan baku/produksi",
          "MEDIUM",
          "Rasio bahan baku terhadap produksi berada di luar rentang umum.",
          `bahan baku ${formatNumber(materialKg)} kg; produksi ${formatNumber(productionKg)} kg; rasio ${formatNumber(ratio, 2)}`,
          "Rasio = total bahan baku kg / total produksi kg. Rentang sanity default 0,2-5.",
          "Cek apakah seluruh input dan output sudah dilaporkan dalam satuan yang sama.",
          "Mohon klarifikasi rasio input-output bahan baku terhadap produksi."
        )
      );
    }
  }

  const materialValue = sum(report.materials.map((row) => row.domesticValue + row.importValue));
  const productValue = productionValue(report);
  const soldValue = salesValue(report);
  if (productionKg > 0 && materialValue === 0 && report.materials.length > 0) {
    findings.push(
      finding(
        "materials",
        "PRODUCTION_WITH_ZERO_MATERIAL_VALUE",
        "Relasi produksi-bahan baku",
        "HIGH",
        "Produksi ada tetapi total nilai bahan baku nol.",
        `produksi ${formatNumber(productionKg)} kg; nilai bahan baku ${formatRupiah(materialValue)}`,
        "Produksi kg dibandingkan dengan total nilai bahan baku dalam negeri dan impor.",
        "Cek apakah nilai bahan baku kosong, salah satuan, atau belum diisi.",
        "Mohon klarifikasi nilai bahan baku karena produksi sudah dilaporkan."
      )
    );
  }
  if (materialValue > 0 && Math.max(productValue, soldValue) > 0 && materialValue > Math.max(productValue, soldValue) * 1.2) {
    findings.push(
      finding(
        "materials",
        "MATERIAL_VALUE_OVER_OUTPUT_VALUE",
        "Relasi nilai input-output",
        "MEDIUM",
        "Nilai bahan baku jauh lebih besar daripada nilai output/penjualan yang terbaca.",
        `nilai bahan baku ${formatRupiah(materialValue)}; nilai produksi ${formatRupiah(productValue)}; nilai penjualan ${formatRupiah(soldValue)}`,
        "Total nilai bahan baku dibandingkan dengan nilai produksi dan nilai penjualan. Ini indikator kewajaran, bukan kesimpulan akuntansi.",
        "Cek kelengkapan nilai produksi/penjualan, persediaan, dan apakah bahan baku termasuk stok untuk periode lain.",
        "Mohon klarifikasi hubungan nilai bahan baku dengan nilai produksi/penjualan pada periode laporan."
      )
    );
  }

  if (productValue > 0 && soldValue > 0 && openingFinishedGoods > 0) {
    const indicativeEnding = openingFinishedGoods + productValue - soldValue;
    const tolerance = Math.max(productValue, soldValue, openingFinishedGoods) * 0.35;
    if (Math.abs(indicativeEnding - endingFinishedGoods) > tolerance) {
      findings.push(
        finding(
          "inventory",
          "FINISHED_GOODS_VALUE_RECONCILIATION",
          "Relasi persediaan-produksi-penjualan",
          "MEDIUM",
          "Nilai persediaan barang jadi tidak selaras secara indikatif dengan produksi dan penjualan.",
          `awal barang jadi ${formatRupiah(openingFinishedGoods)}; nilai produksi ${formatRupiah(productValue)}; nilai penjualan ${formatRupiah(soldValue)}; akhir barang jadi ${formatRupiah(endingFinishedGoods)}`,
          "Estimasi sederhana: persediaan akhir barang jadi kira-kira dipengaruhi persediaan awal + nilai produksi - nilai penjualan. Perbedaan dapat terjadi karena harga pokok, retur, WIP, ekspor, atau klasifikasi nilai.",
          "Gunakan sebagai catatan klarifikasi ringan bila selisih besar; jangan jadikan satu-satunya dasar penolakan.",
          "Mohon klarifikasi perubahan persediaan barang jadi terhadap produksi dan penjualan pada periode laporan."
        )
      );
    }
  }

  const ownershipNumbers = ["Swasta Nasional", "Pemerintah Pusat", "Pemerintah Daerah", "Asing"]
    .map((label) => ownershipPercentage(report.sectionsText.investment, label))
    .filter((value): value is number => value !== null);
  const ownershipTotal = sum(ownershipNumbers);
  if (ownershipNumbers.length >= 2 && ownershipTotal > 0 && Math.abs(ownershipTotal - 100) > 0.5) {
    findings.push(
      finding("investment", "OWNERSHIP_NOT_100", "Persentase kepemilikan", "HIGH", "Total persentase kepemilikan tidak sama dengan 100%.", `${formatNumber(ownershipTotal, 2)}%`, "Swasta Nasional + Pemerintah + Asing harus mendekati 100%.", "Cek persentase kepemilikan.", "Mohon konfirmasi persentase kepemilikan modal.")
    );
  }

  if (report.labor.totalWorkers > 0 && report.labor.educationTotal > 0 && Math.abs(report.labor.totalWorkers - report.labor.educationTotal) > 5) {
    findings.push(
      finding("labor", "LABOR_EDUCATION_MISMATCH", "Total pendidikan vs pekerja", "MEDIUM", "Total pendidikan tidak sama dengan total pekerja.", `pekerja ${report.labor.totalWorkers}; pendidikan ${report.labor.educationTotal}`, "Total kategori pendidikan seharusnya mendekati total pekerja.", "Cek pengisian tingkat pendidikan.", "Mohon cek kembali total pekerja menurut tingkat pendidikan.")
    );
  }
  if (productionKg > 0 && report.labor.totalWorkers === 0) {
    findings.push(finding("labor", "PRODUCTION_WITH_ZERO_LABOR", "Tenaga kerja", "HIGH", "Produksi ada tetapi tenaga kerja nol.", formatNumber(productionKg), "Produksi > 0 dan total pekerja = 0.", "Cek data tenaga kerja.", "Mohon isi atau klarifikasi tenaga kerja."))
  }

  const waterTotal = sum(report.waterRows.map((row) => parseIndonesianNumber(row.Jumlah) ?? 0));
  if (productionKg > 0 && waterTotal === 0) {
    findings.push(finding("water", "PRODUCTION_WITHOUT_WATER", "Air produksi", "MEDIUM", "Produksi ada tetapi penggunaan air nol.", `${formatNumber(productionKg)} kg`, "Produksi > 0 dan total penggunaan air = 0.", "Cek sumber air proses produksi.", "Mohon klarifikasi penggunaan air proses produksi."));
  }

  const electricityKwh = parseIndonesianNumber(report.sectionsText.energy.match(/Dari PLN\s+([\d.,]+)\s+kWh/i)?.[1] ?? "0") ?? 0;
  const electricityValue = parseIndonesianNumber(report.sectionsText.energy.match(/Dari PLN\s+[\d.,]+\s+kWh\s+Rp\.\s*([\d.]+)/i)?.[1] ?? "0") ?? 0;
  if (productionKg > 0 && electricityKwh === 0) {
    findings.push(finding("energy", "PRODUCTION_WITHOUT_ELECTRICITY", "Energi", "HIGH", "Produksi ada tetapi listrik PLN nol/tidak terbaca.", `${formatNumber(productionKg)} kg`, "Produksi > 0 dan kWh PLN = 0.", "Cek penggunaan listrik/bahan bakar.", "Mohon klarifikasi penggunaan listrik produksi."));
  }
  if (electricityKwh > 0 && electricityValue > 0) {
    const cost = electricityValue / electricityKwh;
    if (cost < 500 || cost > 5000) {
      findings.push(finding("energy", "ELECTRICITY_COST_OUTLIER", "Biaya listrik/kWh", "MEDIUM", "Biaya listrik per kWh di luar rentang sanity.", `${formatRupiah(cost)}/kWh`, "Biaya listrik = nilai PLN / kWh; rentang sanity Rp500-Rp5.000/kWh.", "Cek nilai tagihan dan kWh.", "Mohon klarifikasi biaya listrik per kWh."));
    }
  }
  if (productionKg > 0 && electricityKwh > 0) {
    const kwhPerKg = electricityKwh / productionKg;
    if (kwhPerKg > 5) {
      findings.push(
        finding(
          "energy",
          "ELECTRICITY_INTENSITY_HIGH",
          "Relasi produksi-energi",
          "MEDIUM",
          "Intensitas listrik terhadap produksi sangat tinggi.",
          `${formatNumber(kwhPerKg, 3)} kWh/kg`,
          "Intensitas listrik = kWh PLN / kg produksi. Threshold sanity awal >5 kWh/kg.",
          "Cek kWh, kg produksi, dan apakah listrik mencakup aktivitas non-produksi.",
          "Mohon klarifikasi intensitas listrik terhadap produksi."
        )
      );
    }
  }
  if (productionKg > 0 && waterTotal > 0) {
    const waterPerKg = waterTotal / productionKg;
    if (waterPerKg > 0.5) {
      findings.push(
        finding(
          "water",
          "WATER_INTENSITY_HIGH",
          "Relasi produksi-air",
          "MEDIUM",
          "Intensitas penggunaan air terhadap produksi sangat tinggi.",
          `${formatNumber(waterPerKg, 4)} m3/kg`,
          "Intensitas air = total m3 air proses / kg produksi. Threshold sanity awal >0,5 m3/kg.",
          "Cek volume air, kg produksi, dan apakah air mencakup utilitas non-produksi.",
          "Mohon klarifikasi intensitas penggunaan air terhadap produksi."
        )
      );
    }
  }

  const wage = Number(report.expenses["Upah/gaji untuk pekerja produksi"] ?? 0) + Number(report.expenses["Upah/gaji untuk pekerja lainnya"] ?? 0);
  if (report.labor.totalWorkers > 0 && wage > 0) {
    const wagePerWorker = wage / report.labor.totalWorkers;
    if (wagePerWorker < 3_000_000) {
      findings.push(finding("expenses", "LOW_WAGE_PER_WORKER", "Upah rata-rata", "MEDIUM", "Upah rata-rata per pekerja per triwulan rendah.", `${formatRupiah(wagePerWorker)}/pekerja/triwulan`, "Total upah / total pekerja.", "Cek apakah semua upah/gaji sudah masuk.", "Mohon klarifikasi komponen upah/gaji pekerja."));
    }
  }
  if (String(report.expenses["Memiliki unit litbang"] ?? "").toLowerCase().includes("tidak") && Number(report.expenses["Biaya research and development"] ?? 0) > 0) {
    findings.push(finding("expenses", "RD_COST_WITHOUT_UNIT", "Litbang", "LOW", "Biaya R&D ada tetapi unit litbang tidak ada.", "", "Unit litbang = Tidak dan biaya R&D > 0.", "Cek isian litbang.", "Mohon klarifikasi biaya R&D dan unit litbang."));
  }

  for (const row of report.machineRows) {
    const made = parseIndonesianNumber(row.TahunPembuatan) ?? 0;
    const acquired = parseIndonesianNumber(row.TahunPerolehan) ?? 0;
    if (made === 0) findings.push(finding("machines", "MACHINE_YEAR_ZERO", "Tahun mesin", "MEDIUM", "Tahun pembuatan mesin kosong/nol.", row.Mesin, "Tahun pembuatan = 0.", "Lengkapi tahun pembuatan mesin.", "Mohon lengkapi tahun pembuatan mesin."));
    if (made > 0 && acquired > 0 && acquired < made) findings.push(finding("machines", "MACHINE_ACQUIRED_BEFORE_MADE", "Tahun mesin", "HIGH", "Tahun perolehan sebelum tahun pembuatan.", row.Mesin, "Tahun perolehan < tahun pembuatan.", "Cek tahun mesin.", "Mohon cek tahun pembuatan dan perolehan mesin."));
  }

  const solidWasteKg = sum(report.solidWasteRows.map((row) => rowQuantityKg(row, "ton")));
  if (productionKg > 0 && report.solidWasteRows.length === 0) {
    findings.push(finding("solidWaste", "NO_SOLID_WASTE_WITH_PRODUCTION", "Limbah padat", "MEDIUM", "Produksi ada tetapi data limbah padat tidak terbaca.", `${formatNumber(productionKg)} kg`, "Produksi > 0 dan tabel limbah padat kosong.", "Cek pernyataan nihil atau data limbah.", "Mohon klarifikasi limbah padat."));
  }
  if (productionKg > 0 && solidWasteKg > 0) {
    const solidWasteRatio = solidWasteKg / productionKg;
    if (solidWasteRatio > 0.3) {
      findings.push(
        finding(
          "solidWaste",
          "SOLID_WASTE_RATIO_HIGH",
          "Relasi produksi-limbah padat",
          "MEDIUM",
          "Rasio limbah padat terhadap produksi tinggi secara indikatif.",
          `limbah padat ${formatNumber(solidWasteKg)} kg; produksi ${formatNumber(productionKg)} kg; rasio ${formatNumber(solidWasteRatio, 3)}`,
          "Rasio = total limbah padat kg / total produksi kg. Threshold sanity awal >30%.",
          "Cek jenis limbah, satuan ton/kg, dan apakah limbah berasal dari stok/proses periode lain.",
          "Mohon klarifikasi jumlah limbah padat terhadap volume produksi."
        )
      );
    }
  }
  if (report.liquidWaste.codOutlet > report.liquidWaste.codInlet && report.liquidWaste.codInlet > 0) {
    findings.push(finding("liquidWaste", "COD_OUTLET_OVER_INLET", "COD limbah cair", report.liquidWaste.codOutlet > report.liquidWaste.codInlet * 1.5 ? "CRITICAL" : "HIGH", "COD outlet lebih tinggi daripada COD inlet.", `inlet ${formatNumber(report.liquidWaste.codInlet, 2)}; outlet ${formatNumber(report.liquidWaste.codOutlet, 2)}`, "COD outlet seharusnya tidak lebih tinggi daripada inlet setelah pengolahan.", "Cek angka COD inlet/outlet atau proses IPAL.", "Mohon klarifikasi COD inlet dan outlet."));
  }
  if (report.liquidWaste.outletDebit > 10 || report.liquidWaste.inletDebit > 10) {
    findings.push(finding("liquidWaste", "LIQUID_WASTE_DEBIT_TOO_HIGH", "Debit limbah cair", "MEDIUM", "Debit limbah cair perlu dicek satuan/definisinya.", `inlet ${report.liquidWaste.inletDebit} m3/detik; outlet ${report.liquidWaste.outletDebit} m3/detik`, "Jika benar m3/detik, angka >10 m3/detik tergolong sangat besar. Namun pada pelaporan, angka debit kadang merepresentasikan volume periode atau satuan lain; rule ini hanya catatan klarifikasi satuan.", "Cek apakah angka adalah m3/detik, m3/hari, m3/bulan, atau total volume periode.", "Mohon pastikan satuan dan definisi angka debit limbah cair yang dilaporkan."));
  }

  const score = riskScore(findings);
  return {
    findings,
    riskScore: score,
    recommendation: decision(findings, score),
    sectionSummaries: SECTION_ORDER.map((key) => makeSectionSummary(key, findings))
  };
}

function makeSectionSummary(key: ReportSectionKey, findings: Finding[]): SectionSummary {
  const label = SECTION_LABELS[key];
  const related = findings.filter((finding) => finding.section === label);
  const score = riskScore(related);
  const counts = {
    INFO: related.filter((finding) => finding.severity === "INFO").length,
    LOW: related.filter((finding) => finding.severity === "LOW").length,
    MEDIUM: related.filter((finding) => finding.severity === "MEDIUM").length,
    HIGH: related.filter((finding) => finding.severity === "HIGH").length,
    CRITICAL: related.filter((finding) => finding.severity === "CRITICAL").length
  };
  return {
    key,
    label,
    score,
    recommendation: decision(related, score),
    counts,
    topFindings: related.sort((a, b) => WEIGHTS[b.severity] - WEIGHTS[a.severity]).slice(0, 4)
  };
}

export function buildValidatorNote(result: ValidationResult): string {
  const topFindings = result.findings
    .sort((a, b) => WEIGHTS[b.severity] - WEIGHTS[a.severity])
    .slice(0, 5);
  if (topFindings.length === 0) {
    return `Rekomendasi aplikasi: ${result.recommendation}. Tidak ditemukan catatan utama sampai bagian Pengelolaan Limbah Cair.`;
  }
  const details = topFindings
    .map((finding) => `${finding.section}: ${finding.finding} Data: ${finding.detectedValue || "-"}`)
    .join(" ");
  return `Rekomendasi aplikasi: ${result.recommendation} dengan risk score ${result.riskScore}/100. Mohon klarifikasi/perbaikan beberapa catatan utama berikut. ${details}`;
}
