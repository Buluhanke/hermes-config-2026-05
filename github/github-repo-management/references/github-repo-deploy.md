# GitHub Repo Deployment Patterns

Quick reference for installing and running projects cloned from GitHub.

---

## Python Project Setup (uv-first)

### Standard uv workflow
```bash
cd ~/fara                        # project directory
uv sync                           # resolves pyproject.toml, downloads deps, creates .venv
```

**What `uv sync` does:**
1. Reads `pyproject.toml`
2. Resolves dependencies (creates `uv.lock` if absent)
3. Creates `.venv` in project dir if needed
4. Installs all packages

**Signals it's working:**
```
Resolved 216 packages in 3ms
Downloaded playwright (36.2MiB)
Installed 32 packages in 76ms
```

### Fallback: pip
```bash
cd ~/fara
pip install -e .                  # editable install from pyproject.toml
playwright install                # separate browser install if needed
```

### venv activation
```bash
cd ~/fara
.venv/bin/python --version        # confirm python exists
.venv/bin/pip list                # confirm packages installed
```

---

## Repository Discovery Priority

When user shares a GitHub URL or project name:

| Method | Use when | Tool/Command |
|--------|----------|-------------|
| **Web search** | First resort, fastest | `web_search(query)` — catches renamed/moved repos |
| **GitHub API file read** | README/content extraction | `mcp_github_get_file_contents(owner, repo, path)` |
| **GitHub API search** | Search repos by keyword | `mcp_github_search_repositories(query)` ⚠️ may return empty |
| **Raw curl** | README fallback | `curl -sL raw.githubusercontent.com/.../README.md` |

**Important:** `mcp_github_search_repositories` can return `{"items": []}` even for valid repos — web search is more reliable for discovery.

---

## Clone + Install Full Flow

```bash
# 1. Clone (HTTPS, works for public repos without proxy)
git clone https://github.com/microsoft/fara.git
cd fara

# 2. Check available tools
which uv && uv --version           # uv preferred
which pip && pip --version         # fallback

# 3. Install dependencies
uv sync 2>&1 | tail -20            # watch for success
# OR if uv not available:
# python3 -m venv .venv && source .venv/bin/activate && pip install -e .

# 4. Verify installation
ls .venv/bin/ | head -10
.venv/bin/python --version
.venv/bin/pip list | grep -E "fara|playwright"

# 5. Check for post-install steps
cat README.md | grep -A5 "Quick Start\|Installation\|Setup"
```

---

## Common Post-Install Steps

### Python projects often need:
```bash
# Browser/UI automation projects need Playwright browsers
playwright install

# Projects with scripts/
ls scripts/

# Models served via vllm need GPU
# Mac (no NVIDIA GPU) → CPU only, very slow
pip install vllm  # if NVIDIA available
```

### Node.js projects:
```bash
cd dashboard && npm install && npm run build
```

---

## Background Git Clone

When clone might take time (large repo, slow network):
```bash
terminal(background=true, command="git clone https://github.com/owner/repo.git", notify_on_complete=true)
# Poll with:
process(action='wait', session_id=proc_xxx, timeout=120)
```

---

## Key Pitfalls

1. **`uv sync` hangs** — common for large deps (playwright 36MB+). Background it and wait.
2. **Missing `playwright install`** — browser automation repos often need this separately.
3. **`mcp_github_search_repositories` empty** — don't trust it as primary. Web search finds repos that GitHub API search misses.
4. **web_extract payswall** — Firecrawl credits exhausted on GitHub/HuggingFace. Use curl raw.githubusercontent.com instead.
5. **vllm needs NVIDIA GPU** — on Mac, vllm runs on CPU only. INT4 quantization reduces VRAM needs (~4GB for 7B).

---

## Signal Reference: GitHub Repo Health at a Glance

| Signal | Good | Bad |
|--------|------|-----|
| Stars | 100+ | <10 |
| Last push | <3 months | >1 year |
| pyproject.toml | present | absent |
| README | detailed | vague/empty |
| install command | `pip/uv/cargo` | `npx skills add` ❌ |
| License | present | missing |