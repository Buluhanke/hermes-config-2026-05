# GitHub 项目评估指南

当用户分享 GitHub 链接要求评估时，按以下流程：

## 1. 快速扫描（3秒看值不值得细看）

跳到页面获取基本信息即可停止，不用全量抓取：

| 指标 | 值得关注 | 小心 |
|------|---------|------|
| Stars | ≥100 有社区认可 | <10 可能个人项目 |
| 最后提交 | 近3个月内 | 1年+未更新 |
| Fork数 | 有社区活力 | 0 fork → 无人用 |
| Issues | 活跃讨论 | 全关/无人问津 |
| README | 完整文档 | 空/只有标题 |

## 2. 读取 README 的降级链

`web_extract`（首选，快且低开销）→ `browser_navigate`（当 web_extract 额度用完）→ **GitHub API MCP**（最可靠，无额度限制）

**推荐：直接使用 GitHub API MCP 工具 `mcp_github_get_file_contents`**
- 参数：`owner`, `repo`, `path`（如 `README.md`）
- 返回 base64 编码的 `content` 字段，tools 会自动解码
- 不需要 web 抓取额度，不受 Firecrawl 限制
- GitHub 未登录也有 60 req/h 免费额度

```python
# 用 execute_code 或 terminal 的 curl 方式
curl -s https://api.github.com/repos/owner/repo/readme \
  -H "Accept: application/vnd.github.raw+json"
```

## 3. 项目可行性判断

从 README 提取关键信息用于决策：

- **技术栈**：Python 项目看 pyproject.toml / requirements.txt；Node 看 package.json
- **依赖复杂度**：纯 Python 无系统依赖 → 直接部署；需要 Docker/数据库 → 先评估
- **文档完整性**：有配置指南/示例 → 好部署；只有代码无文档 → 谨慎
- **License**：MIT/Apache → 商用友好；GPL → 注意传染性
- **上游依赖**：是否依赖已停服的 API 或服务

## 4. 快速部署模式（Python 项目）

```bash
git clone https://github.com/owner/repo.git
cd repo
uv sync           # 自动创建 .venv + 安装依赖
cp .env.example .env   # 配置 API keys
# 编辑 config.json / 其他配置文件
uv run <script-name>   # 直接运行
```

注意点：
- `uv sync` 自动创建 `.venv`，不需要手动 `source venv/bin/activate`
- `uv run <script>` 自动使用项目的 `.venv` Python
- 配置验证可能要求完整字段（即使 `enabled: false` 也需要占位值）—— 看 pyproject.toml / 源码的 Config 类定义

## 5. 输出验证

运行后检查：
- 是否有退出码或报错
- 输出目录是否生成预期文件
- 实际 Token 消耗（如有 AI 调用）
- 输出的质量是否符合预期
