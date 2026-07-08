import { parseIndonesianNumber, toKg } from "./number";
import type {
  CapacityRow,
  InventoryRow,
  LaborSummary,
  LiquidWaste,
  MaterialRow,
  ParsedReport,
  ProductionRow,
  ReportSectionKey,
  TableRow
} from "./types";

type Marker = { key: ReportSectionKey; label: string; test: (line: string, index: number, lines: string[]) => boolean };

export const SECTION_LABELS: Record<ReportSectionKey, string> = {
  identity: "Identitas dan Perizinan",
  general: "Data Umum",
  inventory: "Persediaan",
  capacity: "Kapasitas Produksi",
  production: "Produksi dan Penjualan",
  materials: "Bahan Baku",
  helpers: "Bahan Penolong",
  investment: "Investasi",
  labor: "Tenaga Kerja",
  internship: "Prakerin",
  water: "Penggunaan Air",
  energy: "Energi",
  expenses: "Pengeluaran Perusahaan",
  productionPlan: "Rencana Produksi",
  machines: "Mesin Produksi",
  solidWaste: "Pengelolaan Limbah Padat",
  hazardousWaste: "Pengelolaan Limbah B3",
  liquidWaste: "Pengelolaan Limbah Cair"
};

const MARKERS: Marker[] = [
  { key: "general", label: "Data Umum", test: (line) => /^Data Umum$/i.test(line) },
  { key: "inventory", label: "Persediaan", test: (line) => /^Persediaan$/i.test(line) },
  {
    key: "capacity",
    label: "Kapasitas Produksi",
    test: (line, index, lines) => {
      if (!/^Kapasitas Produksi\b/i.test(line)) return false;
      if (/^Kapasitas Produksi\s+-\s+KBLI\b/i.test(line)) return false;
      const context = lines.slice(index, index + 5).join(" ");
      return /Kapasitas\s+(Sebelum OSS|OSS|Produksi|Terpasang)|Kode\s+HS|No\.?\s+Nama\s+Produk/i.test(context);
    }
  },
  { key: "production", label: "Produksi dan Penjualan", test: (line) => /^Produksi dan Penjualan$/i.test(line) },
  { key: "materials", label: "Bahan Baku", test: (line) => /^Bahan Baku$/i.test(line) },
  { key: "helpers", label: "Bahan Penolong", test: (line) => /^Bahan Penolong$/i.test(line) },
  { key: "investment", label: "Investasi", test: (line) => /^Investasi$/i.test(line) },
  { key: "labor", label: "Tenaga Kerja", test: (line) => /^Tenaga Kerja$/i.test(line) },
  { key: "internship", label: "Prakerin", test: (line) => /^Prakerin$/i.test(line) },
  { key: "water", label: "Penggunaan Air", test: (line) => /^Penggunaan Air/i.test(line) },
  { key: "energy", label: "Energi", test: (line) => /^Penggunaan Bahan Bakar$/i.test(line) },
  { key: "expenses", label: "Pengeluaran Perusahaan", test: (line) => /^Pengeluaran Perusahaan$/i.test(line) },
  { key: "productionPlan", label: "Rencana Produksi", test: (line) => /^Rencana Produksi$/i.test(line) },
  { key: "machines", label: "Mesin Produksi", test: (line) => /^Mesin Produksi$/i.test(line) },
  { key: "solidWaste", label: "Pengelolaan Limbah Padat", test: (line) => /^Pengelolaan Limbah Padat$/i.test(line) },
  { key: "hazardousWaste", label: "Pengelolaan Limbah B3", test: (line) => /^Pengelolaan Limbah B3$/i.test(line) },
  { key: "liquidWaste", label: "Pengelolaan Limbah Cair", test: (line) => /^Pengelolaan Limbah Cair$/i.test(line) }
];

