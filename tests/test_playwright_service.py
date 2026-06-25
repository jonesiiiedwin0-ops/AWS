"""Tests for the native Playwright browser-automation service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from aws_mcp_server.services.playwright_service import (
    PlaywrightError,
    PlaywrightService,
)


@pytest.fixture
def service():
    return PlaywrightService()


def test_service_metadata(service):
    meta = service.metadata()
    assert meta["service"] == "playwright"
    assert meta["name"] == "Playwright"
    assert "navigate" in meta["tools"]
    assert "screenshot" in meta["tools"]


def test_list_tools(service):
    tools = service.list_tools()
    expected = {
        "navigate",
        "screenshot",
        "click",
        "fill",
        "get_text",
        "get_html",
        "wait_for_selector",
        "evaluate",
        "select_option",
        "hover",
    }
    assert expected.issubset(set(tools))


@pytest.mark.asyncio
async def test_execute_unknown_tool(service):
    with pytest.raises(PlaywrightError, match="Unknown Playwright tool"):
        await service.execute("nonexistent_tool", {})


@pytest.mark.asyncio
async def test_navigate_missing_url(service):
    with pytest.raises(PlaywrightError, match="'url' parameter is required"):
        await service.execute("navigate", {})


@pytest.mark.asyncio
async def test_navigate_success(service):
    mock_response = MagicMock(status=200)
    mock_page = AsyncMock()
    mock_page.goto = AsyncMock(return_value=mock_response)
    mock_page.title = AsyncMock(return_value="Test Page")
    mock_page.url = "https://example.com"
    mock_page.close = AsyncMock()

    with patch.object(service, "_new_page", return_value=mock_page):
        result = await service.execute("navigate", {"url": "https://example.com"})

    assert result["title"] == "Test Page"
    assert result["status"] == 200
    assert result["url"] == "https://example.com"


@pytest.mark.asyncio
async def test_screenshot_missing_url(service):
    with pytest.raises(PlaywrightError, match="'url' parameter is required"):
        await service.execute("screenshot", {})


@pytest.mark.asyncio
async def test_screenshot_success(service):
    mock_page = AsyncMock()
    mock_page.goto = AsyncMock(return_value=None)
    mock_page.screenshot = AsyncMock(return_value=b"\x89PNG\r\n")
    mock_page.url = "https://example.com"
    mock_page.close = AsyncMock()

    with patch.object(service, "_new_page", return_value=mock_page):
        result = await service.execute("screenshot", {"url": "https://example.com"})

    assert result["format"] == "png"
    assert result["data"]  # base64 non-empty


@pytest.mark.asyncio
async def test_get_text_success(service):
    mock_page = AsyncMock()
    mock_page.goto = AsyncMock(return_value=None)
    mock_page.inner_text = AsyncMock(return_value="Hello World")
    mock_page.url = "https://example.com"
    mock_page.close = AsyncMock()

    with patch.object(service, "_new_page", return_value=mock_page):
        result = await service.execute(
            "get_text", {"url": "https://example.com", "selector": "h1"}
        )

    assert result["text"] == "Hello World"
    assert result["selector"] == "h1"


@pytest.mark.asyncio
async def test_evaluate_success(service):
    mock_page = AsyncMock()
    mock_page.goto = AsyncMock(return_value=None)
    mock_page.evaluate = AsyncMock(return_value=42)
    mock_page.url = "https://example.com"
    mock_page.close = AsyncMock()

    with patch.object(service, "_new_page", return_value=mock_page):
        result = await service.execute(
            "evaluate", {"url": "https://example.com", "expression": "1 + 41"}
        )

    assert result["result"] == 42


@pytest.mark.asyncio
async def test_click_missing_params(service):
    with pytest.raises(PlaywrightError, match="'url' and 'selector' are required"):
        await service.execute("click", {"url": "https://example.com"})


@pytest.mark.asyncio
async def test_fill_missing_params(service):
    with pytest.raises(
        PlaywrightError, match="'url', 'selector', and 'value' are required"
    ):
        await service.execute("fill", {"url": "https://example.com", "selector": "#q"})
