from __future__ import annotations

from pathlib import Path
from typing import Any

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from src.browser.downloader import safe_slug, save_text
from src.browser.session import DEFAULT_URL, BrowserSessionManager
from src.parser.csv_parser import parse_csv_file
from src.parser.html_parser import parse_processed_reports, parse_report_detail


class IntraNewNavigator:
    def __init__(
        self,
        session: BrowserSessionManager,
        raw_html_dir: str | Path = "data/raw_html",
        raw_csv_dir: str | Path = "data/raw_csv",
    ) -> None:
        self.session = session
        self.raw_html_dir = Path(raw_html_dir)
        self.raw_csv_dir = Path(raw_csv_dir)

    def open_home(self) -> dict[str, Any]:
        return self.session.open(DEFAULT_URL)

    def fetch_processed_reports(self) -> tuple[list[dict[str, Any]], Path]:
        return self.session.run(self._fetch_processed_reports_on_page, timeout=120)

    def _fetch_processed_reports_on_page(self, page: Page) -> tuple[list[dict[str, Any]], Path]:
        if DEFAULT_URL not in page.url:
            page.goto(DEFAULT_URL, wait_until="domcontentloaded", timeout=60_000)
        self._settle(page)
        html = page.content()
        raw_path = save_text(html, self.raw_html_dir, "laporan_sendiri")
        reports = parse_processed_reports(html, base_url=page.url)
        return reports, raw_path

    def scrape_detail(self, report: dict[str, Any]) -> dict[str, Any]:
        return self.session.run(lambda page: self._scrape_detail_on_page(page, report), timeout=300)

    def _scrape_detail_on_page(self, page: Page, report: dict[str, Any]) -> dict[str, Any]:
        detail_url = report.get("detail_url") or ""
        company_name = report.get("company_name") or "perusahaan"
        if detail_url:
            page.goto(detail_url, wait_until="domcontentloaded", timeout=60_000)
        else:
            page.goto(DEFAULT_URL, wait_until="domcontentloaded", timeout=60_000)
            self._settle(page)
            page.get_by_text(company_name, exact=False).first.click(timeout=15_000)
        self._settle(page)
        self.click_all_buka(page)
        self.scroll_to_bottom(page)
        csv_paths = self.download_csv_links(page, company_name)
        csv_sections: dict[str, list[dict[str, Any]]] = {}
        for path in csv_paths:
            try:
                section_name = Path(path).stem.replace("_", " ")
                from src.parser.section_mapper import canonical_section

                csv_sections.setdefault(canonical_section(section_name), []).extend(parse_csv_file(path))
            except Exception:
                continue

        html = page.content()
        raw_html_path = save_text(html, self.raw_html_dir, company_name)
        parsed = parse_report_detail(html, base_url=page.url, csv_sections=csv_sections)
        merged = {
            **report,
            "scraping_status": "detail_scraped",
            "raw_html_path": str(raw_html_path),
            "raw_csv_paths": [str(path) for path in csv_paths],
            "identity": parsed.get("identity", {}),
            "general": {**(report.get("general") or {}), **parsed.get("general", {})},
            "sections": parsed.get("sections", {}),
            "links": parsed.get("links", []),
            "parser_warnings": parsed.get("parser_warnings", []),
        }
        return merged

    def click_all_buka(self, page: Page) -> int:
        clicked = 0
        for _ in range(8):
            locators = [
                page.get_by_role("button", name="Buka"),
                page.get_by_text("Buka", exact=True),
                page.locator("a:has-text('Buka')"),
            ]
            made_progress = False
            for locator in locators:
                try:
                    count = min(locator.count(), 50)
                except Exception:
                    count = 0
                for index in range(count):
                    item = locator.nth(index)
                    try:
                        if item.is_visible(timeout=1_000):
                            item.click(timeout=3_000)
                            clicked += 1
                            made_progress = True
                            page.wait_for_timeout(300)
                    except Exception:
                        continue
            if not made_progress:
                break
        self._settle(page)
        return clicked

    def scroll_to_bottom(self, page: Page) -> None:
        previous_height = 0
        for _ in range(20):
            height = page.evaluate("document.body.scrollHeight")
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(500)
            if height == previous_height:
                break
            previous_height = height
        page.evaluate("window.scrollTo(0, 0)")

    def download_csv_links(self, page: Page, company_name: str) -> list[Path]:
        paths: list[Path] = []
        locator = page.locator("a:has-text('Download CSV'), button:has-text('Download CSV'), a[href*='.csv'], a[href*='csv']")
        try:
            count = min(locator.count(), 50)
        except Exception:
            count = 0

        for index in range(count):
            item = locator.nth(index)
            try:
                if not item.is_visible(timeout=1_000):
                    continue
                label = item.inner_text(timeout=1_000) or f"csv_{index + 1}"
                with page.expect_download(timeout=10_000) as download_info:
                    item.click(timeout=5_000)
                download = download_info.value
                suggested = download.suggested_filename or f"{safe_slug(company_name)}_{index + 1}.csv"
                target = self.raw_csv_dir / f"{safe_slug(company_name)}_{safe_slug(label)}_{safe_slug(suggested)}"
                target.parent.mkdir(parents=True, exist_ok=True)
                download.save_as(str(target))
                paths.append(target)
            except PlaywrightTimeoutError:
                continue
            except Exception:
                continue
        return paths

    def _settle(self, page: Page) -> None:
        try:
            page.wait_for_load_state("networkidle", timeout=15_000)
        except PlaywrightTimeoutError:
            try:
                page.wait_for_load_state("domcontentloaded", timeout=10_000)
            except PlaywrightTimeoutError:
                pass
