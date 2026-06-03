# GitHub API Empty Response Detection & Bypass (2026-06-03)

## Problem
When calling GitHub API for repo contents, responses can be:
1. **Normal**: JSON with `content` (base64), `sha`, `size`, `name`
2. **Empty body**: exit code 0, body empty or `[]`
3. **404 Not Found**: file doesn't exist in that path

## Detection
```bash
# Check response size — reliable for both rawgh and Contents API
size=$(curl -sf --max-time 10 "https://api.github.com/repos/<org>/<repo>/contents/<path>" | wc -c)
if [ "$size" -lt 100 ]; then
    echo "WARN: response < 100 bytes, likely empty"
fi
```

## GitHub Contents API vs raw.githubusercontent.com

| Scenario | Contents API | rawgh |
|----------|-------------|-------|
| github.com blocked | ❌ Also blocked | ❌ Also blocked |
| rawgh blocked by ad-filter | ✅ Still works | ❌ Blocked |
| Normal retrieval | base64 encoded | Plain text |

**Key insight**: Contents API uses github.com's HTTP stack, not the browser's — so ad-filter doesn't block it.

## AAAI2026 Scan Results (2026-06-03)
- 13 papers found in single scan
- 12 previously unknown to Hermes
- Highest yield subdirectory this week
- All extracted via GitHub Contents API base64 decode
