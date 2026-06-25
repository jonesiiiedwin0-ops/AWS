"""Native Playwright browser-automation service for the AWS MCP Server."""

import asyncio
import base64
import logging
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class PlaywrightError(Exception):
    """Raised when a Playwright operation fails."""

    def __init__(self, message: str, code: str = "PlaywrightError"):
        super().__init__(message)
        self.code = code


class PlaywrightService:
    """Browser-automation service backed by Playwright.

    Exposes a subset of Playwright's page API as named tools that match the
    ``<service>_<operation>`` convention used by the rest of the MCP server.

    The service manages a single shared browser instance (Chromium) and a
    pool of pages so callers do not pay browser-launch overhead per request.
    """

    service_name: str = "playwright"
    display_name: str = "Playwright"
    description: str = (
        "Native browser automation via Playwright — navigate pages, "
        "interact with elements, capture screenshots, and run JavaScript."
    )

    def __init__(self) -> None:
        self._browser: Optional[Any] = None
        self._playwright: Optional[Any] = None
        self._lock = asyncio.Lock()
        self._tools: Dict[str, Callable] = self._build_tools()

    # ------------------------------------------------------------------
    # Browser lifecycle
    # ------------------------------------------------------------------

    async def _ensure_browser(self) -> Any:
        """Lazily launch the browser on first use."""
        if self._browser is not None:
            return self._browser

        async with self._lock:
            if self._browser is not None:
                return self._browser

            from playwright.async_api import async_playwright  # type: ignore[import]

            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=True)
            logger.info("Playwright Chromium browser launched")

        return self._browser

    async def _new_page(self) -> Any:
        """Create a fresh browser page."""
        browser = await self._ensure_browser()
        return await browser.new_page()

    async def close(self) -> None:
        """Shut down the browser gracefully."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        logger.info("Playwright browser closed")

    # ------------------------------------------------------------------
    # Tool implementations
    # ------------------------------------------------------------------

    def _build_tools(self) -> Dict[str, Callable]:
        return {
            "navigate": self._navigate,
            "screenshot": self._screenshot,
            "click": self._click,
            "fill": self._fill,
            "get_text": self._get_text,
            "get_html": self._get_html,
            "wait_for_selector": self._wait_for_selector,
            "evaluate": self._evaluate,
            "select_option": self._select_option,
            "hover": self._hover,
        }

    async def _navigate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Navigate to a URL and return page title and final URL."""
        url: str = params.get("url", "")
        if not url:
            raise PlaywrightError("'url' parameter is required", code="MissingParam")

        timeout: int = int(params.get("timeout_ms", 30_000))
        wait_until: str = params.get("wait_until", "load")

        page = await self._new_page()
        try:
            response = await page.goto(url, timeout=timeout, wait_until=wait_until)
            title = await page.title()
            return {
                "url": page.url,
                "title": title,
                "status": response.status if response else None,
            }
        finally:
            await page.close()

    async def _screenshot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Navigate to a URL and return a base64-encoded PNG screenshot."""
        url: str = params.get("url", "")
        if not url:
            raise PlaywrightError("'url' parameter is required", code="MissingParam")

        timeout: int = int(params.get("timeout_ms", 30_000))
        full_page: bool = bool(params.get("full_page", False))
        selector: Optional[str] = params.get("selector")

        page = await self._new_page()
        try:
            await page.goto(url, timeout=timeout, wait_until="load")
            if selector:
                element = await page.query_selector(selector)
                if element is None:
                    raise PlaywrightError(
                        f"Selector '{selector}' not found", code="SelectorNotFound"
                    )
                png = await element.screenshot()
            else:
                png = await page.screenshot(full_page=full_page)

            return {
                "url": page.url,
                "format": "png",
                "data": base64.b64encode(png).decode(),
            }
        finally:
            await page.close()

    async def _click(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Navigate to a URL, click a selector, and return the resulting URL."""
        url: str = params.get("url", "")
        selector: str = params.get("selector", "")
        if not url or not selector:
            raise PlaywrightError(
                "'url' and 'selector' are required", code="MissingParam"
            )

        timeout: int = int(params.get("timeout_ms", 30_000))
        page = await self._new_page()
        try:
            await page.goto(url, timeout=timeout, wait_until="load")
            await page.click(selector, timeout=timeout)
            return {"url": page.url, "clicked": selector}
        finally:
            await page.close()

    async def _fill(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Navigate to a URL and fill a form field."""
        url: str = params.get("url", "")
        selector: str = params.get("selector", "")
        value: str = params.get("value", "")
        if not url or not selector or "value" not in params:
            raise PlaywrightError(
                "'url', 'selector', and 'value' are required", code="MissingParam"
            )

        timeout: int = int(params.get("timeout_ms", 30_000))
        page = await self._new_page()
        try:
            await page.goto(url, timeout=timeout, wait_until="load")
            await page.fill(selector, value, timeout=timeout)
            return {"url": page.url, "selector": selector, "filled": True}
        finally:
            await page.close()

    async def _get_text(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Return the inner text of a selector on the given page."""
        url: str = params.get("url", "")
        selector: str = params.get("selector", "body")
        if not url:
            raise PlaywrightError("'url' parameter is required", code="MissingParam")

        timeout: int = int(params.get("timeout_ms", 30_000))
        page = await self._new_page()
        try:
            await page.goto(url, timeout=timeout, wait_until="load")
            text = await page.inner_text(selector, timeout=timeout)
            return {"url": page.url, "selector": selector, "text": text}
        finally:
            await page.close()

    async def _get_html(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Return the outer HTML of a selector (or full page) on the given URL."""
        url: str = params.get("url", "")
        selector: str = params.get("selector", "html")
        if not url:
            raise PlaywrightError("'url' parameter is required", code="MissingParam")

        timeout: int = int(params.get("timeout_ms", 30_000))
        page = await self._new_page()
        try:
            await page.goto(url, timeout=timeout, wait_until="load")
            html = await page.inner_html(selector, timeout=timeout)
            return {"url": page.url, "selector": selector, "html": html}
        finally:
            await page.close()

    async def _wait_for_selector(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Navigate to a URL and wait until a selector is visible."""
        url: str = params.get("url", "")
        selector: str = params.get("selector", "")
        if not url or not selector:
            raise PlaywrightError(
                "'url' and 'selector' are required", code="MissingParam"
            )

        timeout: int = int(params.get("timeout_ms", 30_000))
        state: str = params.get("state", "visible")
        page = await self._new_page()
        try:
            await page.goto(url, timeout=timeout, wait_until="load")
            await page.wait_for_selector(selector, state=state, timeout=timeout)
            return {"url": page.url, "selector": selector, "state": state, "found": True}
        finally:
            await page.close()

    async def _evaluate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Navigate to a URL and evaluate a JavaScript expression."""
        url: str = params.get("url", "")
        expression: str = params.get("expression", "")
        if not url or not expression:
            raise PlaywrightError(
                "'url' and 'expression' are required", code="MissingParam"
            )

        timeout: int = int(params.get("timeout_ms", 30_000))
        page = await self._new_page()
        try:
            await page.goto(url, timeout=timeout, wait_until="load")
            result = await page.evaluate(expression)
            return {"url": page.url, "expression": expression, "result": result}
        finally:
            await page.close()

    async def _select_option(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Navigate to a URL and select a <select> option by value or label."""
        url: str = params.get("url", "")
        selector: str = params.get("selector", "")
        value: str = params.get("value", "")
        if not url or not selector or not value:
            raise PlaywrightError(
                "'url', 'selector', and 'value' are required", code="MissingParam"
            )

        timeout: int = int(params.get("timeout_ms", 30_000))
        page = await self._new_page()
        try:
            await page.goto(url, timeout=timeout, wait_until="load")
            selected = await page.select_option(selector, value, timeout=timeout)
            return {"url": page.url, "selector": selector, "selected": selected}
        finally:
            await page.close()

    async def _hover(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Navigate to a URL and hover over a selector."""
        url: str = params.get("url", "")
        selector: str = params.get("selector", "")
        if not url or not selector:
            raise PlaywrightError(
                "'url' and 'selector' are required", code="MissingParam"
            )

        timeout: int = int(params.get("timeout_ms", 30_000))
        page = await self._new_page()
        try:
            await page.goto(url, timeout=timeout, wait_until="load")
            await page.hover(selector, timeout=timeout)
            return {"url": page.url, "selector": selector, "hovered": True}
        finally:
            await page.close()

    # ------------------------------------------------------------------
    # Registry-compatible interface
    # ------------------------------------------------------------------

    def list_tools(self) -> List[str]:
        return list(self._tools.keys())

    async def execute(self, tool: str, params: Dict[str, Any]) -> Any:
        handler = self._tools.get(tool)
        if handler is None:
            raise PlaywrightError(
                f"Unknown Playwright tool '{tool}'", code="UnknownTool"
            )
        try:
            return await handler(params)
        except PlaywrightError:
            raise
        except Exception as exc:
            logger.error("playwright.%s failed: %s", tool, exc)
            raise PlaywrightError(str(exc), code="PlaywrightError") from exc

    def metadata(self) -> Dict[str, Any]:
        return {
            "name": self.display_name,
            "service": self.service_name,
            "description": self.description,
            "tools": self.list_tools(),
        }
