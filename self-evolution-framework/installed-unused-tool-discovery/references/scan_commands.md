# 盲区扫描命令清单

## 1. Python venv 装的库 (看哪些可能用得上)

```bash
# 列出 venv 里所有命令
ls ~/.hermes/hermes-agent/venv/bin/ | grep -vE "python|pip|setuptools" | head -50

# pip list 看库
~/.hermes/hermes-agent/venv/bin/pip list 2>/dev/null | head -50

# 关键库 (已知常用, 但可能没用过的)
~/.hermes/hermes-agent/venv/bin/python -c "
import importlib
candidates = ['ddgs', 'duckduckgo_search', 'searxng', 'crawl4ai', 'firecrawl', 'playwright', 'selenium', 'pandas', 'numpy', 'requests', 'httpx', 'beautifulsoup4', 'lxml', 'pypdf', 'pdfplumber', 'PIL', 'cv2', 'torch', 'transformers', 'openai', 'anthropic']
for c in candidates:
    try:
        m = importlib.import_module(c)
        print(f'✅ {c}: {getattr(m, \"__version__\", \"?\")}')
    except ImportError:
        print(f'❌ {c}: not installed')
"
```

## 2. 系统 CLI (brew + 系统自带)

```bash
# brew 装的
brew list 2>/dev/null | head -30

# 系统命令
which jq ffmpeg curl wget gh rg fd 2>/dev/null
```

## 3. Node.js / npm MCP

```bash
# 全局 npm
npm list -g --depth=0 2>/dev/null

# 找 npx 装的 MCP
ls ~/.npm/_npx/ 2>/dev/null
```

## 4. Skills 用了多少次 (从 usage.json)

```bash
# 用了 >= 1 次的 skill
python3 -c "
import json
with open('/Users/aimac/.hermes/skills/.usage.json') as f:
    d = json.load(f)
unused = [k for k, v in d.items() if v.get('uses', 0) == 0]
print(f'用了 0 次的 skill 数量: {len(unused)}')
print('前 20:', unused[:20])
"
```

## 5. 集成扫描脚本 (一键)

放在 `scripts/scan_blind_spots.sh`:

```bash
#!/bin/bash
echo "=== 已装未用工具扫描 ==="
echo "--- 1. venv 命令 ---"
ls ~/.hermes/hermes-agent/venv/bin/ 2>/dev/null | grep -vE "^(python|pip|setuptools|wheel|easy_install)" | wc -l
echo "--- 2. 0 用 skill ---"
python3 -c "
import json
try:
    d = json.load(open('/Users/aimac/.hermes/skills/.usage.json'))
    print(sum(1 for v in d.values() if v.get('uses', 0) == 0), '个 0 用')
except: print('无 usage.json')
"
echo "--- 3. MCP server 状态 ---"
hermes mcp list 2>/dev/null | tail -10
echo "--- 4. Orphan 进程 ---"
ps aux | grep -E "mcp-|npx " | grep -v grep | wc -l
```

## 6. 真实盲区案例 (6/5 抓到)

- `/opt/homebrew/bin/searxng` — MCP server, 默认接 searx.party
- `ddgs` (9.14.2) — Python CLI 库
- `duckduckgo_search` — Python 库 (跟 ddgs 是同一个作者)
- `firecrawl` — 抓取库 (有 cache 在用)
- `playwright` / `selenium` — 浏览器自动化 (没用, Chrome 9333 走 CDP)
- 4 个孤儿 `mcp-searxng` 进程 (没接进 hermes config)

**教训**: 装了 ≠ 知道用法。要让 hermes 定期扫, 把盲区暴露给用户, 让用户决定激活哪些。