const SECTION_ORDER: ReportSectionKey[] = [
  "identity",
  "general",
  "inventory",
  "capacity",
  "production",
  "materials",
  "helpers",
  "investment",
  "labor",
  "internship",
  "water",
  "energy",
  "expenses",
  "productionPlan",
  "machines",
  "solidWaste",
  "hazardousWaste",
  "liquidWaste"
];

function normalizeText(text: string): string {
  return text
    .replace(/\u00a0/g, " ")
    .replace(/[\uf0f6\uf081]/g, "")
    .replace(/[]/g, "")
    .replace(/\r/g, "")
    .replace(/[ \t]+/g, " ")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function getLines(text: string): string[] {
  return normalizeText(text)
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

function cutAfterLiquidWaste(lines: string[]): string[] {
  const liquidWasteIndex = lines.findIndex((line) => /^Pengelolaan Limbah Cair$/i.test(line));
  const searchFrom = liquidWasteIndex >= 0 ? liquidWasteIndex + 1 : 0;
  const indiIndex = lines.slice(searchFrom).findIndex((line) => /^Indi 4\.0$/i.test(line) || /^Buka\s+Indi 4\.0$/i.test(line));
  if (indiIndex >= 0) return lines.slice(0, searchFrom + indiIndex);
  if (liquidWasteIndex >= 0) return lines;
  const fallbackIndiIndex = lines.findIndex((line) => /^Indi 4\.0$/i.test(line) || /^Buka\s+Indi 4\.0$/i.test(line));
  return fallbackIndiIndex >= 0 ? lines.slice(0, fallbackIndiIndex) : lines;
}

function sectionize(lines: string[]): Record<ReportSectionKey, string> {
  const limited = cutAfterLiquidWaste(lines);
  const hits: Array<Marker & { index: number }> = [];
  let searchFrom = 0;
  for (const marker of MARKERS) {
    const relativeIndex = limited.slice(searchFrom).findIndex((line, offset) => marker.test(line, searchFrom + offset, limited));
    if (relativeIndex < 0) continue;
    const index = searchFrom + relativeIndex;
    hits.push({ ...marker, index });
    searchFrom = index + 1;
  }

  const sections = Object.fromEntries(SECTION_ORDER.map((key) => [key, ""])) as Record<ReportSectionKey, string>;
  const firstMarker = Math.min(...hits.map((hit) => hit.index), limited.length);
  sections.identity = limited.slice(0, firstMarker).join("\n");

  const sortedHits = hits.sort((a, b) => a.index - b.index);
  for (let index = 0; index < sortedHits.length; index += 1) {
    const current = sortedHits[index];
    const next = sortedHits[index + 1];
    sections[current.key] = limited.slice(current.index, next?.index ?? limited.length).join("\n");
  }
  return sections;
}

function valueAfter(label: string, text: string): string {
  const escaped = label.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const match = text.match(new RegExp(`${escaped}\\s+([^\\n]+)`, "i"));
  return match?.[1]?.trim() ?? "";
}

function parseIdentity(text: string): Record<string, string> {
  const lines = getLines(text);
  const identity: Record<string, string> = {};
  identity["Nama Perusahaan"] = lines.find((line) => /^PT\s+/i.test(line)) ?? lines[0] ?? "";
  for (const label of ["Alamat Kantor", "Alamat Pabrik", "Gudang", "Nomor Telp.", "Nomor Fax", "NIB", "Perizinan", "Sertifikat", "Bidang Usaha"]) {
    const value = valueAfter(label, text);
    if (value) identity[label] = value;
  }
  identity["KBLI"] = [...text.matchAll(/KBLI\s+(\d{5})/gi)].map((match) => match[1]).join(", ");
  return identity;
}

function parseGeneral(text: string): Record<string, string> {
  const general: Record<string, string> = {};
  for (const label of [
    "Periode Laporan",
    "Nilai Investasi (PP No 7/Tanpa Tanah dan Bangunan)",
    "Menggunakan Maklon",
    "Menyediakan Maklon",
    "Nama Penanda Tangan Laporan",
    "Jabatan"
  ]) {
    const value = valueAfter(label, text);
    if (value) general[label] = value;
  }
  const statusIndex = getLines(text).findIndex((line) => /^Status Berproduksi$/i.test(line));
  if (statusIndex >= 0) {
    const lines = getLines(text).slice(statusIndex, statusIndex + 5);
    general["Status Berproduksi"] = lines[0].replace(/^Status\s+/i, "").trim() || (lines.includes("Buka") ? "Buka" : lines[1] ?? "");
  }
  const statusValue = valueAfter("Status", text);
  if (statusValue && !/^Berproduksi\s+Menggunakan Maklon/i.test(statusValue)) general["Status Berproduksi"] = statusValue;
  return general;
}

function parseInventory(text: string): InventoryRow[] {
  return getLines(text)
    .map((line) => {
      const match = line.match(/^(.+?)\s+([\d.]+)\s+([\d.]+)$/);
      if (!match || !/^Nilai persediaan/i.test(match[1])) return null;
      return {
        type: match[1],
        startValue: parseIndonesianNumber(match[2]) ?? 0,
        endValue: parseIndonesianNumber(match[3]) ?? 0
      };
    })
    .filter((row): row is InventoryRow => Boolean(row));
}

function uniqueInventoryRows(rows: InventoryRow[]): InventoryRow[] {
  const seen = new Set<string>();
  return rows.filter((row) => {
    const key = `${row.type}|${row.startValue}|${row.endValue}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

export function parseCapacityRows(text: string): CapacityRow[] {
  const rows: CapacityRow[] = [];
  for (const line of getLines(text)) {
    const match = line.match(
      /^\d+\.?\s+(.+?)\s+(\d{5})\s+(\d{6,10})\s+([\d.,]+\s+\S+)\s+([\d.,]+\s+\S+)\s+([\d.,]+\s+Kilogram)\s+([\d.,]+\s+Kilogram)/i
    );
    if (!match) continue;
    rows.push({
      product: match[1].trim(),
      kbli: match[2],
      hs: match[3],
      productionOriginal: match[4],
      installedOriginal: match[5],
      productionKg: toKg(match[6]),
      installedKg: toKg(match[7])
    });
  }
  return rows;
}

export function parseProductionRows(text: string): ProductionRow[] {
  const rows: ProductionRow[] = [];
  for (const line of getLines(text)) {
    const head = line.match(/^\d+\.?\s+(.+?)\s+(\d{5})\s+(\d{6,10})\s+(.+)$/);
    if (!head) continue;
    const [, productRaw, kbli, hs, rest] = head;
    const values = [...rest.matchAll(/[\d.]+,\d{2}|[\d.]+/g)].map((match) => match[0]);
    if (values.length < 6) continue;
    const unitMatch = rest.match(/\b(kilogram|kg|ton|liter|ct|unit)\b/i);
    const stockSoldMatch = rest.match(/\b(Ya|Tidak)\b\s+\d+(?:,\d+)?%/i);
    const exportPercent = rest.match(/(\d+(?:,\d+)?)%/);
    rows.push({
      product: productRaw.replace(/\(.*?\)/g, "").trim(),
      kbli,
      hs,
      unit: unitMatch?.[1] ?? "",
      productionQty: parseIndonesianNumber(values[0]) ?? 0,
      productionKg: parseIndonesianNumber(values[1]) ?? 0,
      productionValue: parseIndonesianNumber(values[2]) ?? 0,
      salesQty: parseIndonesianNumber(values[3]) ?? 0,
      salesKg: parseIndonesianNumber(values[4]) ?? 0,
      salesValue: parseIndonesianNumber(values[5]) ?? 0,
      stockSoldFlag: /^ya$/i.test(stockSoldMatch?.[1] ?? ""),
      exportPercent: parseIndonesianNumber(exportPercent?.[1] ?? "0") ?? 0
    });
  }
  return rows;
}

export function parseMaterialRows(text: string): MaterialRow[] {
  const rows: MaterialRow[] = [];
  for (const line of getLines(text)) {
    const match = line.match(/^(\d+)\s+(.+?)\s+(\d{6,10})\s+(\S+)\s+(.+)$/);
    if (!match) continue;
    const tailValues = [...match[5].matchAll(/[\d.]+,\d{2}|[\d.]+/g)].map((hit) => hit[0]);
    if (tailValues.length < 6) continue;
    const kbliMatch = match[5].match(/\b(\d{5})\b/);
    rows.push({
      name: match[2].trim(),
      hs: match[3],
      unit: match[4],
      domesticQty: parseIndonesianNumber(tailValues[0]) ?? 0,
      domesticKg: parseIndonesianNumber(tailValues[1]) ?? 0,
      domesticValue: parseIndonesianNumber(tailValues[2]) ?? 0,
      importQty: parseIndonesianNumber(tailValues[3]) ?? 0,
      importKg: parseIndonesianNumber(tailValues[4]) ?? 0,
      importValue: parseIndonesianNumber(tailValues[5]) ?? 0,
      kbliProduct: kbliMatch?.[1] ?? "",
      productName: "",
      inventoryKg: parseIndonesianNumber(tailValues.at(-2) ?? "0") ?? 0,
      inventoryValue: parseIndonesianNumber(tailValues.at(-1) ?? "0") ?? 0
    });
  }
  return rows;
}

function parseLabor(text: string): LaborSummary {
  const lines = getLines(text);
  const male = lines.find((line) => /^Laki-Laki\s+/i.test(line))?.match(/\d+/g)?.map(Number) ?? [];
  const female = lines.find((line) => /^Wanita\s+/i.test(line))?.match(/\d+/g)?.map(Number) ?? [];
  const educationLine = lines.find((line) => /^0\s+0\s+\d+\s+\d+/.test(line));
  const education = educationLine?.match(/\d+/g)?.map(Number) ?? [];
  const totalWorkers = [...male, ...female].reduce((sum, value) => sum + value, 0);
  return {
    productionPermanentMale: male[0] ?? 0,
    productionTemporaryMale: male[1] ?? 0,
    otherPermanentMale: male[2] ?? 0,
    otherTemporaryMale: male[3] ?? 0,
    productionPermanentFemale: female[0] ?? 0,
    productionTemporaryFemale: female[1] ?? 0,
    otherPermanentFemale: female[2] ?? 0,
    otherTemporaryFemale: female[3] ?? 0,
    educationTotal: education.reduce((sum, value) => sum + value, 0),
    totalWorkers
  };
}

function parseSimpleNumberRows(text: string): TableRow[] {
  return getLines(text)
    .map((line) =>
      line.match(
        /^(\d+\.?)\s+(.+?)\s+([\d.,]+(?:\s+(?:kg|kilogram|ton|m3|m³|kwh|mmbtu|orang|hari|unit|liter|ltr|mtq))?)(?:\s+([\d.]+))?$/i
      )
    )
    .filter((match): match is RegExpMatchArray => Boolean(match))
    .map((match) => ({
      No: match[1],
      Uraian: match[2],
      Jumlah: match[3],
      Nilai: match[4] ?? ""
    }));
}

function parseWasteRows(text: string): TableRow[] {
  const simpleRows = parseSimpleNumberRows(text);
  if (simpleRows.length > 0) return simpleRows;

  return getLines(text)
    .map((line) => line.match(/^(?:\d+\.?\s+)?(.+?)\s+([\d.,]+)\s*(ton|kg|kilogram)\b/i))
    .filter((match): match is RegExpMatchArray => Boolean(match))
    .map((match, index) => ({
      No: String(index + 1),
      Uraian: match[1].trim(),
      Jumlah: `${match[2]} ${match[3]}`,
      Nilai: ""
    }));
}

function parseExpenses(text: string): Record<string, number | string> {
  const result: Record<string, number | string> = {};
  for (const line of getLines(text)) {
    const money = line.match(/^(.+?)\s+Rp\.\s*([\d.]+)$/i);
    if (money) result[money[1]] = parseIndonesianNumber(money[2]) ?? 0;
    const litbang = line.match(/^(Memiliki unit litbang|Jumlah researcher \/ periset dari unit litbang)\s+(.+)$/i);
    if (litbang) result[litbang[1]] = litbang[2];
  }
  return result;
}

function parseLiquidWaste(text: string): LiquidWaste {
  return {
    inletDebit: parseIndonesianNumber(valueAfter("Debit limbah cair di inlet", text)) ?? 0,
    outletDebit: parseIndonesianNumber(valueAfter("Debit limbah cair di outlet", text)) ?? 0,
    codInlet: parseIndonesianNumber(valueAfter("COD pada saluran inlet (sebelum diolah di IPAL)", text)) ?? 0,
    codOutlet: parseIndonesianNumber(valueAfter("COD pada saluran outlet (titik pemetaan)", text)) ?? 0,
    sludgeRemoved: parseIndonesianNumber(valueAfter("Sludge removed", text)) ?? 0
  };
}

function parseMachineRows(text: string): TableRow[] {
  return getLines(text)
    .map((line) => line.match(/^(\d+)\.\s+(.+?)\s+(\d{4}|0)\s+(\d{4}|0)\s+(.+)$/))
    .filter((match): match is RegExpMatchArray => Boolean(match))
    .map((match) => ({
      No: match[1],
      Mesin: match[2],
      TahunPembuatan: match[3],
      TahunPerolehan: match[4],
      Detail: match[5]
    }));
}

export function parseReportFromText(text: string, fileName = "laporan.pdf"): ParsedReport {
  const normalized = normalizeText(text);
  const lines = getLines(normalized);
  const sectionsText = sectionize(lines);
  const parserWarnings: string[] = [];
  const identity = parseIdentity(sectionsText.identity);
  const general = parseGeneral(`${sectionsText.general}\n${sectionsText.inventory}`);
  const companyName = identity["Nama Perusahaan"] || fileName.replace(/\.pdf$/i, "");
  const capacity = parseCapacityRows(sectionsText.capacity);
  const production = parseProductionRows(sectionsText.production);
  const materials = parseMaterialRows(sectionsText.materials);
  const helpers = parseMaterialRows(sectionsText.helpers);

  for (const key of SECTION_ORDER) {
    if (key !== "identity" && !sectionsText[key]) parserWarnings.push(`Bagian ${SECTION_LABELS[key]} tidak ditemukan pada teks PDF.`);
  }
  if (capacity.length === 0 && sectionsText.capacity) parserWarnings.push("Tabel kapasitas ditemukan tetapi baris kapasitas belum berhasil diparse penuh.");
  if (production.length === 0 && sectionsText.production) parserWarnings.push("Tabel produksi ditemukan tetapi baris produksi belum berhasil diparse penuh.");

  return {
    fileName,
    rawText: normalized,
    companyName,
    identity,
    general,
    sectionsText,
    inventory: uniqueInventoryRows(parseInventory(`${sectionsText.inventory}\n${sectionsText.machines}`)),
    capacity,
    production,
    materials,
    helpers,
    labor: parseLabor(sectionsText.labor),
    waterRows: parseSimpleNumberRows(sectionsText.water),
    energyRows: parseSimpleNumberRows(sectionsText.energy),
    expenses: parseExpenses(sectionsText.expenses),
    productionPlanRows: parseSimpleNumberRows(sectionsText.productionPlan),
    machineRows: parseMachineRows(sectionsText.machines),
    solidWasteRows: parseWasteRows(sectionsText.solidWaste),
    hazardousWasteRows: parseWasteRows(sectionsText.hazardousWaste),
    liquidWaste: parseLiquidWaste(sectionsText.liquidWaste),
    parserWarnings
  };
}

