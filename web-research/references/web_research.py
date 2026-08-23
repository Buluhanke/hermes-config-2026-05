"""
web_research — 联网搜索与总结
搜索 → 提取 → 过滤 → 总结 → 缓存1小时

免费优先策略：
  有 MINIMAX_API_KEY → MiniMax 搜索
  有 SERPER_API_KEY  → Serper（2500次/月）
  有 TAVILY_API_KEY  → Tavily（1000次/月）
  否则               → Bing RSS（完全免费，无需key）
"""

import re, time, json
from typing import Optional

# ─── 缓存 ───────────────────────────────────────────────
_CACHE: dict = {}
_CACHE_TTL = 3600


def research(query: str, max_sources: int = 3) -> dict:
    """
    联网研究主函数。
    返回: {query, conclusion, sources, search_time_ms, cached}
    """
    cache_key = query.lower().strip()
    now = time.time()
    if cache_key in _CACHE:
        entry = _CACHE[cache_key]
        if now - entry["ts"] < _CACHE_TTL:
            r = entry["result"].copy()
            r["cached"] = True
            return r

    t0 = time.time()

    # Step 1: 搜索
    sources = _search(query, max_sources)
    if not sources:
        result = {
            "query": query,
            "conclusion": f"未找到关于「{query}」的相关信息",
            "sources": [],
            "search_time_ms": int((time.time() - t0) * 1000),
            "cached": False,
        }
        _CACHE[cache_key] = {"result": result, "ts": now}
        return result

    # Step 2: 提取正文（并发）
    sources = _extract_pages(sources)

    # Step 3: 过滤低质量
    sources = [s for s in sources if len(s.get("content", "")) > 50]

    # Step 4: 总结
    conclusion = _summarize(query, sources)

    result = {
        "query": query,
        "conclusion": conclusion,
        "sources": [
            {"title": s["title"], "url": s["url"], "relevance": s["relevance"]}
            for s in sources
        ],
        "search_time_ms": int((time.time() - t0) * 1000),
        "cached": False,
    }
    _CACHE[cache_key] = {"result": result, "ts": now}
    return result


# ─── 内部函数 ───────────────────────────────────────────

def _get_env(key: str) -> str:
    import os
    return os.environ.get(key, "")


def _search(query: str, max_results: int) -> list[dict]:
    """搜索：按优先级尝试各方案"""
    # 1. MiniMax 搜索（有 key 质量最高）
    key = _get_env("MINIMAX_API_KEY")
    if key:
        result = _search_minimax(query, max_results, key)
        if result:
            return result

    # 2. Serper（2500次/月免费）
    key = _get_env("SERPER_API_KEY")
    if key:
        result = _search_serper(query, max_results, key)
        if result:
            return result

    # 3. Tavily（1000次/月免费）
    key = _get_env("TAVILY_API_KEY")
    if key:
        result = _search_tavily(query, max_results, key)
        if result:
            return result

    # 4. Bing RSS（完全免费，无需key）
    return _search_bing_rss(query, max_results)


def _search_bing_rss(query: str, max_results: int) -> list[dict]:
    """Bing RSS 搜索（免费无需key）"""
    import xml.etree.ElementTree as ET
    import urllib.parse
    import subprocess

    encoded = urllib.parse.quote(query)
    url = f"https://www.bing.com/search?q={encoded}&format=rss&mkt=zh-CN"

    try:
        r = subprocess.run(
            ["curl", "-s", "-L", "--max-time", "10",
             "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
             url],
            capture_output=True, text=True, timeout=15,
        )
        raw = r.stdout
    except Exception:
        return []

    if not raw or len(raw) < 200:
        return []

    try:
        root = ET.fromstring(raw)
        items = root.findall(".//item")
        results = []
        for i, item in enumerate(items[:max_results]):
            title_el = item.find("title")
            link_el = item.find("link")
            desc_el = item.find("description")
            results.append({
                "title": (title_el.text or "").strip() if title_el is not None else "",
                "url": (link_el.text or "").strip() if link_el is not None else "",
                "snippet": _strip_html(desc_el.text or "") if desc_el is not None else "",
                "relevance": "高" if i == 0 else "中",
                "content": "",
            })
        return results
    except Exception:
        return []


def _search_serper(query: str, max_results: int, key: str) -> list[dict]:
    """Serper 搜索"""
    import subprocess, json as _json

    raw = subprocess.run(
        ["curl", "-s", "-X", "POST", "https://google.serper.dev/search",
         "-H", f"X-API-KEY: {key}",
         "-H", "Content-Type: application/json",
         "-d", _json.dumps({"q": query, "num": max_results})],
        capture_output=True, text=True, timeout=15,
    ).stdout

    try:
        data = _json.loads(raw)
        organic = data.get("organic", []) or []
        if not organic:
            return []
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("link", ""),
                "snippet": r.get("snippet", ""),
                "relevance": "高" if i == 0 else "中",
                "content": "",
            }
            for i, r in enumerate(organic[:max_results])
        ]
    except Exception:
        return []


