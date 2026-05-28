# GitHub API 搜索（Firecrawl 降级方案）

Firecrawl web_search 额度耗尽时（402 Payment Required），GitHub API 是最可靠的免费替代方案。

## 基础用法

```python
# 按 stars 排序搜索
import subprocess, json
cmd = 'curl -s "https://api.github.com/search/repositories?q=KEYWORD&sort=stars&order=desc&per_page=10"'
r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
data = json.loads(r.stdout)
for item in data['items']:
    print(f"{item['stargazers_count']:>5}★ {item['full_name']:<40} {(item.get('description','') or '')[:100]}")
```

## 已验证可获取的关键信息

| 搜索类型 | 示例 | 获取内容 |
|---------|------|---------|
| 按 stars 排序 | `q=GUI+agent+screen&sort=stars` | 热门项目排行 |
| 特定领域 | `q=CAPTCHA+solver+python` | 验证码工具 |
| 精确搜索 | `q=OmniParser+screen&in:name` | 精确匹配项目名 |
| 按更新时间 | `sort=updated&order=desc` | 最新活跃项目 |

## 已验证成功案例（2026-05-29）

- OmniParser ★24,823 — `microsoft/OmniParser`
- CloakBrowser ★22,036 — `CloakHQ/CloakBrowser`（仅Linux/Windows，无macOS ARM64）
- Camofox ★5,929 — `jo-inc/camofox-browser`（macOS友好）
- NopeCHA ★10,334 — `NopeCHALLC/nopecha-extension`（Python SDK ★1,647）
- patchright ★3,326 — `Kaliiiiiiiiii-Vinyzu/patchright`
- nodriver ★4,286 — `ultrafunkamsterdam/nodriver`
- OS-Copilot ★1,772 — `OS-Copilot/OS-Copilot`

## 获取项目详情

```python
# 获取单个仓库信息
cmd = 'curl -s "https://api.github.com/repos/OWNER/REPO"'
# 获取 README
cmd = 'curl -s "https://api.github.com/repos/OWNER/REPO/readme"'
# 获取 releases
cmd = 'curl -s "https://api.github.com/repos/OWNER/REPO/releases?per_page=3"'
```

## 限制

- 未认证 API 有速率限制（60次/小时），但足够深度进化单次使用
- GitHub Search API 有结果上限（前1000条）
- `repo/contents` 读取需要每个文件单独请求，大仓库较慢
