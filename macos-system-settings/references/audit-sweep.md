# macOS time/region/clock-format audit sweep

Run this after any change to timezone, region, or 24h/12h format, to confirm
every surface is consistent (the user asked "check everything" — don't eyeball it).

```bash
echo "24h force: $(defaults read -g AppleICUForce24HourTime 2>&1)"
echo "locale   : $(defaults read -g AppleLocale 2>&1)"
echo "time     : $(date '+%H:%M:%S %Z %Y-%m-%d')"

# scan user-domain plists for leftover 12h / time-format / region keys
for dom in -g com.apple.systempreferences com.apple.menuextra.clock com.apple.controlcenter; do
  echo "-- $dom --"
  defaults read $dom 2>/dev/null | grep -iE "Hour|TimeFormat|Region|Locale" || echo "(none)"
done

# lock screen / login window has NO separate plist — it follows the global 24h switch
echo "-- loginwindow --"
defaults read com.apple.loginwindow 2>/dev/null | grep -iE "time|clock|hour" || echo "(follows global AppleICUForce24HourTime)"

# terminal locale (informational; does NOT affect 24h — date uses %H by default)
echo "LC_TIME=$LC_TIME"
```

Expected after a "Beijing time + US region + 24h" setup:
- `AppleICUForce24HourTime` = 1
- `AppleLocale` = `..._US` (unchanged)
- `time` shows `HH:MM:SS CST` with NO AM/PM
- no 12h/TimeFormat keys in the scanned plists
- loginwindow: nothing (follows global)

Note: `AppleTerritory` may not exist (only `AppleLocale` like `zh-Hant_US`).
Absence is fine — territory defaults from the locale suffix. Don't create it.
