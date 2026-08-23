# Zero-OCR page-text extraction via local Chrome CDP

Goal: read a webpage's rendered text WITHOUT screenshots or OCR.

## Why local Chrome (not cloud tools)
- `web_extract` / `browser_navigate` false-trip on `#:~:text=` text-fragment URLs
  (report `Blocked: URL targets a private or internal network address`) and the
  block CASCADES to all URL-tool calls that session — even `example.com` and the
  tool's own docs domain.
- Datacenter egress IPs get anti-scraped: `curl https://zhuanlan.zhihu.com/...`
  -> `HTTP 403`; Jina Reader / cloud extractors fail on the user's egress IP.
- Local Chrome CDP carries the user's real IP + login cookies -> reads fine.

## Verified recipe (synchronous websocket-client)
Mirrors `scripts/read_page_text.py`. Do NOT use asyncio (see pitfalls in SKILL.md).
1. browser WS: `Target.createTarget` `{"url": <url>}` -> `targetId`.
2. `time.sleep(6)` (SPA/JS render; Zhihu needs it).
3. page WS from `/json` (`t["id"]==targetId` -> `webSocketDebuggerUrl`), `Runtime.enable`.
4. `Runtime.evaluate({"expression":"document.body.innerText","returnByValue":true})`
   -> `result.result.value`.

## Failure modes observed this session
- asyncio `wait_for` wrapper -> `CancelledError` -> dead context -> `Runtime.evaluate`
  returns `None`. Fix: fresh tab + sync pattern (verify_cdp.py style).
- Reading a tab whose WS was opened before navigation -> `innerText` empty / `None`.
  Fix: open the WS AFTER createTarget + sleep, or re-open on a new tab.
- `document.body.innerText` empty but `document.title` correct -> SPA shadow/iframe
  content not yet in body; wait longer / re-read. (Worked at ~6s for Zhihu.)
- `Runtime.evaluate` returns `None` (not `""`) => stale/detached tab, not empty page.

## Real result
Zhihu article '【第三版】如何在苹果电脑macOS下微信多开/双开？'
(p/1976589723620364615) read as 3964 chars of clean text, including the C1/C3/C6
微信多开 steps the user wanted — with no OCR, no screenshot, pure DOM text.
