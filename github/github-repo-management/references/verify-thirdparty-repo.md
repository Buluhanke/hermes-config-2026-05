# Verifying a third-party GitHub repo claim

## When to Use

Use when the user supplies a repo name/URL plus a claim (star count, feature list,
"it can do X") and wants it checked before adopting, recommending, or installing.

## Procedure

1. **Fetch the canonical record**, not a search result:
   `curl -s https://api.github.com/repos/OWNER/REPO`.
   The single-repo endpoint is live; `/search/repositories` is indexed and its
   totals drift. Report `stargazers_count`, `forks_count`, `open_issues_count`,
   `language`, `license.spdx_id`, `pushed_at`. If the user's number is stale, say
   so plainly and give the live one.

2. **Cross-check every feature claim against source.** Fetch the default branch's
   `README.md` from `raw.githubusercontent.com/OWNER/REPO/<branch>/README.md`,
   then open the implementation file for any load-bearing behavior. The repo
   `description` and README bullet list are marketing; they can invert a safety
   claim outright (example shape: "signature verification" turning out to be the
   app's own signing certificate plus a disclaimer that third-party downloads are
   NOT validated). Correct the claim explicitly instead of repeating it.

3. **Check whether compatibility claims survive a format comparison.** When the
   tool produces an artifact meant for another system (a skill file, a config),
   read its renderer/serializer in source and compare field-by-field with the
   target schema. Do not infer compatibility from the artifact's name.

4. **Resolve install artifacts from the live API:** `GET /releases/latest`, pick
   the asset matching the host architecture. Do not trust a Homebrew tap/cask or
   other package-manager formula — these lag on version and can point at an old
   owner/repo name. Remove a hand-built tap after use so a later upgrade cannot
   pull a dead URL.

5. **Verify the transfer** before mounting/installing: compare the local byte
   count with the API asset's `size`. If the host's release CDN stalls at zero
   bytes (HEAD still returns 302 + Content-Length), fetch through a mirror by
   prefixing the full original URL — e.g. `https://gh-proxy.com/<original-url>` —
   with `curl -L -C - --retry 8` for resume, then re-check the byte count. Mirror
   availability churns; probe several and use one that returns HTTP 206 on a
   ranged request.

6. **Report shape:** a short verified-facts table, the explicit correction(s),
   then one concrete next action. Never silently adopt the user's claim.

## Pitfalls

- **Trusting the star figure from a topic list or search snippet** — those are
  snapshots; only `/repos/OWNER/REPO` is authoritative.
- **Reading the README summary for a safety/feature claim** — the disclaimer
  and the implementation often contradict the headline bullet; read both.
- **Installing from a package-manager formula without checking the release API**
  — a stale formula silently installs an old version or fails on a dead URL.
- **Declaring a download complete on exit code alone** — with a throttled CDN,
  curl can return a 302 and zero bytes; compare against the API `size`.
