---
name: macos-system-settings
description: macOS system preference tweaks that are commonly requested and easy to get subtly wrong — timezone set independent of region, forcing a 24-hour clock that overrides a US region, and auditing every surface where the clock/date format appears. Use when a user asks to change system time zone, keep region but change time, set 24-hour format, remove AM/PM, or "check/fix the clock or date format".
triggers:
  - "set system timezone to Beijing / Shanghai but keep region as US"
  - "change to 24-hour clock / remove AM-PM"
  - "timezone and region should be different"
  - "the clock shows the wrong format"
  - "audit where the system time / date format is set"
  - "force 24 hour time on a US locale"
---

# macOS system settings: timezone, region, clock format

## Key mental model
On macOS these three are **independent**:
- **Time Zone** (`systemsetup -settimezone`) — what UTC offset the clock uses.
- **Region** (`AppleLocale` territory, e.g. `..._US`) — date/number/currency formatting conventions (MM/DD vs DD/MM, $ vs ¥).
- **24-hour vs 12-hour clock** — `AppleICUForce24HourTime`, a separate global override that wins over the region's default.

So "Beijing time but US region" is perfectly valid: set timezone to `Asia/Shanghai`, leave region `_US`, and force 24h to drop the AM/PM marker.

## Steps
1. **Set timezone** (needs sudo; the command prints a harmless `Error:-99` red herring but still succeeds — verify with the get command):
   ```bash
   sudo systemsetup -settimezone Asia/Shanghai
   sudo systemsetup -gettimezone        # expect: Time Zone: Asia/Shanghai
   date "+%H:%M:%S %Z %Y-%m-%d"         # UTC+8, no AM/PM
   ```
   List valid zones: `sudo systemsetup -listtimezones | grep -i "Asia/Shanghai"`.
2. **Force 24-hour clock** (independent of region; works even on `_US`):
   ```bash
   defaults write -g AppleICUForce24HourTime -bool true
   defaults read -g AppleICUForce24HourTime   # expect: 1
   killall SystemUIServer ControlCenter        # refresh menu bar clock
   ```
3. **Leave region alone** — do NOT touch `AppleLocale`/`AppleTerritory`. Confirm unchanged: `defaults read -g AppleLocale` (e.g. `zh-Hant_US`).

## Verify every surface (user asked "check everything")
Run a single sweep so nothing is missed:
```bash
echo "24h force: $(defaults read -g AppleICUForce24HourTime 2>&1)"
echo "locale   : $(defaults read -g AppleLocale 2>&1)"
echo "time     : $(date '+%H:%M:%S %Z %Y-%m-%d')"
# scan user-domain plists for leftover 12h / time-format keys
for dom in -g com.apple.systempreferences com.apple.menuextra.clock com.apple.controlcenter; do
  defaults read $dom 2>/dev/null | grep -iE "Hour|TimeFormat|Region|Locale" || true
done
# lock screen has NO separate plist — it follows the global 24h switch
defaults read com.apple.loginwindow 2>/dev/null | grep -iE "time|clock|hour" || echo "(loginwindow: none, follows global)"
```
- **Lock screen / login window clock**: no independent preference file — it reads the same global `AppleICUForce24HourTime`. Nothing extra to set; if you can't visually confirm, state that config-level it follows global.
- **Terminal `date`**: uses `%H` (24h) by default regardless of `LC_TIME`; the global force switch makes any Cocoa app show 24h.

## Pitfalls
- **`systemsetup -settimezone` returns `Error:-99 ... File:...InternetServices.m`** — a benign logging warning about network time sync, NOT a failure. Trust the subsequent `gettimezone` result, not the error line.
- **`AppleICUForce24HourTime` is the only reliable 24h lever on a US region.** Setting region to a 24h-default territory (e.g. `_GB`, `_DE`) also flips the clock — but it ALSO changes date/currency/number formatting the user may NOT want. Force the bool instead; it changes ONLY the clock.
- **Don't `killall SystemUIServer` alone** — also kill `ControlCenter` (Ventura+) so the menu bar fully re-reads. Both are safe to restart.
- **Region and timezone are different keys** — never "fix" a timezone complaint by changing `AppleLocale`; that drags in formatting changes the user didn't ask for.
- **`AppleTerritory` may not exist** (only `AppleLocale` like `zh-Hant_US`). Absence means territory defaults from the locale's suffix — that's fine, don't create it.

## References
- `references/audit-sweep.md` — the exact verification one-liner sweep used to confirm all time/format surfaces are consistent after a change.
