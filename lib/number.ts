export type ParsedQuantity = {
  value: number | null;
  unit: string;
  original: string;
};

const NUMBER_RE = /[-+]?\d[\d.,]*/;
const CURRENCY_RE = /\b(?:rp\.?|idr|rupiah)\b/gi;

export function parseIndonesianNumber(input: unknown): number | null {
  if (input === null || input === undefined) return null;
  if (typeof input === "number") return Number.isFinite(input) ? input : null;
  if (typeof input === "boolean") return input ? 1 : 0;

  let text = String(input).trim();
  if (!text || /^[-–—]$/.test(text)) return null;
  const negative = text.startsWith("(") && text.endsWith(")");
  text = text.replace(CURRENCY_RE, "").replace(/\u00a0/g, " ").replace("−", "-");
  const match = text.match(NUMBER_RE);
  if (!match) return null;

  let token = match[0].trim();
  const sign = token.startsWith("-") ? -1 : 1;
  token = token.replace(/^[-+]/, "");
  let normalized = token;

  if (token.includes(",")) {
    normalized = token.replace(/\./g, "").replace(",", ".");
  } else if (token.includes(".")) {
    const parts = token.split(".");
    if (parts.length > 2) {
      normalized = parts.join("");
    } else {
      const [integer, fraction] = parts;
      if (fraction.length === 3 && (fraction !== "000" || integer.length <= 3)) {
        normalized = integer + fraction;
      } else if (fraction.length >= 4 && /^0+$/.test(fraction)) {
        normalized = integer;
      } else if (fraction.length > 3) {
        normalized = `${integer}.${fraction}`;
      } else if (integer.length > 3 && fraction === "000") {
        normalized = integer;
      } else {
        normalized = `${integer}.${fraction}`;
      }
    }
  }

  const parsed = Number(normalized) * sign * (negative ? -1 : 1);
  if (!Number.isFinite(parsed)) return null;
  return Math.abs(parsed - Math.round(parsed)) < 1e-9 ? Math.round(parsed) : parsed;
}

export function parseQuantity(input: unknown): ParsedQuantity {
  const original = input === null || input === undefined ? "" : String(input).trim();
  const value = parseIndonesianNumber(original);
  const withoutCurrency = original.replace(CURRENCY_RE, "");
  const match = withoutCurrency.match(NUMBER_RE);
  const afterNumber = match ? withoutCurrency.slice((match.index ?? 0) + match[0].length) : "";
  const unitMatch = afterNumber.match(/[A-Za-z%/]+(?:\s*[A-Za-z%/]+)*/);
  return { value, unit: unitMatch?.[0]?.trim() ?? "", original };
}

export function toKg(input: unknown): number {
  const quantity = parseQuantity(input);
  if (quantity.value === null) return 0;
  const unit = quantity.unit.toLowerCase();
  if (unit.includes("ton") || unit.includes("tne")) return quantity.value * 1000;
  return quantity.value;
}

export function formatNumber(value: number | null | undefined, fractionDigits = 0): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return "-";
  return new Intl.NumberFormat("id-ID", {
    maximumFractionDigits: fractionDigits,
    minimumFractionDigits: fractionDigits
  }).format(value);
}

export function formatRupiah(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return "-";
  return `Rp${formatNumber(value)}`;
}

