"""
browser_read_funnel — Unified web content extraction for Hermes
Priority funnel: Hermes web_extract → Scrapling → Crawl4AI → screenshot OCR

Usage:
  from browser_read_funnel import read_page, ReadResult
  result = asyncio.run(read_page("https://example.com"))
"""

from __future__ import annotations
import asyncio, json, os, pathlib, re, sys, tempfile, time
from dataclasses import dataclass, field
from typing import Literal, Optional

# ---------------------------------------------------------------------------
# Firecrawl (Hermes web_extract backend)
# ---------------------------------------------------------------------------

def _get_firecrawl_key() -> Optional[str]:
    """Read FIRECRAWL_API_KEY from ~/.hermes/.env"""
    env = pathlib.Path.home() / ".hermes" / ".env"
    if not env.exists():
        return None
    for line in env.read_text().splitlines():
        if line.startswith("FIRECRAWL_API_KEY="):
            return line.split("=", 1)[1].strip()
    return None


async def _read_firecrawl(url: str, timeout: int = 30) -> "ReadResult":
    """Extract via Firecrawl cloud API (Hermes web_extract backend)."""
    key = _get_firecrawl_key()
    if not key:
        return ReadResult(success=False, source="firecrawl", error="FIRECRAWL_API_KEY not set")

    import urllib.request, urllib.error

    body = json.dumps({"url": url, "formats": ["markdown"]}).encode()
    req = urllib.request.Request(
        "https://api.firecrawl.dev/v1/scrape",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read() if e.fp else b""
        try:
            err = json.loads(body).get("error", str(e))
        except Exception:
            err = str(e)
        return ReadResult(success=False, source="firecrawl", error=f"HTTP {e.code}: {err}")
    except Exception as e:
        return ReadResult(success=False, source="firecrawl", error=str(e))

    markdown = data.get("data", {}).get("markdown", "")
    if not markdown:
        # Fallback: maybe response structure is different
        markdown = data.get("markdown", data.get("content", ""))
    return ReadResult(success=True, source="firecrawl", markdown=markdown)


# ---------------------------------------------------------------------------
# Scrapling (stealth dynamic pages, Cloudflare bypass)
# ---------------------------------------------------------------------------

async def _read_scrapling(url: str, timeout: int = 30) -> "ReadResult":
    """Extract via Scrapling — stealth browser, good for Cloudflare & dynamic pages."""
    try:
        from scrapling import StealthyFetcher
    except ImportError:
        return ReadResult(success=False, source="scrapling", error="scrapling not installed")

    try:
        def _fetch():
            resp = StealthyFetcher.fetch(url)
            # Prefer html_content; fall back to body or raw text
            return (
                resp.html_content
                or (resp.body.decode() if hasattr(resp, "body") else "")
                or str(resp)
            )

        # Run sync fetch in thread pool to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        content = await asyncio.wait_for(
            loop.run_in_executor(None, _fetch),
            timeout=timeout,
        )
        if not content or len(content.strip()) < 100:
            return ReadResult(success=False, source="scrapling", error="Empty or too short content")
        return ReadResult(success=True, source="scrapling", markdown=content)
    except asyncio.TimeoutError:
        return ReadResult(success=False, source="scrapling", error=f"Timeout after {timeout}s")
    except Exception as e:
        return ReadResult(success=False, source="scrapling", error=str(e))


# ---------------------------------------------------------------------------
# Crawl4AI (Shadow DOM specialist)
# ---------------------------------------------------------------------------

