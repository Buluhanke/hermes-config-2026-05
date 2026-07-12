# AnySearch Skill 研究笔记

来源：https://github.com/anysearch-ai/anysearch-skill（4,049 ⭐，Apache-2.0，2026-04 上线）

## 核心架构：多 Runtime CLI Skill 模式

AnySearch skill 不是单一脚本，而是**多 runtime CLI 入口**：

```
anysearch_skill/
  SKILL.md                    ← 元数据 + 使用说明
  runtime.conf                ← 平台检测结果缓存（Command/Python path）
  scripts/
    anysearch_cli.py         ← Python runtime（需 requests 库）
    anysearch_cli.js          ← Node.js runtime（无外部依赖）
    anysearch_cli.sh          ← Bash runtime（需 jq + curl）
    anysearch_cli.ps1         ← PowerShell runtime
```

**平台检测逻辑**（优先级：Python > Node.js > Shell）：
- 检测 `<skill_dir>/runtime.conf` 存在 → 直接读 `Command` 字段，跳过检测
- 不存在 → 按优先级探测可用 runtime，写入 `runtime.conf` 缓存

**Credential 注入**（API key 管理）：
```yaml
credentials:
  - name: ANYSEARCH_API_KEY
    required: false
    description: "API key for higher rate limits. Anonymous access available."
    storage: ".env file, environment variable, or --api_key CLI flag"
```

Key 优先级：`--api_key` > `.env` > 环境变量 > 匿名访问

## Frontmatter Schema 扩展

标准 Hermes skill frontmatter 只有 `name`/`description`。AnySearch 的扩展版：
```yaml
---
name: anysearch
description: Real-time search engine supporting...
version: 2.1.0          # 版本号
authors:                # 作者列表
  - AnySearch Team
credentials:            # 凭证字段（API key 等）
  - name: ANYSEARCH_API_KEY
    required: false
    description: "..."
    storage: ".env file, environment variable, or --api_key CLI flag"
---
```

**对 skill harvesting 的启发**：评估一个 skill 时，同步记录它的 frontmatter schema 复杂度，判断落地成本。

## 接入方式矩阵

| 方式 | 协议 | 备注 |
|------|------|------|
| SKILL.md | Skill 协议 | `anysearch-skill` 仓库 |
| MCP Server | JSON-RPC 2.0 over Streamable HTTP | `anysearch-mcp-server` 仓库 |
| REST API | `api.anysearch.com/v1/...` | 底层都是这个 |

## 功能覆盖判断（决策框架）

**已有 `web_search_plus` + `web_extract_plus` 时，还需不需要装 AnySearch？**

判断标准：
1. **是否有垂直领域专项**（金融/学术/安全/法律/代码等结构化搜索）？→ AnySearch 有 23 个垂直领域
2. **是否有统一 API 中间层价值**（多引擎聚合、统一输出格式）？→ 当前 Hermes 已有类似路由
3. **API key 管理是否更优**？→ AnySearch 的 credential 注入模式更规范

结论：AnySearch 的多 runtime CLI skill 架构值得借鉴（落地 skill 时参考其 `runtime.conf` 机制），但功能层面与现有 Hermes 工具重叠，不需安装。

## 安装命令（测试用）
```bash
curl -L -o /tmp/anysearch-skill.zip https://github.com/anysearch-ai/anysearch-skill/archive/refs/heads/main.zip
```
