# 博查 (Bocha) 搜索后端补丁

向 Hermes 的 `web_tools.py` 添加博查 AI 作为 web search 后端。适用于 Firecrawl 不可用（无 API key）或国内网络不稳定的场景。

## 修改文件

`tools/web_tools.py`（Hermes 源码目录下）

## 修改清单 (4 处)

### 1. `_get_backend()` — 添加 bocha 到合法后端列表

```python
# 行的位置 ~128
configured = (_load_web_config().get("backend") or "").lower().strip()
if configured in ("parallel", "firecrawl", "tavily", "exa", "bocha"):  # ← 加 bocha
    return configured
```

### 2. `_get_backend()` — 添加 bocha 到自动检测候选

```python
# 约 ~136 行
backend_candidates = (
    ("firecrawl", _has_env("FIRECRAWL_API_KEY") or ...),
    ("bocha", _has_env("BOCHA_API_KEY")),  # ← 添加这行
    ("parallel", _has_env("PARALLEL_API_KEY")),
    ...
)
```

### 3. 添加 `_bocha_search()` 函数（插在 `_get_parallel_extract_client()` 的 `return results` 和 `web_search_tool()` 之间）

```python
# ─── Bocha Search ─────────────────────────────────────────────────────────────

def _bocha_search(query: str, limit: int = 5) -> dict:
    """Search using the Bocha AI API and return results as a dict."""
    from tools.interrupt import is_interrupted
    if is_interrupted():
        return {"error": "Interrupted", "success": False}

    api_key = os.getenv("BOCHA_API_KEY")
    if not api_key:
        raise ValueError(
            "BOCHA_API_KEY environment variable not set. "
            "Get your API key at https://bochaai.com"
        )

    logger.info("Bocha search: '%s' (limit=%d)", query, limit)
    resp = httpx.post(
        "https://api.bochaai.com/v1/web-search",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"query": query, "count": min(limit, 50), "freshness": "noLimit"},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    web_results = []
    pages = []
    if isinstance(data, dict):
        inner = data.get("data") or data
        webpages = inner.get("webPages") if isinstance(inner, dict) else {}
        if isinstance(webpages, dict):
            pages = webpages.get("value") or []

    for i, item in enumerate(pages):
        if isinstance(item, dict):
            web_results.append({
                "url": item.get("url", ""),
                "title": item.get("name", ""),
                "description": item.get("snippet", ""),
                "position": i + 1,
            })

    # Fallback: try flat list format (alternative API version)
    if not web_results and isinstance(data, dict):
        inner = data.get("data") or data
        if isinstance(inner, dict):
            pages = inner.get("list") or inner.get("results") or []
            for i, item in enumerate(pages):
                if isinstance(item, dict):
                    web_results.append({
                        "url": item.get("url", ""),
                        "title": item.get("title", item.get("name", "")),
                        "description": item.get("summary", item.get("content", item.get("snippet", ""))),
                        "position": i + 1,
                    })

    return {"success": True, "data": {"web": web_results}}
```

### 4. `web_search_tool()` — 添加 bocha 调度分支

```python
# 约在 exa 分支之后
if backend == "bocha":
    response_data = _bocha_search(query, limit)
    debug_call_data["results_count"] = len(response_data.get("data", {}).get("web", []))
    result_json = json.dumps(response_data, indent=2, ensure_ascii=False)
    debug_call_data["final_response_size"] = len(result_json)
    _debug.log_call("web_search_tool", debug_call_data)
    _debug.save()
    return result_json
```

### 5. `_web_requires_env()` — 添加 `BOCHA_API_KEY`

```python
requires = [
    ...
    "BOCHA_API_KEY",  # ← 添加
]
```

## 使用方式

```bash
# 1. 配置 API key
echo 'BOCHA_API_KEY=your_key_here' >> ~/.hermes/.env

# 2. 可选：设为默认 backend
hermes config set web.backend bocha

# 3. 重启生效
hermes gateway restart
```

## 博查 API 说明

- 端点: `POST https://api.bochaai.com/v1/web-search`
- 认证: `Authorization: Bearer {key}`
- 请求体: `{"query": str, "count": int, "freshness": "noLimit"|"day"|"week"|"month"}`
- 响应格式: `{code:200, data: {webPages: {value: [{name, url, snippet, siteName, ...}]}}}`
  - 注意字段名: `name`(标题), `snippet`(摘要), `siteName`(网站名), `url`, `datePublished`
- 国内直连可用，无需代理

## ⚠️ 免费额度领取（铁律）

博查有免费试用套餐：**Web Search API 1000次/0元，有效期3个月**。但**不是自动生效的**——生成 API Key 后，新 key 没有绑定任何资源包，直接调用会返回 403：

```json
{"code":"403","message":"You do not have enough money or package quota"}
```

**必须手动领取免费试用资源包**：登录 https://open.bochaai.com → 控制台 → 资源包管理 → 领取"Web Search API 免费试用"。

领取路径也可以从官方帮助文档进入：`博查用户帮助文档` → `免费领取调用资源包`。

如果没有手动领取，千万不要说"免费额度用完了"或"需要充值"——先确认是否已领取免费试用包。

## 多后端协同使用策略

Firecrawl 和 Bocha 可同时配置，协同使用：

| 特性 | Firecrawl | Bocha |
|------|-----------|-------|
| 免费额度 | 500次一次性（**永不过期**） | 1000次，3个月有效期 |
| 注册赠送 | 注册即送，无需手动领取 | 需手动在控制台领取试用包 |
| 过期 | **无时间限制** | 3个月 |
| 国内访问 | 需代理 | 国内直连 |

**推荐策略：**
- 先吃 Bocha（1000次有3个月时效，先用完）
- 同时配置 Firecrawl（500次永不过期，保底用）
- 设置 `web.backend: bocha` 先用 Bocha
- 博查用完后切 `web.backend: firecrawl`
- 也可两个都不设 auto-detect，由代码自动选 Firecrawl（检测到 FIRECRAWL_API_KEY）或 Bocha

**修改 backend：**
```bash
hermes config set web.backend bocha    # 先吃波査
# 或用完后再改
hermes config set web.backend firecrawl # 切 Firecrawl
```

- **Hermes 更新后会覆盖此修改** — `hermes update` 重新安装源码会覆盖 `tools/web_tools.py`，补丁需要重打
- **`httpx` 已导入** — Hermes 的 `web_tools.py` 顶部已 `import httpx`，无需额外安装依赖
- **后端优先级** — 在自动检测中 bocha 排在 Firecrawl 之后、其他后端之前。设置 `web.backend: bocha` 可固定使用
