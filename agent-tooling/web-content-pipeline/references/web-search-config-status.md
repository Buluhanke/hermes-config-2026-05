# Web Search 配置现状 (2026-07-05 实测)

## 当前配置

```yaml
web:
  backend: ddgs           # 搜索后端
  search_backend: ddgs    # 同上
  extract_backend: firecrawl  # 提取后端（firecrawl key 失效中）
```

## 各 Provider 实测状态

| Provider | 状态 | 备注 |
|---|---|---|
| **ddgs (DuckDuckGo)** | ✅ 正常工作 | 搜索免费，无需 key，当前主力 |
| **Firecrawl** | ❌ 401 Unauthorized | API Key 失效，需到 firecrawl.dev 重新获取 |
| **Exa** | ✅ 实测有效 | key 存在但未接入配置 |
| **SearXNG (本地 Docker)** | ❌ 未运行 | local instance down |
| **SearXNG (公用)** | ❌ 已挂 | searx.party 不可用 |

## 已知可用免费 Tier (2026-07 调研)

| Provider | 免费额度 | 搜索 | 提取 | 备注 |
|---|---|---|---|---|
| **Firecrawl** | 500 credits/mo | ✅ | ✅ | key 失效，需换 key |
| **Tavily** | 1000 searches/mo | ✅ | ✅ | 需申请 key |
| **Exa** | 1000 searches/mo | ✅ | ✅ | key 已有效，未配置 |
| **Brave Search** | 2000 queries/mo | ✅ | ❌ | 需申请 key |
| **DDGS** | ✅ 免费 | ✅ | ❌ | 当前在用 |
| **Nous Portal Tool Gateway** | 订阅用户 | ✅ | ✅ | 无需 key，付费用户专用 |

## 切换 extract_backend 到 Exa (已有有效 key)

如需立即解决 extract 问题，配置:

```yaml
web:
  extract_backend: exa
```

同时建议去 firecrawl.dev 申请新 key 替换。

## 验证命令

```bash
# 测试 ddgs 搜索
hermes tools  # 看 web_search 状态

# 测试 Exa (Python)
python3 -c "
import urllib.request, json
req = urllib.request.Request('https://api.exa.ai/search',
    data=json.dumps({'query':'test','numResults':3}).encode(),
    headers={'Authorization': 'Bearer 767362d8-81a1-4991-bcae-6198c54871fe','Content-Type':'application/json'})
with urllib.request.urlopen(req, timeout=10) as r:
    d=json.load(r)
    print(f'Exa OK: {len(d[\"results\"])} results')
"
```

## 调研结论 (2026-07-05)

- DDGS 搜索够用，**无需更换**
- Exa key 有效，备用价值高
- Firecrawl key 失效是唯一中断点，需用户重新申请
- 浏览器控制层 CDP + AX 树已验证可用，无需换 browser-use
