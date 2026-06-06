# anysearch CLI — 完整操作参考

## 安装位置
- Skill 目录: `~/.hermes/skills/anysearch/`
- CLI 路径: `~/.hermes/skills/anysearch/scripts/anysearch_cli.py` (Python 首选)
- 其他运行时: `.sh` (bash) / `.js` (Node.js) / `.ps1` (Windows PowerShell)
- 配置文件: `~/.hermes/skills/anysearch/runtime.conf` (Runtime: Python, Command: python3 .../anysearch_cli.py)

## 凭证
- **不需要 API key**（匿名访问可用，限速低）。
- 想提高限速：去 https://anysearch.com/console/api-keys 申请免费 key，写到 `~/.hermes/.env` 的 `ANYSEARCH_API_KEY=<key>`，或环境变量。
- 优先级：`--api_key` CLI > `.env` 文件 > 环境变量 > 匿名。

## 核心命令

### search — 通用搜索
```bash
python3 ~/.hermes/skills/anysearch/scripts/anysearch_cli.py search "query" --max_results 5
```
可选参数：
- `--max_results N` (默认 5)
- `--freshness day|week|month|year` (时效过滤)
- `--content_types web,news,code,doc,academic,data,image,video,audio`
- `--domain <name>` (垂直域，需先 `list_domains` 查 sub_domain)

**输出格式** (Markdown):
```
## Search Results (5 results, 10000ms)

### 1. Title
- **URL**: https://...
- > Description snippet...

### 2. ...
```

### batch_search — 并行批量
```bash
python3 ~/.hermes/skills/anysearch/scripts/anysearch_cli.py batch_search --queries '[{"query":"q1","max_results":3},{"query":"q2","max_results":3}]'
```
- 多个查询并发跑，**实测每个 ~10s**（顺序跑，不是真并行）
- 返回 Markdown, 每段以 `## Query N:` 开头

### extract — 全页内容提取
```bash
python3 ~/.hermes/skills/anysearch/scripts/anysearch_cli.py extract "https://example.com/page"
python3 ~/.hermes/skills/anysearch/scripts/anysearch_cli.py extract --url "https://example.com/page"
```
- 输出 Markdown
- **不要**加 `--format` 或 `--markdown` 参数（命令没有这个选项）

### list_domains — 列垂直域
```bash
python3 ~/.hermes/skills/anysearch/scripts/anysearch_cli.py list_domains
python3 ~/.hermes/skills/anysearch/scripts/anysearch_cli.py list_domains --domain finance
```
- 默认报"需要 --domain 或 --domains"（CLI 接口比 SKILL.md 描述的严格）
- 已知域：finance / academic / travel / health / code / geo / patent / stock / CVE / DOI / IATA

### doc — 离线文档（仅在不确定 CLI 用法时跑）
```bash
python3 ~/.hermes/skills/anysearch/scripts/anysearch_cli.py doc
```
- 本地操作，不发网络请求
- **不要**每次都跑——SKILL.md 已有 cheat sheet, 跑 doc 浪费 token

## 实测能力（2026-06-05 21:30）

| 场景 | 关键词 | 结果数 | 耗时 | 质量 |
|---|---|---|---|---|
| 中文电商 | "小米SU7 2026 价格" | 5 | 10s | 优（小米官网/网通社/太平洋/Udn 联合报）|
| 英文技术 | "Mac mini M4 24GB AI" | 3 | 10s | 优（Reddit/Apple/YouTube）|
| 英文车评 | "Tesla Model Y 2026 review" | 3 | 10s | 优（Car and Driver/Edmunds/YouTube）|
| 批量并发 | 2 问并发 | 4 (2+2) | 10s | OK |
| 提取 URL | (没测) | - | - | 待测 |

## 中文质量 vs ddgs

| 引擎 | "小米SU7" 测试 | 来源 |
|---|---|---|
| **anysearch** | 5 条全对路，4 国内站 + 1 英文 | 实测 ✅ |
| **ddgs** | 翻译成英文 "xiaomi su7"，返英文结果或低相关 | 6/5 文档记录 ⚠️ |

**结论**：中文搜索 anysearch 一边倒优势。

## 统一入口 search.py

**所有平台统一调这一个**：
```bash
python3 ~/.hermes/scripts/search.py "查询词" 5
```

内部自动路由：
- 含"趋势/热点/社媒/舆情/过去N天/月" → last30days
- 其余 → anysearch
- anysearch 挂了 → agg_search.py (ddgs)

不要每次直调 anysearch_cli.py，统一走 search.py。

## 不要做的事

- ❌ **不要**每次激活 anysearch 都跑 `doc`（浪费 token，SKILL.md 已有 cheat sheet）
- ❌ **不要**用 `extract --format markdown`（没有这参数，会报错）
- ❌ **不要**改 `~/.hermes/config.yaml` 的 `search_backend: ddgs` 为 anysearch（框架可能只认固定字符串，瞎改会崩）
- ❌ **不要**把 anysearch 和 multi_ask_v3 混（multi_ask_v3 是 6 站 AI 对话，不是搜索）

## 已知 bug / 限制

- `list_domains` 不带 `--domain` 报参数错（CLI 接口比文档严格，但不影响主流程）
- 批量 `batch_search` 实际是顺序跑（10s for 2 queries），不是真并行
- 匿名访问有 rate limit，跑太频繁可能被临时限速——加 API key 解决