async def _read_crawl4ai(
    url: str,
    flatten_shadow_dom: bool = True,
    screenshot: bool = True,
    timeout: int = 60,
) -> "ReadResult":
    """Extract via Crawl4AI — best for Shadow DOM, Canvas, nested web components."""
    try:
        from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
    except ImportError:
        return ReadResult(success=False, source="crawl4ai", error="crawl4ai not installed")

    try:
        async def _fetch():
            config = CrawlerRunConfig(
                flatten_shadow_dom=flatten_shadow_dom,
                screenshot=screenshot,
                verbose=False,
            )
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url, config=config)
                return result.markdown if hasattr(result, "markdown") else ""

        content = await asyncio.wait_for(_fetch(), timeout=timeout)
        if not content or len(content.strip()) < 100:
            return ReadResult(success=False, source="crawl4ai", error="Empty or too short content")
        return ReadResult(success=True, source="crawl4ai", markdown=content)
    except asyncio.TimeoutError:
        return ReadResult(success=False, source="crawl4ai", error=f"Timeout after {timeout}s")
    except Exception as e:
        return ReadResult(success=False, source="crawl4ai", error=str(e))


# ---------------------------------------------------------------------------
# Screenshot OCR — final fallback (Canvas, WebGL, exotic content)
# ---------------------------------------------------------------------------

async def _read_screenshot_ocr(url: str, timeout: int = 60) -> "ReadResult":
    """
    Final fallback: navigate to URL in Chrome, take screenshot, OCR with Tesseract.
    Requires Chrome with CDP debugging enabled (port 9222).
    """
    try:
        import websockets
    except ImportError:
        return ReadResult(success=False, source="tesseract", error="websockets not installed")

    # 1. Find or create a Chrome tab for the URL
    try:
        import urllib.request, json as json2

        with urllib.request.urlopen("http://127.0.0.1:9222/json/version", timeout=5) as r:
            _ = json2.loads(r.read())
    except Exception:
        return ReadResult(
            success=False,
            source="tesseract",
            error="Chrome CDP not reachable at port 9222 — is Chrome started with --remote-debugging-port=9222?",
        )

    try:
        # List tabs
        with urllib.request.urlopen("http://127.0.0.1:9222/json/list", timeout=5) as r:
            tabs = json2.loads(r.read())

        tab = None
        for t in tabs:
            if t.get("type") == "page":
                tab = t
                break
            elif t.get("url", "").startswith("about:"):
                tab = t

        if not tab:
            # Create new tab
            req = urllib.request.Request(
                "http://127.0.0.1:9222/json/new", method="POST",
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                tab = json2.loads(r.read())
    except Exception as e:
        return ReadResult(success=False, source="tesseract", error=f"Failed to get/create tab: {e}")

    tab_id = tab["id"]
    ws_url = tab.get("webSocketDebuggerUrl", "")
    if not ws_url:
        return ReadResult(success=False, source="tesseract", error="No WebSocket URL for tab")

    try:
        async with websockets.connect(ws_url, timeout=10) as ws:
            msg_id = 1

            async def send(method: str, params: dict = None, delay: float = 0.5):
                nonlocal msg_id
                await asyncio.sleep(delay)
                await ws.send(json2.dumps({"id": msg_id, "method": method, "params": params or {}}))
                msg_id += 1

            # Navigate
            await send("Page.navigate", {"url": url}, delay=2)
            # Wait for load
            await asyncio.sleep(5)
            # Take screenshot
            await send("Page.takeScreenshot", {"format": "png", "quality": 90}, delay=1)

            # Collect responses
            screenshots = []
            deadline = time.time() + timeout
            while time.time() < deadline:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=5)
                    data = json2.loads(msg)
                    if data.get("id") == msg_id - 1 and data.get("method") == "Page.screencastFrame":
                        # Screencast frame — collect first one
                        pass
                    if "result" in data and "data" in data.get("result", {}):
                        screenshots.append(data["result"]["data"])
                    elif data.get("result", {}).get("data"):
                        screenshots.append(data["result"]["data"])
                except asyncio.TimeoutError:
                    break

    except Exception as e:
        return ReadResult(success=False, source="tesseract", error=f"CDP error: {e}")

    if not screenshots:
        return ReadResult(success=False, source="tesseract", error="No screenshot data received")

    # Save and OCR
    import base64
    tmp = pathlib.Path(tempfile.mktemp(suffix=".png"))
    try:
        tmp.write_bytes(base64.b64decode(screenshots[0]))
    except Exception as e:
        return ReadResult(success=False, source="tesseract", error=f"Failed to decode screenshot: {e}")

    try:
        import subprocess
        result = subprocess.run(
            ["tesseract", str(tmp), "stdout", "-l", "chi_sim+eng", "--psm", "6"],
            capture_output=True, text=True, timeout=30,
        )
        text = result.stdout.strip()
    except FileNotFoundError:
        # Try using Python tesseract wrapper if available
        try:
            import pytesseract
            from PIL import Image
            text = pytesseract.image_to_string(Image.open(tmp), lang="chi_sim+eng")
        except Exception:
            text = ""
    except subprocess.TimeoutExpired:
        return ReadResult(success=False, source="tesseract", error="Tesseract OCR timeout")
    finally:
        tmp.unlink(missing_ok=True)

    if not text:
        return ReadResult(success=False, source="tesseract", error="OCR returned empty text")
    return ReadResult(success=True, source="tesseract", markdown=text)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@dataclass