def _search_tavily(query: str, max_results: int, key: str) -> list[dict]:
    """Tavily 搜索"""
    import subprocess, json as _json

    raw = subprocess.run(
        ["curl", "-s", "-X", "POST", "https://api.tavily.com/search",
         "-H", "Content-Type: application/json",
         "-d", _json.dumps({"api_key": key, "query": query, "max_results": max_results})],
        capture_output=True, text=True, timeout=15,
    ).stdout

    try:
        data = _json.loads(raw)
        results = data.get("results", []) or []
        if not results:
            return []
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("content", ""),
                "relevance": "高" if i == 0 else "中",
                "content": "",
            }
            for i, r in enumerate(results[:max_results])
        ]
    except Exception:
        return []


def _search_minimax(query: str, max_results: int, key: str) -> list[dict]:
    """MiniMax 内置搜索（质量最高）"""
    import urllib.request, json as _json

    payload = _json.dumps({
        "model": "MiniMax-Text-01",
        "messages": [
            {"role": "system", "content": "你是一个搜索助手。请根据用户问题返回3个最相关的网页搜索关键词，用于搜索引挚查询。只返回关键词，不要其他内容。"},
            {"role": "user", "content": f"用户问题：{query}\n请给出3个搜索关键词，用逗号分隔："},
        ],
        "max_tokens": 50,
        "temperature": 0,
    })

    req = urllib.request.Request(
        "https://api.minimax.chat/v1/text/chatcompletion_v2",
        data=payload.encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = _json.loads(resp.read().decode("utf-8"))
            keywords = data["choices"][0]["message"]["content"].strip()
    except Exception:
        return []

    # 用关键词调 Bing 搜索
    return _search_bing_rss(keywords, max_results)


def _extract_pages(sources: list[dict]) -> list[dict]:
    """并发抓取页面正文"""
    import concurrent.futures

    def fetch_one(src):
        content = _curl_extract(src["url"])
        return {**src, "content": content}

    with concurrent.futures.ThreadPoolExecutor(max_workers=min(3, len(sources))) as ex:
        return list(ex.map(fetch_one, sources))


def _curl_extract(url: str, timeout: int = 8) -> str:
    """curl 抓页面，取 <p> 段落"""
    import subprocess

    skip_hosts = ["google.com", "baidu.com", "bing.com", "sina.com", "weibo.com", "douyin.com"]
    if any(h in url for h in skip_hosts):
        return ""

    cmd = [
        "curl", "-s", "-L", "--max-time", str(timeout),
        "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "-H", "Accept-Language: zh-CN,zh;q=0.9",
        url,
    ]

    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 2)
        html = r.stdout
        if not html or len(html) < 200:
            return ""

        paragraphs = re.findall(r"<p[^>]*>(.*?)</p>", html, re.DOTALL)
        texts = [_strip_html(p) for p in paragraphs]
        meaningful = [t for t in texts if len(t) > 30][:8]
        return " ".join(meaningful)
    except Exception:
        return ""


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _summarize(query: str, sources: list[dict]) -> str:
    """总结：有 MiniMax key 则调用，否则返回摘要"""
    if not sources:
        return f"未找到关于「{query}」的相关信息"

    # 拼接内容
    parts = []
    total = 0
    for s in sources:
        c = s.get("content", "") or s.get("snippet", "")
        if c and total < 1500:
            parts.append(f"【{s['title']}】{c[:400]}")
            total += len(c)

    combined = "\n\n".join(parts)

    key = _get_env("MINIMAX_API_KEY")
    if key:
        conclusion = _call_minimax(query, combined, key)
        if conclusion:
            return conclusion

    # Fallback: 返回第一条有效摘要
    for s in sources:
        c = s.get("content", "") or s.get("snippet", "")
        if len(c) > 50:
            return c[:300]
    return f"关于「{query}」找到了一些信息"


def _call_minimax(query: str, content: str, api_key: str) -> str:
    """调 MiniMax 总结"""
    import urllib.request

    prompt = f"""基于以下搜索结果，回答用户问题。要求：3句话以内给出明确结论，不确定的内容说"不确定"。

问题：{query}

搜索结果：
{content[:3000]}

回答："""

    payload = json.dumps({
        "model": "MiniMax-Text-01",
        "messages": [
            {"role": "system", "content": "你是一个专业的搜索结果总结助手。"},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 250,
        "temperature": 0.3,
    })

    req = urllib.request.Request(
        "https://api.minimax.chat/v1/text/chatcompletion_v2",
        data=payload.encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"].strip()
    except Exception:
        return ""
