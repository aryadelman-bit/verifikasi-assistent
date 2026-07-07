"use client";

type TextItem = {
  str: string;
  transform: number[];
};

export async function extractPdfText(file: File): Promise<string> {
  const pdfjs = await import("pdfjs-dist/legacy/build/pdf.mjs");
  pdfjs.GlobalWorkerOptions.workerSrc = new URL("pdfjs-dist/legacy/build/pdf.worker.mjs", import.meta.url).toString();
  const data = new Uint8Array(await file.arrayBuffer());
  const document = await pdfjs.getDocument({ data }).promise;
  const pages: string[] = [];

  for (let pageNumber = 1; pageNumber <= document.numPages; pageNumber += 1) {
    const page = await document.getPage(pageNumber);
    const content = await page.getTextContent();
    const items = (content.items as unknown[])
      .filter((item): item is TextItem => {
        const candidate = item as Partial<TextItem>;
        return typeof candidate.str === "string" && Array.isArray(candidate.transform) && Boolean(candidate.str.trim());
      })
      .map((item) => ({
        text: item.str.trim(),
        x: item.transform[4] ?? 0,
        y: item.transform[5] ?? 0
      }));

    const lineMap = new Map<number, { y: number; items: typeof items }>();
    for (const item of items) {
      const key = Math.round(item.y / 3) * 3;
      const existing = lineMap.get(key);
      if (existing) existing.items.push(item);
      else lineMap.set(key, { y: item.y, items: [item] });
    }

    const lines = [...lineMap.values()]
      .sort((a, b) => b.y - a.y)
      .map((line) =>
        line.items
          .sort((a, b) => a.x - b.x)
          .map((item) => item.text)
          .join(" ")
          .replace(/\s+/g, " ")
          .trim()
      )
      .filter(Boolean);

    pages.push(`--- PAGE ${pageNumber} ---\n${lines.join("\n")}`);
  }

  return pages.join("\n\n");
}
