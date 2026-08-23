# WeChat Multi-Instance on macOS — Investigation Report

**Date:** 2026-07-15
**WeChat version:** 4.1.11 (Mac)
**macOS:** macOS 26.5.2

---

## What the user wanted

A Zhihu article (blocked on this network, URL shared with anchor `#:~:text=...C1%E5%90%8E...`) describes a "stable" WeChat multi-instance method involving C1/C3/C6 steps — likely WeChat's built-in **multi-account switching** feature (账号切换), not system-level multi-instance. Could not fetch the article to verify.

---

## Methods attempted and results

| Method | Command | Result |
|--------|---------|--------|
| Standard multi-instance launch | `open -n /Applications/WeChat.app` | ❌ macOS deduplicates by bundle ID — only activates existing instance |
| Hidden `--multiple-instance` flag | `/Applications/WeChat.app/Contents/MacOS/WeChat --multiple-instance` | ❌ Flag not implemented by WeChat 4.x |
| Copy app + change bundle ID + ad-hoc sign | `sudo cp -R ...`, `defaults write ... CFBundleIdentifier ...`, `codesign --force --sign -` | ❌ **No code signing certificate available** (`security find-identity -v -p codesigning` returns 0 identities). WeChat2.app rejected by Gatekeeper: "executable is missing" (bundle ID mismatch without valid signature) |
| `open` without `-n` | `open /Applications/WeChat.app` | ✅ Launches normally (single instance) |

---

## Key findings

- **No developer certificate:** `security find-identity -v -p codesigning` returns `0 valid identities found`. The machine has never been used for code signing — no Apple Developer account certs, no self-signed certs. The "copy + re-sign" approach is **blocked on this machine** and likely on most non-developer Macs.
- **WeChat 4.x actively prevents multi-instance** via `open -n`. The bundle identifier deduplication is at the macOS `open` level, not a WeChat feature flag.
- **`--multiple-instance` does not exist** in the WeChat 4.1.11 binary — confirmed via `strings` analysis; no matching CLI handler found.

---

## Working alternatives

1. **WeChat built-in multi-account switch** (most reliable)
   - WeChat menu → 账号切换 (Account Switch) → 添加账号 (Add Account)
   - Cycles between saved accounts without system-level multi-instance
   - No third-party tools, no code signing needed

2. **Web WeChat** (web.wechat.com)
   - Login second account in browser
   - No desktop app duplication needed

3. **Virtual machine** (Parallel/VMware)
   - Full Windows environment → runs native WeChat.exe
   - Completely isolated from macOS WeChat process space
   - Overkill for most use cases

---

## Why the Zhihu article matters

The article's C1/C3/C6 step notation (C1 = 微信多开操作步骤? C3/C6 = 进入后的正确界面?) strongly suggests it's describing **WeChat's own multi-account switching UI**, not a system-level trick. The method likely works reliably because it uses WeChat's documented account-switching feature rather than fighting macOS app sandboxing.

**Recommendation:** Read the article from a network that can reach zhihu.com (mobile hotspot, VPN) and follow the account-switching steps directly in the WeChat UI.
