from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from src.parser.section_mapper import canonical_section, merge_section_records


HEADING_SELECTORS = ["h1", "h2", "h3", "h4", "h5", "legend", ".card-title", ".panel-title", ".box-title"]


def _clean(text: Any) -> str:
    return " ".join(str(text or "").replace("\xa0", " ").split())


def _unique_headers(headers: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    result: list[str] = []
    for index, header in enumerate(headers, start=1):
        clean = _clean(header) or f"kolom_{index}"
        count = seen.get(clean, 0)
        seen[clean] = count + 1
        result.append(clean if count == 0 else f"{clean}_{count + 1}")
    return result


def table_to_records(table: Tag) -> list[dict[str, str]]:
    rows = table.find_all("tr")
    if not rows:
        return []

    header_cells = rows[0].find_all(["th", "td"])
    th_cells = rows[0].find_all("th")
    headers = [_clean(cell.get_text(" ")) for cell in (th_cells or header_cells)]
    headers = _unique_headers(headers)
    data_rows = rows[1:] if header_cells else rows
    records: list[dict[str, str]] = []

    for row in data_rows:
        cells = row.find_all(["td", "th"])
        if not cells:
            continue
        values = [_clean(cell.get_text(" ")) for cell in cells]
        if len(values) > len(headers):
            headers = _unique_headers(headers + [f"kolom_{i}" for i in range(len(headers) + 1, len(values) + 1)])
        record = {headers[index]: values[index] if index < len(values) else "" for index in range(len(headers))}
        if any(value for value in record.values()):
            records.append(record)
    return records


def _nearest_heading(table: Tag) -> str:
    current = table
    while current:
        previous = current.find_previous(HEADING_SELECTORS)
        if previous:
            return _clean(previous.get_text(" "))
        current = current.parent if isinstance(current.parent, Tag) else None
    return "unknown"


def _table_links(table: Tag, base_url: str = "") -> list[str]:
    links: list[str] = []
    for anchor in table.find_all("a", href=True):
        href = anchor.get("href", "")
        if href:
            links.append(urljoin(base_url, href))
    return links


def extract_key_values(soup: BeautifulSoup) -> dict[str, str]:
    values: dict[str, str] = {}
    for table in soup.find_all("table"):
        records = table_to_records(table)
        for record in records:
            items = list(record.items())
            if len(items) == 2:
                key, value = items[0][1], items[1][1]
                if key and value and len(key) < 80:
                    values.setdefault(key, value)

    for definition_list in soup.find_all("dl"):
        terms = definition_list.find_all("dt")
        defs = definition_list.find_all("dd")
        for term, definition in zip(terms, defs):
            key = _clean(term.get_text(" "))
            value = _clean(definition.get_text(" "))
            if key and value:
                values.setdefault(key, value)
    return values


def parse_processed_reports(html: str, base_url: str = "") -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "lxml")
    candidate_tables: list[Tag] = []
    for table in soup.find_all("table"):
        header_text = _clean(" ".join(cell.get_text(" ") for cell in table.find_all(["th", "td"], limit=12))).lower()
        if any(token in header_text for token in ["perusahaan", "periode", "tanggal kirim", "status"]):
            candidate_tables.append(table)

    reports: list[dict[str, Any]] = []
    for table in candidate_tables[:2]:
        rows = table.find_all("tr")
        if not rows:
            continue
        headers = [_clean(cell.get_text(" ")) for cell in rows[0].find_all(["th", "td"])]
        if not headers:
            continue
        headers = _unique_headers(headers)
        for row in rows[1:]:
            cells = row.find_all(["td", "th"])
            if not cells:
                continue
            values = [_clean(cell.get_text(" ")) for cell in cells]
            record = {headers[index]: values[index] if index < len(values) else "" for index in range(len(headers))}
            link = ""
            first_anchor = row.find("a", href=True)
            if first_anchor:
                link = urljoin(base_url, first_anchor["href"])
            normalized = {key.lower(): value for key, value in record.items()}
            reports.append(
                {
                    "company_name": _pick(normalized, ["nama perusahaan", "perusahaan", "nama"]),
                    "period": _pick(normalized, ["periode", "triwulan"]),
                    "submitted_at": _pick(normalized, ["tanggal kirim", "tgl kirim", "tanggal"]),
                    "status": _pick(normalized, ["status"]),
                    "verifier": _pick(normalized, ["verifikator"]),
                    "validator": _pick(normalized, ["validator"]),
                    "detail_url": link,
                    "scraping_status": "listed",
                    "raw_row": record,
                }
            )
    return [report for report in reports if report.get("company_name")]


def _pick(record: dict[str, Any], candidates: list[str]) -> str:
    for key, value in record.items():
        key_lower = key.lower()
        if any(candidate in key_lower for candidate in candidates):
            return str(value)
    return ""


def parse_report_detail(html: str, base_url: str = "", csv_sections: dict[str, list[dict[str, Any]]] | None = None) -> dict[str, Any]:
    soup = BeautifulSoup(html, "lxml")
    key_values = extract_key_values(soup)
    sections: dict[str, list[dict[str, Any]]] = {}
    warnings: list[str] = []

    for table in soup.find_all("table"):
        heading = _nearest_heading(table)
        canonical = canonical_section(heading)
        rows = table_to_records(table)
        if canonical == "unknown":
            warnings.append("Ada tabel yang tidak dapat dipetakan ke section. Raw HTML tetap disimpan.")
        merge_section_records(sections, canonical, rows)

    if csv_sections:
        for section, rows in csv_sections.items():
            if rows:
                sections[section] = rows

    links = []
    csv_links = []
    statement_links = []
    for anchor in soup.find_all("a", href=True):
        text = _clean(anchor.get_text(" "))
        href = urljoin(base_url, anchor["href"])
        links.append({"text": text, "href": href})
        lower = f"{text} {href}".lower()
        if "csv" in lower:
            csv_links.append(href)
        if "surat" in lower or "pernyataan" in lower:
            statement_links.append(href)

    identity = {key: value for key, value in key_values.items() if canonical_section(key) == "identitas"}
    general = {key: value for key, value in key_values.items() if canonical_section(key) == "umum"}
    if statement_links:
        general["link_surat_pernyataan"] = statement_links[0]

    if not sections:
        warnings.append("Tidak ada tabel detail yang berhasil diparse. Kemungkinan struktur website berubah atau semua data lazy-loaded.")

    return {
        "identity": identity,
        "general": general,
        "sections": sections,
        "links": links,
        "csv_links": csv_links,
        "statement_links": statement_links,
        "parser_warnings": warnings,
    }


def parse_report_detail_file(path: str | Path, base_url: str = "") -> dict[str, Any]:
    return parse_report_detail(Path(path).read_text(encoding="utf-8", errors="replace"), base_url=base_url)

