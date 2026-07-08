import { parseReportFromText, SECTION_LABELS } from "./reportParser";
import type { ReportSectionKey } from "./types";

export type IntraNewSource = {
  fileName: string;
  text: string;
};

export type IntraNewImportResult = {
  fileNames: string[];
  text: string;
  warnings: string[];
};

const SECTION_ORDER = Object.keys(SECTION_LABELS) as ReportSectionKey[];

function normalizeHeader(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
}

function parseCsvRows(text: string): string[][] {
  const rows: string[][] = [];
  let row: string[] = [];
  let value = "";
  let quoted = false;

  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    const next = text[index + 1];
    if (char === '"') {
      if (quoted && next === '"') {
        value += '"';
        index += 1;
      } else {
        quoted = !quoted;
      }
      continue;
    }
    if (char === "," && !quoted) {
      row.push(value.trim());
      value = "";
      continue;
    }
    if ((char === "\n" || char === "\r") && !quoted) {
      if (char === "\r" && next === "\n") index += 1;
      row.push(value.trim());
      if (row.some(Boolean)) rows.push(row);
      row = [];
      value = "";
      continue;
    }
    value += char;
  }
  row.push(value.trim());
  if (row.some(Boolean)) rows.push(row);
  return rows;
}

function rowGetter(headers: string[], row: string[]) {
  const indexByHeader = new Map(headers.map((header, index) => [normalizeHeader(header), index]));
  return (candidates: string[], fallback = "") => {
    for (const candidate of candidates) {
      const index = indexByHeader.get(normalizeHeader(candidate));
      if (index !== undefined) return row[index] ?? fallback;
    }
    return fallback;
  };
}

function numbered(value: string, index: number): string {
  const clean = value.trim();
  return clean || `${index + 1}.`;
}

function productionCsvToText(headers: string[], rows: string[][]): string {
  const lines = ["Produksi dan Penjualan"];
  rows.forEach((row, index) => {
    const get = rowGetter(headers, row);
    const no = numbered(get(["No.", "No"]), index);
    const product = get(["Produk", "Nama Produk"], "Produk");
    const kbli = get(["KBLI"], "");
    const hs = get(["Kode HS", "HS"], "");
    const unit = get(["Satuan Asli"], "kilogram");
    const productionQty = get(["Jumlah Produksi Satuan Asli", "Jumlah Produksi"], "0");
    const productionKg = get(["Jumlah Produksi Satuan Standar (Kilogram)", "Jumlah Produksi Kilogram"], "0");
    const productionValue = get(["Nilai Produksi (Rp.)", "Nilai Produksi"], "0");
    const salesQty = get(["Jumlah Penjualan Satuan Asli", "Jumlah Penjualan"], "0");
    const salesKg = get(["Jumlah Penjualan Satuan Standar (Kilogram)", "Jumlah Penjualan Kilogram"], "0");
    const salesValue = get(["Nilai Penjualan", "Nilai Penjualan (Rp.)"], "0");
    const stockFlag = get(["Terdapat Stok Yang Dijual"], "Tidak") || "Tidak";
    const exportPct = get(["Persentase Ekspor Penjualan (%)", "% Ekspor"], "0,00%");
    lines.push(`${no} ${product} ${kbli} ${hs} ${unit} ${productionQty} ${productionKg} ${productionValue} ${salesQty} ${salesKg} ${salesValue} ${stockFlag} ${exportPct}`);
  });
  return lines.join("\n");
}

function materialCsvToText(headers: string[], rows: string[][], sectionTitle: string): string {
  const lines = [sectionTitle];
  rows.forEach((row, index) => {
    const get = rowGetter(headers, row);
    const no = numbered(get(["No.", "No"]), index).replace(/\.$/, "");
    const name = get(["Nama Bahan Baku", "Nama Bahan", "Nama Bahan Penolong"], "Bahan");
    const hs = get(["Kode HS", "HS"], "");
    const unit = get(["Satuan Asli"], "kilogram");
    const domesticQty = get(["Jumlah Dalam Negeri (Satuan Asli)"], "0");
    const domesticKg = get(["Jumlah Dalam Negeri (Kilogram)"], "0");
    const domesticValue = get(["Nilai Dalam Negeri (Rp.)"], "0");
    const importQty = get(["Jumlah Luar Negeri (Satuan Asli)", "Jumlah Impor (Satuan Asli)"], "0");
    const importKg = get(["Jumlah Luar Negeri (Kilogram)", "Jumlah Impor (Kilogram)"], "0");
    const importValue = get(["Nilai Luar Negeri (Rp.)", "Nilai Impor (Rp.)"], "0");
    const outputKbli = get(["KBLI Produk Yang Dihasilkan"], "");
    const inventoryKg = get(["Jumlah Persediaan (Kilogram)"], "0");
    const inventoryValue = get(["Nilai Persediaan (Rp.)"], "0");
    lines.push(`${no} ${name} ${hs} ${unit} ${domesticQty} ${domesticKg} ${domesticValue} ${importQty} ${importKg} ${importValue} ${outputKbli} ${inventoryKg} ${inventoryValue}`);
  });
  return lines.join("\n");
}

