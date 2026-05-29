# Web搜索后端配置（2026-05-29）

## 现状

- `web.backend: ddgs` ✅ 可用
- `web.search_backend: ddgs` ✅ 可用
- `web.extract_backend: ddgs` ✅ 已从firecrawl切换

## 教训

**Firecrawl 需要付费API**，注册送额度但长期免费不可用。
发现过程：装了firecrawl-py模块，但没付费API key所以用不了。

**原则**：web backend优先用ddgs（本地免费），不要默认用需要API key的服务。

## 验证命令

```bash
python3 -c "from ddgs import DDGS; d=DDGS(); print(list(d.text('test', max_results=1)))"
```

## 相关配置

```yaml
web:
  backend: ddgs
  search_backend: ddgs
  extract_backend: ddgs  # 不是firecrawl（需付费）
```
