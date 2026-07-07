import { parseIndonesianNumber } from "./number";
import type { PriceLimit, PriceLimitMap } from "./types";

const PERIODS = ["3 2024", "4 2024", "1 2025"];

export function parsePriceLimits(text: string): PriceLimitMap {
  const limits: PriceLimitMap = {};
  const lines = text
    .replace(/\u00a0/g, " ")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);

  for (const line of lines) {
    const match = line.match(/^(\d{5})\s+(.+?)\s+((?:\d[\d.]*|0)(?:\s+(?:\d[\d.]*|0)){5})$/);
    if (!match) continue;
    const [, kbli, description, numericTail] = match;
    const numbers = numericTail.split(/\s+/).map((value) => parseIndonesianNumber(value) ?? 0);
    if (numbers.length < 6) continue;
    let selected: PriceLimit | null = null;
    for (let pair = 2; pair >= 0; pair -= 1) {
      const lower = numbers[pair * 2];
      const upper = numbers[pair * 2 + 1];
      if (lower > 0 || upper > 0) {
        selected = {
          kbli,
          description: description.trim(),
          lower,
          upper,
          sourcePeriod: PERIODS[pair]
        };
        break;
      }
    }
    if (selected) limits[kbli] = selected;
  }

  return limits;
}

export function getPriceLimitForKbli(limits: PriceLimitMap, kbli: string): PriceLimit | null {
  return limits[kbli] ?? null;
}