function capacityCsvToText(headers: string[], rows: string[][]): string {
  const lines = ["Kapasitas Produksi"];
  rows.forEach((row, index) => {
    const get = rowGetter(headers, row);
    const no = numbered(get(["No.", "No"]), index);
    const product = get(["Produk", "Nama Produk"], "Produk");
    const kbli = get(["KBLI"], "");
    const hs = get(["Kode HS", "HS"], "");
    const productionOriginal = get(["Kapasitas Produksi Satuan Asli", "Kapasitas Produksi"], "0 ton");
    const installedOriginal = get(["Kapasitas Terpasang Satuan Asli", "Kapasitas Terpasang"], productionOriginal);
    const productionKg = get(["Kapasitas Produksi Satuan Standar (Kilogram)", "Kapasitas Produksi Kilogram"], "0 Kilogram");
    const installedKg = get(["Kapasitas Terpasang Satuan Standar (Kilogram)", "Kapasitas Terpasang Kilogram"], productionKg);
    lines.push(`${no} ${product} ${kbli} ${hs} ${productionOriginal} ${installedOriginal} ${productionKg} ${installedKg}`);
  });
  return lines.join("\n");
}

function detectCsvSection(fileName: string, headers: string[]): ReportSectionKey | null {
  const normalizedName = normalizeHeader(fileName);
  const normalizedHeaders = headers.map(normalizeHeader).join(" | ");
  if (normalizedName.includes("bahanpenolong")) return "helpers";
  if (normalizedName.includes("bahanbaku")) return "materials";
  if (normalizedName.includes("produksi")) return "production";
  if (normalizedName.includes("kapasitas")) return "capacity";
  if (normalizedHeaders.includes("jumlah produksi") && normalizedHeaders.includes("nilai produksi")) return "production";
  if (normalizedHeaders.includes("nama bahan baku") && normalizedHeaders.includes("nilai dalam negeri")) return normalizedName.includes("penolong") ? "helpers" : "materials";
  if (normalizedHeaders.includes("kapasitas") && normalizedHeaders.includes("kode hs")) return "capacity";
  return null;
}

export function csvToSectionText(fileName: string, csvText: string): { key: ReportSectionKey | null; text: string; warning?: string } {
  const rows = parseCsvRows(csvText);
  if (rows.length < 2) return { key: null, text: "", warning: `${fileName}: CSV kosong atau tidak memiliki baris data.` };
  const [headers, ...dataRows] = rows;
  const key = detectCsvSection(fileName, headers);
  if (key === "production") return { key, text: productionCsvToText(headers, dataRows) };
  if (key === "materials") return { key, text: materialCsvToText(headers, dataRows, "Bahan Baku") };
  if (key === "helpers") return { key, text: materialCsvToText(headers, dataRows, "Bahan Penolong") };
  if (key === "capacity") return { key, text: capacityCsvToText(headers, dataRows) };
  return { key: null, text: "", warning: `${fileName}: jenis CSV belum dikenali, file dilewati.` };
}

export function htmlToPlainText(html: string): string {
  return html
    .replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<br\s*\/?>/gi, "\n")
    .replace(/<\/(tr|table|thead|tbody|div|section|article|p|h1|h2|h3|h4|li)>/gi, "\n")
    .replace(/<\/t[dh]>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#039;/g, "'")
    .replace(/[ \t]+/g, " ")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

export function buildIntraNewImportText(sources: IntraNewSource[]): IntraNewImportResult {
  const warnings: string[] = [];
  const fileNames = sources.map((source) => source.fileName);
  const htmlSource = sources.find((source) => /\.(html?|xhtml)$/i.test(source.fileName));
  const htmlText = htmlSource ? htmlToPlainText(htmlSource.text) : "";
  const htmlReport = htmlText ? parseReportFromText(htmlText, htmlSource?.fileName ?? "intranew.html") : null;
  const sectionTexts = new Map<ReportSectionKey, string>();

  for (const source of sources) {
    if (!/\.csv$/i.test(source.fileName)) {
      if (!/\.(html?|xhtml)$/i.test(source.fileName)) warnings.push(`${source.fileName}: hanya HTML dan CSV yang didukung pada tahap import manual.`);
      continue;
    }
    const parsed = csvToSectionText(source.fileName, source.text);
    if (parsed.warning) warnings.push(parsed.warning);
    if (parsed.key && parsed.text) sectionTexts.set(parsed.key, parsed.text);
  }

  if (sectionTexts.size === 0) {
    return {
      fileNames,
      text: htmlText,
      warnings: htmlText ? warnings : [...warnings, "Tidak ada HTML/CSV yang berhasil diproses."]
    };
  }

  const identity = htmlReport?.sectionsText.identity || `Import IntraNEW\nSumber file ${fileNames.join(", ")}`;
  const mergedSections = SECTION_ORDER.filter((key) => key !== "identity")
    .map((key) => sectionTexts.get(key) || htmlReport?.sectionsText[key] || "")
    .filter(Boolean);

  return {
    fileNames,
    text: [identity, ...mergedSections].join("\n\n"),
    warnings
  };
}

export async function importIntraNewFiles(files: File[]): Promise<IntraNewImportResult> {
  const sources = await Promise.all(
    files.map(async (file) => ({
      fileName: file.name,
      text: await file.text()
    }))
  );
  return buildIntraNewImportText(sources);
}
