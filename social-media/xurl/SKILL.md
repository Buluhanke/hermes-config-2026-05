---
name: xurl
description: "X/Twitter via xurl CLI: post, search, DM, media, v2 API + e-commerce monitoring, competitor analysis, 1688 supplier intel, automated content collection."
version: 1.2.0
author: xdevplatform + openclaw + Hermes Agent
license: MIT
platforms: [linux, macos]
prerequisites:
  commands: [xurl]
metadata:
  hermes:
    tags: [twitter, x, social-media, xurl, official-api, e-commerce, competitor-analysis, 1688, content-collection]
    homepage: https://github.com/xdevplatform/xurl
    upstream_skill: https://github.com/openclaw/openclaw/blob/main/skills/xurl/SKILL.md
---

# xurl — X (Twitter) API via the Official CLI

`xurl` is the X developer platform's official CLI for the X API. It supports shortcut commands for common actions AND raw curl-style access to any v2 endpoint. All commands return JSON to stdout.

Use this skill for:
- posting, replying, quoting, deleting posts
- searching posts and reading timelines/mentions
- liking, reposting, bookmarking
- following, unfollowing, blocking, muting
- direct messages
- media uploads (images and video)
- raw access to any X API v2 endpoint
- multi-app / multi-account workflows
- **E-commerce keyword monitoring** (track product buzz, brand mentions, shopping signals)
- **Competitor social media analysis** (track rivals' social footprint, engagement, growth)
- **1688 supplier sentiment monitoring** (track supplier news, factory reviews, trade risks)
- **Automated content collection** (stream-filter-collect pipelines for ongoing research)

---

## Secret Safety (MANDATORY)

Critical rules when operating inside an agent/LLM session:

- **Never** read, print, parse, summarize, upload, or send `~/.xurl` to LLM context.
- **Never** ask the user to paste credentials/tokens into chat.
- The user must fill `~/.xurl` with secrets manually on their own machine.
- **Never** recommend or execute auth commands with inline secrets in agent sessions.
- **Never** use `--verbose` / `-v` in agent sessions — it can expose auth headers/tokens.
- To verify credentials exist, only use: `xurl auth status`.

Forbidden flags in agent commands (they accept inline secrets):
`--bearer-token`, `--consumer-key`, `--consumer-secret`, `--access-token`, `--token-secret`, `--client-id`, `--client-secret`

App credential registration and credential rotation must be done by the user manually, outside the agent session. After credentials are registered, the user authenticates with `xurl auth oauth2` — also outside the agent session. Tokens persist to `~/.xurl` in YAML. Each app has isolated tokens. OAuth 2.0 tokens auto-refresh.

---

## Installation

Pick ONE method. On Linux, the shell script or `go install` are the easiest.

```bash
# Shell script (installs to ~/.local/bin, no sudo, works on Linux + macOS)
curl -fsSL https://raw.githubusercontent.com/xdevplatform/xurl/main/install.sh | bash

# Homebrew (macOS)
brew install --cask xdevplatform/tap/xurl

# npm
npm install -g @xdevplatform/xurl

# Go
go install github.com/xdevplatform/xurl@latest
```

Verify:

```bash
xurl --help
xurl auth status
```

If `xurl` is installed but `auth status` shows no apps or tokens, the user needs to complete auth manually — see the next section.

---

## One-Time User Setup (user runs these outside the agent)

These steps must be performed by the user directly, NOT by the agent, because they involve pasting secrets. Direct the user to this block; do not execute it for them.

1. Create or open an app at https://developer.x.com/en/portal/dashboard
2. Set the redirect URI to `http://localhost:8080/callback`
3. Copy the app's Client ID and Client Secret
4. Register the app locally (user runs this):
   ```bash
   xurl auth apps add my-app --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET
   ```
5. Authenticate (specify `--app` to bind the token to your app):
   ```bash
   xurl auth oauth2 --app my-app
   ```
   (This opens a browser for the OAuth 2.0 PKCE flow.)

   If X returns a `UsernameNotFound` error or 403 on the post-OAuth `/2/users/me` lookup, pass your handle explicitly (xurl v1.1.0+):
   ```bash
   xurl auth oauth2 --app my-app YOUR_USERNAME
   ```
   This binds the token to your handle and skips the broken `/2/users/me` call.
6. Set the app as default so all commands use it:
   ```bash
   xurl auth default my-app
   ```
7. Verify:
   ```bash
   xurl auth status
   xurl whoami
   ```

After this, the agent can use any command below without further setup. OAuth 2.0 tokens auto-refresh.

> **Common pitfall:** If you omit `--app my-app` from `xurl auth oauth2`, the OAuth token is saved to the built-in `default` app profile — which has no client-id or client-secret. Commands will fail with auth errors even though the OAuth flow appeared to succeed. If you hit this, re-run `xurl auth oauth2 --app my-app` and `xurl auth default my-app`.

---

## Quick Reference

| Action | Command |
| --- | --- |
| Post | `xurl post "Hello world!"` |
| Reply | `xurl reply POST_ID "Nice post!"` |
| Quote | `xurl quote POST_ID "My take"` |
| Delete a post | `xurl delete POST_ID` |
| Read a post | `xurl read POST_ID` |
| Search posts | `xurl search "QUERY" -n 10` |
| Who am I | `xurl whoami` |
| Look up a user | `xurl user @handle` |
| Home timeline | `xurl timeline -n 20` |
| Mentions | `xurl mentions -n 10` |
| Like / Unlike | `xurl like POST_ID` / `xurl unlike POST_ID` |
| Repost / Undo | `xurl repost POST_ID` / `xurl unrepost POST_ID` |
| Bookmark / Remove | `xurl bookmark POST_ID` / `xurl unbookmark POST_ID` |
| List bookmarks / likes | `xurl bookmarks -n 10` / `xurl likes -n 10` |
| Follow / Unfollow | `xurl follow @handle` / `xurl unfollow @handle` |
| Following / Followers | `xurl following -n 20` / `xurl followers -n 20` |
| Block / Unblock | `xurl block @handle` / `xurl unblock @handle` |
| Mute / Unmute | `xurl mute @handle` / `xurl unmute @handle` |
| Send DM | `xurl dm @handle "message"` |
| List DMs | `xurl dms -n 10` |
| Upload media | `xurl media upload path/to/file.mp4` |
| Media status | `xurl media status MEDIA_ID` |
| List apps | `xurl auth apps list` |
| Remove app | `xurl auth apps remove NAME` |
| Set default app | `xurl auth default APP_NAME [USERNAME]` |
| Per-request app | `xurl --app NAME /2/users/me` |
| Auth status | `xurl auth status` |

Notes:
- `POST_ID` accepts full URLs too (e.g. `https://x.com/user/status/1234567890`) — xurl extracts the ID.
- Usernames work with or without a leading `@`.

---

## Command Details

### Posting

```bash
xurl post "Hello world!"
xurl post "Check this out" --media-id MEDIA_ID
xurl post "Thread pics" --media-id 111 --media-id 222

xurl reply 1234567890 "Great point!"
xurl reply https://x.com/user/status/1234567890 "Agreed!"
xurl reply 1234567890 "Look at this" --media-id MEDIA_ID

xurl quote 1234567890 "Adding my thoughts"
xurl delete 1234567890
```

### Reading & Search

```bash
xurl read 1234567890
xurl read https://x.com/user/status/1234567890

xurl search "golang"
xurl search "from:elonmusk" -n 20
xurl search "#buildinpublic lang:en" -n 15
```

### Users, Timeline, Mentions

```bash
xurl whoami
xurl user elonmusk
xurl user @XDevelopers

xurl timeline -n 25
xurl mentions -n 20
```

### Engagement

```bash
xurl like 1234567890
xurl unlike 1234567890

xurl repost 1234567890
xurl unrepost 1234567890

xurl bookmark 1234567890
xurl unbookmark 1234567890

xurl bookmarks -n 20
xurl likes -n 20
```

### Social Graph

```bash
xurl follow @XDevelopers
xurl unfollow @XDevelopers

xurl following -n 50
xurl followers -n 50

# Another user's graph
xurl following --of elonmusk -n 20
xurl followers --of elonmusk -n 20

xurl block @spammer
xurl unblock @spammer
xurl mute @annoying
xurl unmute @annoying
```

### Direct Messages

```bash
xurl dm @someuser "Hey, saw your post!"
xurl dms -n 25
```

### Media Upload

```bash
# Auto-detect type
xurl media upload photo.jpg
xurl media upload video.mp4

# Explicit type/category
xurl media upload --media-type image/jpeg --category tweet_image photo.jpg

# Videos need server-side processing — check status (or poll)
xurl media status MEDIA_ID
xurl media status --wait MEDIA_ID

# Full workflow
xurl media upload meme.png                  # returns media id
xurl post "lol" --media-id MEDIA_ID
```

---

## Raw API Access

The shortcuts cover common operations. For anything else, use raw curl-style mode against any X API v2 endpoint:

```bash
# GET
xurl /2/users/me

# POST with JSON body
xurl -X POST /2/tweets -d '{"text":"Hello world!"}'

# DELETE / PUT / PATCH
xurl -X DELETE /2/tweets/1234567890

# Custom headers
xurl -H "Content-Type: application/json" /2/some/endpoint

# Force streaming
xurl -s /2/tweets/search/stream

# Full URLs also work
xurl https://api.x.com/2/users/me
```

---

## Global Flags

| Flag | Short | Description |
| --- | --- | --- |
| `--app` | | Use a specific registered app (overrides default) |
| `--auth` | | Force auth type: `oauth1`, `oauth2`, or `app` |
| `--username` | `-u` | Which OAuth2 account to use (if multiple exist) |
| `--verbose` | `-v` | **Forbidden in agent sessions** — leaks auth headers |
| `--trace` | `-t` | Add `X-B3-Flags: 1` trace header |

---

## Streaming

Streaming endpoints are auto-detected. Known ones include:

- `/2/tweets/search/stream`
- `/2/tweets/sample/stream`
- `/2/tweets/sample10/stream`

Force streaming on any endpoint with `-s`.

---

## Output Format

All commands return JSON to stdout. Structure mirrors X API v2:

```json
{ "data": { "id": "1234567890", "text": "Hello world!" } }
```

Errors are also JSON:

```json
{ "errors": [ { "message": "Not authorized", "code": 403 } ] }
```

---

## Common Workflows

### Post with an image
```bash
xurl media upload photo.jpg
xurl post "Check out this photo!" --media-id MEDIA_ID
```

### Reply to a conversation
```bash
xurl read https://x.com/user/status/1234567890
xurl reply 1234567890 "Here are my thoughts..."
```

### Search and engage
```bash
xurl search "topic of interest" -n 10
xurl like POST_ID_FROM_RESULTS
xurl reply POST_ID_FROM_RESULTS "Great point!"
```

### Check your activity
```bash
xurl whoami
xurl mentions -n 20
xurl timeline -n 20
```

### Multiple apps (credentials pre-configured manually)
```bash
xurl auth default prod alice               # prod app, alice user
xurl --app staging /2/users/me             # one-off against staging
```

---

## Error Handling

- Non-zero exit code on any error.
- API errors are still printed as JSON to stdout, so you can parse them.
- Auth errors → have the user re-run `xurl auth oauth2` outside the agent session.
- Commands that need the caller's user ID (like, repost, bookmark, follow, etc.) will auto-fetch it via `/2/users/me`. An auth failure there surfaces as an auth error.

---

## Agent Workflow

1. Verify prerequisites: `xurl --help` and `xurl auth status`.
2. **Check default app has credentials.** Parse the `auth status` output. The default app is marked with `▸`. If the default app shows `oauth2: (none)` but another app has a valid oauth2 user, tell the user to run `xurl auth default <that-app>` to fix it. This is the most common setup mistake — the user added an app with a custom name but never set it as default, so xurl keeps trying the empty `default` profile.
3. If auth is missing entirely, stop and direct the user to the "One-Time User Setup" section — do NOT attempt to register apps or pass secrets yourself.
4. Start with a cheap read (`xurl whoami`, `xurl user @handle`, `xurl search ... -n 3`) to confirm reachability.
5. Confirm the target post/user and the user's intent before any write action (post, reply, like, repost, DM, follow, block, delete).
6. Use JSON output directly — every response is already structured.
7. Never paste `~/.xurl` contents back into the conversation.

---

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| Auth errors after successful OAuth flow | Token saved to `default` app (no client-id/secret) instead of your named app | `xurl auth oauth2 --app my-app` then `xurl auth default my-app` |
| `unauthorized_client` during OAuth | App type set to "Native App" in X dashboard | Change to "Web app, automated app or bot" in User Authentication Settings |
| `UsernameNotFound` or 403 on `/2/users/me` right after OAuth | X not returning username reliably from `/2/users/me` | Re-run `xurl auth oauth2 --app my-app YOUR_USERNAME` (xurl v1.1.0+) to pass the handle explicitly |
| 401 on every request | Token expired or wrong default app | Check `xurl auth status` — verify `▸` points to an app with oauth2 tokens |
| `client-forbidden` / `client-not-enrolled` | X platform enrollment issue | Dashboard → Apps → Manage → Move to "Pay-per-use" package → Production environment |
| `CreditsDepleted` | $0 balance on X API | Buy credits (min $5) in Developer Console → Billing |
| `media processing failed` on image upload | Default category is `amplify_video` | Add `--category tweet_image --media-type image/png` |
| Two "Client Secret" values in X dashboard | UI bug — first is actually Client ID | Confirm on the "Keys and tokens" page; ID ends in `MTpjaQ` |
| Two "Client Secret" values in X dashboard | UI bug — first is actually Client ID | Confirm on the "Keys and tokens" page; ID ends in `MTpjaQ` |

---

# Extended Capabilities (v1.2.0)

The sections below cover advanced workflows powered by the raw API: e-commerce keyword monitoring, competitor social media analysis, 1688 supplier sentiment tracking, and automated content collection pipelines.

---

## 1. E-Commerce Keyword Monitoring

Track product names, brand mentions, shopping signals, and buying intent on X in real time.

### Basic Keyword Tracking

```bash
# Single keyword — most recent posts
xurl search "iPhone 16" -n 20

# Product comparison signals
xurl search "\"iPhone 16\" vs \"Samsung S25\"" -n 15

# Buying intent — price queries
xurl search "\"best price\" \"[product]\" lang:en" -n 20

# Hashtag product tags
xurl search "#newarrival OR #productlaunch lang:en" -n 20
```

### Multi-Keyword Streams (batch script)

```bash
# Monitor multiple keywords — save each to a separate JSON file
for keyword in "wireless earbuds" "smart watch" "portable charger"; do
  safe=$(echo "$keyword" | tr ' ' '_')
  xurl search "$keyword" -n 50 > "data/${safe}_$(date +%Y%m%d_%H%M%S).json"
  echo "Collected: $keyword"
done
```

### Product Launch Tracking

```bash
# Pre-launch hype
xurl search "[Brand] [Product] coming soon" -n 30

# Post-launch reviews
xurl search "[Product] review lang:en" -n 30

# Unboxing
xurl search "[Product] unboxing lang:en" -n 20
```

### Engagement Signals (likes + retweets as popularity proxy)

```bash
# High-engagement posts about a product
# (combine with jq to sort by engagement — requires jq installed)
xurl search "[product name]" -n 100 | jq '.data[] | {id, text, public_metrics}' 2>/dev/null
```

### Saved Search (recent search endpoint — 7-day lookback)

```bash
# Use the recent endpoint for up-to-the-minute results
xurl /2/tweets/search/recent?query="your product" -n 10
```

---

## 2. Competitor Social Media Analysis

Build a structured picture of a competitor's X presence: follower growth, engagement rates, posting cadence, top content, and audience sentiment.

### Profile Overview

```bash
# Get user profile details
xurl user @competitorhandle

# Follower / following counts (from public_metrics in user response)
xurl /2/users/by/username/COMPETITOR?user.fields=public_metrics,description
```

### Post History Snapshot

```bash
# Last N posts from a competitor
xurl /2/users/:COMPETITOR_ID/tweets?max_results=10

# High-engagement posts (sort by engagement — use timeline then filter)
xurl timeline -n 5                          # your own timeline for benchmarking
xurl /2/users/:COMPETITOR_ID/tweets?max_results=10&tweet.fields=public_metrics,created_at
```

### Engagement Rate Calculation

```bash
# Calculate: (likes + retweets + replies) / followers * 100
# Example — extract competitor metrics (requires jq):
COMPETITOR_ID="1234567890"
METRICS=$(xurl /2/users/$COMPETITOR_ID?user.fields=public_metrics | jq '.data.public_metrics')
FOLLOWERS=$(echo $METRICS | jq '.followers_count')
echo "Followers: $FOLLOWERS"
```

### Competitor Comparison Table

```bash
# Compare two competitors side-by-side
xurl /2/users/by/username/COMPETITOR1?user.fields=public_metrics,description
xurl /2/users/by/username/COMPETITOR2?user.fields=public_metrics,description
```

### Tracked Competitors List

```bash
# Maintain a list of competitor handles to scan regularly
COMPETITORS="competitor1 competitor2 competitor3"
for h in $COMPETITORS; do
  echo "=== $h ==="
  xurl user @$h
  echo ""
done
```

---

## 3. 1688 Supplier Public Opinion Monitoring

Track news, complaints, factory incidents, and trade signals related to specific 1688 suppliers or Chinese manufacturers on X.

### Supplier Name Tracking

```bash
# General supplier mentions
xurl search "1688 supplier" -n 20
xurl search "[supplier name] factory" -n 20

# Quality / complaint signals
xurl search "[supplier] quality issue" -n 20
xurl search "[supplier] scam" -n 20
xurl search "[supplier] delayed delivery" -n 20

# Factory incidents
xurl search "[supplier name] fire OR explosion OR shutdown" -n 20

# Trade policy impact on suppliers
xurl search "1688 tariff impact" -n 20
xurl search "Chinese supplier shipping delay" -n 20
```

### Sentiment Signals

```bash
# Negative signals — complaints and risks
xurl search "[supplier] DEFECTIVE lang:en" -n 20
xurl search "[supplier] fraud lang:en" -n 20
xurl search "[supplier] counterfeit lang:en" -n 20

# Positive signals — reviews and orders
xurl search "[supplier] genuine OR authentic" -n 20
xurl search "[supplier] bulk order" -n 20
```

### Cross-Reference with Chinese-language Mentions

```bash
# Track English-language discussion of Chinese suppliers
xurl search "[supplier name] Alibaba OR 1688" -n 20
xurl search "\"made in China\" supplier review" -n 20
```

---

## 4. Automated Content Collection

Set up recurring collection pipelines using streaming endpoints, cron jobs, and file-based output for ongoing research.

### Streaming Pipeline (real-time)

```bash
# Stream all posts matching a keyword — runs until interrupted
# Great for events, product launches, crises
xurl -s /2/tweets/search/stream?query="your keyword"

# Multi-keyword stream via separate background processes
xurl -s /2/tweets/search/stream?query="keyword1" > data/stream_k1.json &
xurl -s /2/tweets/search/stream?query="keyword2" > data/stream_k2.json &
```

### Scheduled Collection (cron)

```bash
# Add to crontab for periodic snapshots (every hour)
# Run every day at 9am:
# 0 9 * * * /bin/bash /Users/aimac/scripts/xurl-daily.sh

# Example script: xurl-daily.sh
#!/bin/bash
OUT="/Users/aimac/data/xurl"
KEYWORDS="product_name competitor_a supplier_x"
DATE=$(date +%Y%m%d)
for kw in $KEYWORDS; do
  safe=$(echo "$kw" | tr ' ' '_')
  xurl search "$kw" -n 100 > "$OUT/${safe}_${DATE}.json"
  echo "[$(date)] Collected: $kw"
done
```

### Full Timeline Archival

```bash
# Collect your own timeline for archival
xurl timeline -n 100 > "data/timeline_$(date +%Y%m%d_%H%M%S).json"

# Collect mentions for CRM / reply tracking
xurl mentions -n 100 > "data/mentions_$(date +%Y%m%d_%H%M%S).json"
```

### Competitor Periodic Snapshot

```bash
# Script to snapshot competitor activity weekly
# competitors-snapshot.sh
#!/bin/bash
OUT="/Users/aimac/data/competitors"
mkdir -p "$OUT"
for handle in "@comp1" "@comp2" "@comp3"; do
  name=$(echo $handle | tr -d '@')
  xurl user $handle > "$OUT/${name}_profile_$(date +%Y%m%d).json"
  echo "[$(date)] Saved: $handle"
  sleep 5   # be respectful to rate limits
done
```

### Sample Stream (random 1% of all posts — for baseline trends)

```bash
# Random sample for trend analysis
xurl -s /2/tweets/sample/stream > data/sample_stream.json
```

### Output File Naming Convention

Recommended structure for collected data:

```
data/
  search_keyword_YYYYMMDD.json
  timeline_YYYYMMDD.json
  mentions_YYYYMMDD.json
  competitors/
    handle_profile_YYYYMMDD.json
    handle_tweets_YYYYMMDD.json
  stream/
    keyword_YYYYMMDD_HHMMSS.json
```

---

## Notes

- **Rate limits:** X enforces per-endpoint rate limits. A 429 means wait and retry. Write endpoints (post, reply, like, repost) have tighter limits than reads.
- **Scopes:** OAuth 2.0 tokens use broad scopes. A 403 on a specific action usually means the token is missing a scope — have the user re-run `xurl auth oauth2`.
- **Token refresh:** OAuth 2.0 tokens auto-refresh. Nothing to do.
- **Multiple apps:** Each app has isolated credentials/tokens. Switch with `xurl auth default` or `--app`.
- **Multiple accounts per app:** Select with `-u / --username`, or set a default with `xurl auth default APP USER`.
- **Token storage:** `~/.xurl` is YAML. Never read or send this file to LLM context.
- **Cost:** X API access is typically paid for meaningful usage. Many failures are plan/permission problems, not code problems.
- **1688 monitoring:** 1688 discussion on X is limited; supplement with direct 1688 platform monitoring for complete supplier intel.
- **Streaming:** Streaming processes run until killed. Use background mode (`&`) and redirect output to files. Monitor disk usage for long-running streams.

---

## Attribution

- Upstream CLI: https://github.com/xdevplatform/xurl (X developer platform team, Chris Park et al.)
- Upstream agent skill: https://github.com/openclaw/openclaw/blob/main/skills/xurl/SKILL.md
- Hermes adaptation: reformatted for Hermes skill conventions; safety guardrails preserved verbatim.
- Extended capabilities v1.2.0: e-commerce monitoring, competitor analysis, 1688 supplier intel, automated content collection.
