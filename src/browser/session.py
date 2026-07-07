from __future__ import annotations

import asyncio
import queue
import sys
import threading
import traceback
import warnings
from pathlib import Path
from typing import Any, Callable, TypeVar

from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright


DEFAULT_URL = "https://intranew.kemenperin.go.id/siinas/laporan/laporan_sendiri.php"
T = TypeVar("T")


def ensure_windows_playwright_event_loop() -> None:
    """Use an asyncio policy that supports subprocesses on Windows."""

    if sys.platform != "win32":
        return
    proactor_policy = getattr(asyncio, "WindowsProactorEventLoopPolicy", None)
    if proactor_policy is None:
        return
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        current_policy = asyncio.get_event_loop_policy()
        if not isinstance(current_policy, proactor_policy):
            asyncio.set_event_loop_policy(proactor_policy())


class BrowserSessionError(RuntimeError):
    """Raised when a browser operation fails inside the Playwright worker."""


class _BrowserSessionCore:
    """Actual Playwright objects. This class must only be used on one thread."""

    def __init__(
        self,
        mode: str = "persistent",
        user_data_dir: str | Path = "browser_profiles/intranew",
        cdp_endpoint: str = "http://127.0.0.1:9222",
        headless: bool = False,
    ) -> None:
        self.mode = mode
        self.user_data_dir = Path(user_data_dir)
        self.cdp_endpoint = cdp_endpoint
        self.headless = headless
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    @property
    def connected(self) -> bool:
        return self._context is not None

    def start(self) -> Page:
        if self._page and not self._page.is_closed():
            return self._page
        ensure_windows_playwright_event_loop()
        self._playwright = sync_playwright().start()
        chromium = self._playwright.chromium
        if self.mode == "cdp":
            self._browser = chromium.connect_over_cdp(self.cdp_endpoint)
            self._context = self._browser.contexts[0] if self._browser.contexts else self._browser.new_context(accept_downloads=True)
            self._page = self._context.pages[0] if self._context.pages else self._context.new_page()
        else:
            self.user_data_dir.mkdir(parents=True, exist_ok=True)
            self._context = chromium.launch_persistent_context(
                user_data_dir=str(self.user_data_dir),
                headless=self.headless,
                accept_downloads=True,
                viewport={"width": 1440, "height": 1000},
            )
            self._page = self._context.pages[0] if self._context.pages else self._context.new_page()
        return self._page

    def open(self, url: str = DEFAULT_URL) -> Page:
        page = self.start()
        page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        return page

    def page(self) -> Page:
        if not self._page or self._page.is_closed():
            return self.start()
        return self._page

    def refresh(self) -> None:
        if self._page and not self._page.is_closed():
            self._page.reload(wait_until="domcontentloaded", timeout=60_000)

    def close(self) -> None:
        if self.mode == "cdp" and self._browser:
            self._browser.close()
        elif self._context:
            self._context.close()
        elif self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
        self._browser = None
        self._context = None
        self._page = None
        self._playwright = None

    def status(self) -> dict[str, Any]:
        url = ""
        try:
            url = self._page.url if self._page and not self._page.is_closed() else ""
        except Exception:
            url = ""
        return {
            "connected": self.connected,
            "mode": self.mode,
            "user_data_dir": str(self.user_data_dir),
            "cdp_endpoint": self.cdp_endpoint,
            "current_url": url,
        }


class _PlaywrightWorker:
    def __init__(
        self,
        mode: str,
        user_data_dir: str | Path,
        cdp_endpoint: str,
        headless: bool,
    ) -> None:
        self.mode = mode
        self.user_data_dir = Path(user_data_dir)
        self.cdp_endpoint = cdp_endpoint
        self.headless = headless
        self._tasks: queue.Queue[tuple[Callable[[_BrowserSessionCore], Any] | None, threading.Event, dict[str, Any]]] = queue.Queue()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._started = False

    @property
    def started(self) -> bool:
        return self._started and self._thread is not None and self._thread.is_alive()

    def _ensure_thread(self) -> None:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._thread = threading.Thread(target=self._run, name="intranew-playwright-worker", daemon=True)
            self._thread.start()
            self._started = True

    def _run(self) -> None:
        core = _BrowserSessionCore(
            mode=self.mode,
            user_data_dir=self.user_data_dir,
            cdp_endpoint=self.cdp_endpoint,
            headless=self.headless,
        )
        while True:
            func, done, box = self._tasks.get()
            if func is None:
                try:
                    core.close()
                finally:
                    box["result"] = None
                    done.set()
                return
            try:
                box["result"] = func(core)
            except Exception as exc:
                box["error"] = exc
                box["traceback"] = traceback.format_exc()
            finally:
                done.set()

    def call(self, func: Callable[[_BrowserSessionCore], T], timeout: float | None = None) -> T:
        self._ensure_thread()
        done = threading.Event()
        box: dict[str, Any] = {}
        self._tasks.put((func, done, box))
        if not done.wait(timeout):
            raise BrowserSessionError("Operasi browser terlalu lama dan belum selesai.")
        if "error" in box:
            exc = box["error"]
            message = str(exc) or exc.__class__.__name__
            raise BrowserSessionError(message) from exc
        return box.get("result")

    def stop(self) -> None:
        if not self.started:
            return
        done = threading.Event()
        box: dict[str, Any] = {}
        self._tasks.put((None, done, box))
        done.wait(10)


class BrowserSessionManager:
    """Thread-safe Playwright session manager for Streamlit reruns.

    Streamlit reruns the app script in changing threads. Playwright's sync API
    uses greenlets that cannot be moved across threads, so all Playwright work
    is executed in this manager's dedicated worker thread.
    """

    def __init__(
        self,
        mode: str = "persistent",
        user_data_dir: str | Path = "browser_profiles/intranew",
        cdp_endpoint: str = "http://127.0.0.1:9222",
        headless: bool = False,
    ) -> None:
        self.mode = mode
        self.user_data_dir = Path(user_data_dir)
        self.cdp_endpoint = cdp_endpoint
        self.headless = headless
        self._worker = _PlaywrightWorker(mode, self.user_data_dir, cdp_endpoint, headless)

    @property
    def connected(self) -> bool:
        if not self._worker.started:
            return False
        try:
            return bool(self.status().get("connected"))
        except BrowserSessionError:
            return False

    def open(self, url: str = DEFAULT_URL) -> dict[str, Any]:
        return self._worker.call(lambda core: (core.open(url), core.status())[1])

    def refresh(self) -> dict[str, Any]:
        return self._worker.call(lambda core: (core.refresh(), core.status())[1])

    def status(self) -> dict[str, Any]:
        if not self._worker.started:
            return {
                "connected": False,
                "mode": self.mode,
                "user_data_dir": str(self.user_data_dir),
                "cdp_endpoint": self.cdp_endpoint,
                "current_url": "",
            }
        return self._worker.call(lambda core: core.status())

    def run(self, func: Callable[[Page], T], timeout: float | None = None) -> T:
        return self._worker.call(lambda core: func(core.page()), timeout=timeout)

    def close(self) -> None:
        self._worker.stop()
