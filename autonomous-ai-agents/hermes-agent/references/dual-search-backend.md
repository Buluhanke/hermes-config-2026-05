# 双搜索后端配置（Bocha + Firecrawl）


## 架构

web_search 支持多个后端，通过 `config.yaml` 的 `web.backend` 控制：

```yaml
web:
  backend: bocha      # 当前默认：博查（先用完3个月免费额度）
```

自动检测优先级：Firecrawl → Bocha → Parallel → Tavily → Exa

## 当前配置

| 后端 | 免费额度 | 有效期 | 当前角色 |
|------|---------|--------|---------|
| Bocha | 1000次 | 3个月（2026-05 ~ 2026-08） | ✅ 主力 |
| Firecrawl | 500次 | 永不过期 | ⏸ 备用 |

## 切换命令

```bash
# 切到 Firecrawl
hermes config set web.backend firecrawl

# 切回 Bocha
hermes config set web.backend bocha
```

## 额度状态

- Bocha: 1000次免费试用包（需在控制台手动领取，不领返回403）
- Firecrawl: 500次一次性，用完需付费（Hobby $20/月=3000次）
- 两者都不依赖代理，国内直连可用

## 注意

- Firecrawl 免费额度永久有效，建议先用 Bocha（有3个月期限）
- 博查补丁在 `web_tools.py`，Hermes 更新后需重打
- 博查 API 响应格式：`data.webPages.value[{name, url, snippet, siteName}]`
- Firecrawl API 响应格式：`data[{url, title, description}]`
