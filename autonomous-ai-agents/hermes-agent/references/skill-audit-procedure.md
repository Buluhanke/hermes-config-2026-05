# Skill Audit Procedure — Which installed skills can be invoked?

Used when the user asks "what skills are broken", "which skills can't be called", or similar audit requests.

## Procedure

### 1. Get the full skill list
```python
skills_list()  # returns list of skill names + descriptions
```

### 2. Categorize each skill by dependency type

**A) CLI-dependent skills** — check with `which`:
```bash
which claude codex opencode himalaya xurl remindctl memo imsg findmy \
     linear notion gws nano-pdf hamelnb yuanbao airtable 2>/dev/null || echo "NOT FOUND"
```

**B) Python package skills** — check with `python3 -c "import <pkg>"`:
```bash
python3 -c "import torch; print(torch.__version__)" 2>&1
python3 -c "import playwright; print(playwright.__version__)" 2>&1
# etc.
```

**C) macOS app skills** — check with `ls /Applications/*.app`:
```bash
ls "/Applications/Spotify.app" 2>/dev/null && echo "exists" || echo "NOT FOUND"
ls "/Applications/Obsidian.app" 2>/dev/null && echo "exists" || echo "NOT FOUND"
```

Unlike third-party apps, Apple built-in apps (Reminders, Notes, Messages, FindMy) exist at `/System/Applications/` but the CLIs that skills depend on (remindctl, memo, imsg, findmy) are NOT installed — the skills reference non-existent third-party CLI wrappers.

**D) API-key-dependent skills** — check config.yaml:
```bash
grep -A2 "1688-open-platform" ~/.hermes/config.yaml 2>/dev/null
# or check .env
grep "1688\|MINIMAX\|OPENAI" ~/.hermes/.env 2>/dev/null
```

**E) MCP-server-dependent skills**:
```bash
ls ~/.hermes/mcp_servers/ 2>/dev/null || echo "no mcp_servers dir"
```

### 3. Classify each skill

| Status | Meaning |
|--------|---------|
| ✅ Ready | Dependencies all confirmed present |
| ❌ CLI missing | Required `which` didn't find the binary |
| ❌ Package missing | `python3 -c "import <pkg>"` failed |
| ❌ App missing | Application not installed (Spotify, Obsidian, etc.) |
| ❌ API key missing | No credentials in config/.env |
| ❌ Deprecated | Skill says it's replaced by another |
| ⚠️ Partial | Path exists but times out on first use (moss-tts-nano) |

### 4. Report grouping

Group by failure reason, not alphabetically. This makes it actionable:
- **CLI missing** (bulk install opportunity)
- **Python packages missing** (pip install one shot)
- **API keys missing** (need account registration)
- **Apps missing** (need manual download/install)
- **Deprecated** (safe to delete)

## Traps & pitfalls

- **Apple system apps exist but the skill depends on non-standard CLI wrappers** (remindctl, memo, imsg, findmy are third-party tools, not macOS built-ins). Don't assume "Reminders.app exists = skill works".
- **Playwright imports succeed** without error message — check the output; empty string ≠ error, it means the import worked.
- **torch and most ML packages are NOT installed** on this machine (aimac Mac mini) — all ML-related skills (audiocraft, segment-anything, vllm, unsloth, trl, etc.) are automatically broken.
- **Vision API** (vision_analyze) depends on the current model's capabilities — MiniMax-M2.7-highspeed via aicodee does NOT support `image_url` messages. Switch to a vision-capable provider to use vision tools.
- **1688-open-platform-api** has SKILL.md with endpoints/params but requires ISV account registration — not a tool-installation problem.
