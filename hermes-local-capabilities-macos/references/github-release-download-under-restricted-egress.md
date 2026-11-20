# Installing GitHub-hosted binaries under restricted egress

Use when `brew install` stalls, `github.com` times out, or a release asset downloads at 0 bytes. The failure is usually split across several endpoints with different reachability — never conclude "GitHub is blocked" from one failed URL.

## 1. Probe endpoints before choosing a path

Probe in parallel with short timeouts; the results decide the route:

```bash
curl -s -o /dev/null -w "api=%{http_code} %{time_total}s\n" --max-time 12 https://api.github.com
curl -s -o /dev/null -w "codeload=%{http_code} %{time_total}s\n" --max-time 12 https://codeload.github.com/<owner>/<repo>/tar.gz/refs/heads/main
curl -s -o /dev/null -w "web=%{http_code} %{time_total}s\n" --max-time 12 https://github.com
curl -sIL --max-time 20 <release_asset_url> | grep -Ei 'HTTP/|location:|content-length'
```

- `api.github.com` + `codeload.github.com` reachable while `github.com` times out → skip git clone and web UI entirely.
- HEAD on the asset returns `302` → `200` with a real `content-length`, but a ranged GET returns `size=0` → CDN entity throttle. Route through a mirror.

## 2. Get the authoritative asset URL from the API

Never take a download URL from a README or a Homebrew cask without checking it. Fetch `https://api.github.com/repos/<owner>/<repo>/releases/latest` and read `tag_name`, and each asset's `name`, `size`, and `browser_download_url` (the `web_extract` tool returns this JSON cleanly; no shell pipe needed).

Use `size` as the post-download integrity check. Casks go stale: a cask may pin an older version and an obsolete org name after the project migrates — the cask URL can be dead while the API points at a live asset.

## 3. Mirror prefixes and resumable download

Mirror prefixes that have worked: `https://gh-proxy.com/`, `https://ghfast.top/`. Prefix the **full** GitHub URL:

```bash
URL="https://gh-proxy.com/https://github.com/<owner>/<repo>/releases/download/<tag>/<asset>"
curl -sL --max-time 20 -r 0-1048575 -o /dev/null \
  -w "%{http_code} %{size_download}B %{speed_download}B/s" "$URL"
```

Probe several prefixes; some return `000` or redirect to a landing page and must be discarded. Expect a few hundred KB/s for a ~200 MB asset — run the real download in the background with resume and completion notification:

```bash
curl -L -C - --retry 8 --retry-delay 3 --connect-timeout 20 \
  -o <asset> "$URL"
```

Verify with `stat -f%z <asset>` against the API `size`, then `shasum -a 256` if the project publishes a digest (many publish only an APK signing certificate, which authenticates the app itself, not a downloadable asset).

## 4. When `brew tap` is the blocker

`brew tap` clones from `github.com`. If that hangs, lay the tap down from codeload instead:

```bash
curl -sL --max-time 60 \
  https://codeload.github.com/<org>/homebrew-<name>/tar.gz/refs/heads/main -o /tmp/tap.tgz
mkdir -p /opt/homebrew/Library/Taps/<org>/homebrew-<name>
tar -xzf /tmp/tap.tgz -C /opt/homebrew/Library/Taps/<org>/homebrew-<name> --strip-components=1
brew tap | grep <org>/<name>
```

Inspect the cask before using it. If it is stale, install the API-sourced asset directly and **remove the hand-placed tap afterwards** (move its directory out of the Taps tree) — leaving a cask with dead URLs makes a future `brew upgrade` fail or fetch the wrong artifact.

## 5. Install an unsigned / unnotarized macOS dmg

```bash
hdiutil attach <asset>.dmg -nobrowse -quiet
cp -R /Volumes/<Volume>/<App>.app /Applications/
xattr -dr com.apple.quarantine /Applications/<App>.app
hdiutil detach /Volumes/<Volume> -quiet
defaults read /Applications/<App>.app/Contents/Info.plist CFBundleShortVersionString
codesign -dv /Applications/<App>.app 2>&1 | head -5
```

If a prior version exists, move it to the Trash before copying rather than deleting it in place. Gatekeeper blocks unsigned apps without the quarantine removal; `adhoc` signature is expected. Launch with `open -g -j` to avoid stealing focus.

## 6. Prove the app actually works

A running process proves only that it launched. For an app with a local database or cache, query the persisted state for real fetched data:

```bash
sqlite3 "$HOME/Library/Application Support/<App>/<db>" \
  "SELECT name FROM sqlite_master WHERE type='table';"
sqlite3 -header -column "<db>" "SELECT * FROM cache_entries;"
```

A populated feed/cache with current items demonstrates the network path works. If the app disables its accessibility bridge, read the local state instead of fighting AX — check its session log for the reason before attempting GUI verification.

## Pitfalls (rules)

- Probe every endpoint separately; one blocked host does not imply the whole platform is unreachable.
- Use the API as the source of truth for version, asset URL, and size; READMEs and casks lag behind.
- Confirm a mirror actually serves bytes with a ranged GET before committing to a long download.
- Never leave a hand-placed tap with stale URLs in Homebrew's tree.
- Do not claim a download is verified by size alone when the project publishes a signing certificate for a different artifact; state precisely what was checked.
- Do not equate "process is running" with "feature works"; query local state for evidence of real fetches.