class ReadResult:
    success: bool
    source: Literal["firecrawl", "scrapling", "crawl4ai", "tesseract", ""]
    markdown: str = ""
    error: str = ""
    url: str = ""

    @property
    def via(self) -> str:
        """Human-readable source label."""
        labels = {
            "firecrawl": "🔥 Firecrawl（云端）",
            "scrapling": "🕷️ Scrapling（反反爬）",
            "crawl4ai": "🤖 Crawl4AI（本地+Shadow DOM）",
            "tesseract": "📷 截图 OCR（降级兜底）",
            "": "—",
        }
        return labels.get(self.source, self.source)


async def read_page(
    url: str,
    prefer: Literal["firecrawl", "scrapling", "crawl4ai", "auto"] = "auto",
    flatten_shadow_dom: bool = True,
    timeout: int = 60,
) -> ReadResult:
    """
    Read a URL via the priority funnel.

    Args:
        url: Target URL.
        prefer: Which tool to try first.
            "auto"   — Firecrawl → Scrapling → Crawl4AI → screenshot OCR
            "firecrawl" — Firecrawl only
            "scrapling" — Scrapling only
            "crawl4ai"  — Crawl4AI only
        flatten_shadow_dom: Passed to Crawl4AI.
        timeout: Per-step timeout in seconds.

    Returns:
        ReadResult with success/markdown/source/error.
    """
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    result: Optional[ReadResult] = None

    if prefer == "firecrawl":
        result = await asyncio.wait_for(_read_firecrawl(url, timeout=timeout), timeout=timeout + 5)
        if result.success:
            result.url = url
            return result

    # In auto mode, always try Firecrawl first (fastest)
    if prefer in ("auto",):
        result = await asyncio.wait_for(_read_firecrawl(url, timeout=timeout), timeout=timeout + 5)
        if result.success:
            result.url = url
            return result

    # Then try Scrapling
    if prefer in ("auto", "scrapling"):
        result = await asyncio.wait_for(_read_scrapling(url, timeout=timeout), timeout=timeout + 5)
        if result.success:
            result.url = url
            return result

    if prefer in ("auto", "crawl4ai"):
        result = await asyncio.wait_for(
            _read_crawl4ai(url, flatten_shadow_dom=flatten_shadow_dom, timeout=timeout),
            timeout=timeout + 10,
        )
        if result.success:
            result.url = url
            return result

    # Final fallback: screenshot OCR
    if prefer == "auto":
        result = await asyncio.wait_for(_read_screenshot_ocr(url, timeout=timeout), timeout=timeout + 30)
        result.url = url
        return result

    # Last resort: return whatever we have
    if result:
        result.url = url
        return result

    return ReadResult(success=False, source="", error="Unknown error", url=url)


# ---------------------------------------------------------------------------
# Sync wrapper for non-async contexts
# ---------------------------------------------------------------------------

def read_page_sync(url: str, **kwargs) -> ReadResult:
    """Synchronous wrapper — use read_page() in async contexts."""
    return asyncio.run(read_page(url, **kwargs))
