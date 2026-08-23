---
name: anysearch
description: "垂直领域搜索 + 通用搜索统一接口。触发: 金融数据查询/学术搜索/安全情报/批量并行搜索/URL内容提取。与 web_search_plus 是互补关系，后者覆盖通用搜索，前者提供23个垂直领域结构化数据。"
version: "1.0.0"
authors:
  - "AnySearch Team (skill adapted for Hermes)"
credentials:
  - name: ANYSEARCH_API_KEY
    required: false
    description: "已配置 .env 文件（rate_limit:20），配额用尽可换 key。免费获取: https://anysearch.com/console/api-keys"
    storage: "~/.hermes/skills/anysearch/.env"
setup_needed: false
api_key_configured: true
---

## Overview

AnySearch 是统一实时搜索服务，支持通用搜索 + 23 个垂直领域 + 并行批量 + URL内容提取。对 Hermes 来说，核心价值是**垂直领域结构化数据**（金融行情/财务数据/学术论文/CVE漏洞等），这是现有 `web_search_plus` 做不到的。

**无需安装任何依赖**——直接用 Python CLI，requests 已在 Hermes venv 里。

## Trigger Conditions

**硬路由规则**（直接执行，不问用户）：

| 查询类型 | 走 anysearch 命令 |
|---------|-----------------|
| 股票行情（AAPL/NVDA/贵州茅台） | `batch_search` 并行查多只 |
| 宏观经济（GDP/CPI/利率） | `search` + `finance.macro` |
| 学术论文/arXiv/DOI | `search` + `academic` domain |
| CVE漏洞/安全情报 | `search` + `security.cve` |
| 多股并行查询（>1只） | `batch_search` 一次完成 |
| 混合任务（金融+通用） | `anysearch batch` 为主 + `web_search_plus` 补 |

**通用搜索用 web_search_plus**：新闻/百科/常识/非结构化信息

## Trigger Conditions

以下场景优先使用 anysearch 而非 web_search_plus：
1. **金融数据**：股票行情(AAPL/NVDA)、财务指标、宏观经济(GDP/CPI)
2. **安全情报**：CVE漏洞、IP威胁情报、专利查询
3. **学术研究**：arXiv论文、DOI查询
4. **并行批量**：多个独立查询一次 API 调用完成
5. **URL内容提取**：将网页转为 Markdown（比浏览器更轻量）

## Skill Directory
```
/tmp/anysearch-skill/anysearch-skill-main/
```

## CLI Entry Point
```bash
CMD="python3 /tmp/anysearch-skill/anysearch-skill-main/scripts/anysearch_cli.py"
```

## Commands

### 1. 通用搜索（通用场景，优先级低于垂直搜索）
```bash
$CMD search "AI search trends 2026" --max_results 5
```

### 2. 垂直领域搜索（金融/学术/安全等，先查子域再搜索）
```bash
# 先查子域
$CMD get_sub_domains --domain finance

# 股票行情示例
$CMD search "AAPL" \
  --domain finance \
  --sub_domain finance.quote \
  --sdp "type=stock,symbol=AAPL,cn_code=" \
  --max_results 3

# 宏观经济示例
$CMD search "China GDP" \
  --domain finance \
  --sub_domain finance.macro \
  --sdp "type=gdp,period=2y" \
  --max_results 3

# 金融新闻示例
$CMD search "NVDA earnings" \
  --domain finance \
  --sub_domain finance.news \
  --sdp "type=stock,symbol=NVDA" \
  --max_results 3

# CVE漏洞查询
$CMD search "CVE-2026" \
  --domain security \
  --sub_domain security.cve \
  --sdp "query=CVE-2026" \
  --max_results 5
```

### 3. 并行批量搜索（多个独立查询一次完成）
```bash
# ⚠️ 匿名模式下 batch_search 可能连接失败，配 API key 可解决
# ⚠️ batch_search 命令不接受 --max_results 参数（--max_results 仅用于 search 命令）
$CMD batch_search --queries '[{"query":"NVDA","domain":"finance","sub_domain":"finance.quote","sub_domain_params":"type=stock,symbol=NVDA,cn_code="},{"query":"TSLA","domain":"finance","sub_domain":"finance.quote","sub_domain_params":"type=stock,symbol=TSLA,cn_code="}]'
```

### 4. URL 内容提取
```bash
$CMD extract "https://www.anysearch.com/about"
```

## Vertical Domains（23个）

| Domain | 内容 |
|--------|------|
| finance | 股票/宏观/财务/新闻/日历 |
| academic | arXiv/DOI/学术搜索 |
| security | CVE/威胁情报/IP/漏洞 |
| legal | 判例/法规/合同 |
| code | GitHub/代码搜索 |
| travel | 航班/酒店/旅游 |
| health | 医疗/药物/健康 |
| gaming | 游戏/电竞 |
| film | 电影/影视数据 |
| business | 商业/公司数据 |
| energy | 能源/油价 |
| environment | 环境/气候数据 |
| agriculture | 农业/农产品 |
| resource | 自然资源 |
| social_media | 社交媒体 |

## API Key 配置（如需更高限流）
```bash
# 获取免费 key: https://anysearch.com/console/api-keys
export ANYSEARCH_API_KEY=as_sk_xxxxx
```

## 安装位置
Skill 文件在 `/tmp/anysearch-skill/anysearch-skill-main/`，已通过以下命令下载：
```bash
cd /tmp && curl -L -o anysearch-skill.zip https://github.com/anysearch-ai/anysearch-skill/archive/refs/heads/main.zip && unzip -q anysearch-skill.zip -d anysearch-skill
```

## Known Limitations
1. 匿名模式下 batch_search 偶发连接错误（服务器限流），配 key 可解决；替代：sequential 多次调用
2. 垂直搜索需严格按 `get_sub_domains` 返回的 params 传参，漏传 required param 会报验证错误
3. 不支持敏感查询（查询会被送往 api.anysearch.com）

## Pitfalls

### YAML Frontmatter 格式错误（Python 3.14 严格模式）
**症状**：`yaml.safe_load` 报 `ParserError: expected '<document start>', but found '<scalar>'`
**根因**：SKILL.md frontmatter 中 `version: 1.0.0`（裸标量）在 Python 3.14 的 yaml 库中解析失败
**修复**：所有非布尔/数字标量值必须加双引号
```yaml
# 错误 ❌
version: 1.0.0
authors:
  - AnySearch Team

# 正确 ✅
version: "1.0.0"
authors:
  - "AnySearch Team"
```

## Verified Outputs
实际返回格式示例、命令错误记录、API 注册方法 → `references/verified-outputs.md`
