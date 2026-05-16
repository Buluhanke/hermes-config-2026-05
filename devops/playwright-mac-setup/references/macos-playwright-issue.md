# Playwright macOS Download Timeout Issue (Session 2025-05-03)

## Context
During a session on macOS (Mac-Pro.local, Darwin 25.4.0), the command `playwright install chromium` repeatedly timed out after 30 seconds while downloading the Chrome Headless Shell (~96.6 MiB). The default timeout in Playwright's network utility is 30 s, which is insufficient for slower connections.

## Symptoms
- Error: `Request to https://storage.googleapis.com/chrome-for-testing-public/... timed out after 30000ms`
- The process exits with code 124 (timeout) when run with a default `timeout` parameter.
- Running with `timeout=600` still triggered the internal 30‑s timeout.

## Workaround Used
1. **Background Process**: Launched `playwright install chromium` as a background process with `timeout=900` (15 min) to allow the download to complete without blocking the terminal.
2. **Using `playwright install chromium`** (specific browser) instead of `playwright install` (all browsers) to reduce download size.

## Root Cause
Playwright’s internal download client enforces a 30‑second timeout per HTTP request, independent of the outer `timeout` parameter of the terminal tool. For large files or slow networks, this is too short.

## Recommendations
- Pre‑download the browser binaries using a more tolerant downloader (e.g., `curl` with `--max-time 0`) and place them in `~/.cache/ms-playwright/`.
- If the environment allows, set `PLAYWRIGHT_BROWSERS_PATH` to a persistent directory and reuse across sessions.
- For CI/CD, consider using the official Playwright Docker images which bundle the browsers.

## Related Files
- Created project: `1688_bot/` with Python scripts using Playwright.
- The `login.json` file stores 1688.com authentication state.