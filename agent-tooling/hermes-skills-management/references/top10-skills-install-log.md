# 打工人十大Skills安装记录

## 全部完成 ✅ 2026-07-11

| # | 技能名 | 安装路径 | 实际来源 | 状态 |
|---|--------|---------|---------|------|
| 1 | agent-browser | `skills-sh/101-skills/skills/agent-browser` | skills-sh | ✅ |
| 2 | find-skills | `skills-sh/vercel-labs/skills/find-skills` | skills-sh | ✅ |
| 3 | skill-creator | `skills-sh/anthropics/skills/skill-creator` | skills-sh | ✅ |
| 4 | creative-ideation | `official/creative/creative-ideation` | official | ✅ |
| 5 | brainstorming | → creative-ideation 代替 | - | ✅ |
| 6 | minimax-docx | `skills/minimax-docx` | MiniMax-AI/skills | ✅ |
| 7 | minimax-pdf | `skills/minimax-pdf` | MiniMax-AI/skills | ✅ |
| 8 | minimax-xlsx | `skills/minimax-xlsx` | MiniMax-AI/skills | ✅ |
| 9 | ppt-generation | `skills/public/ppt-generation` | bytedance/deer-flow | ✅ |
| 10 | humanizer-zh | `op7418/humanizer-zh` | GitHub raw | ✅ |
| 11 | write-product-spec | `.agents/skills/write-product-spec` | warpdotdev/common-skills | ✅ |
| 12 | ui-prompt-generator | `skills-sh/zinohome/cozyengine/ui-prompt-generator` | skills-sh | ✅ |
| 13 | avoid-ai-writing | `conorbronsdon/avoid-ai-writing` | GitHub raw | ✅ |

## 新技能发现（2026-07-11）

| 技能 | Stars | 特点 | 结论 |
|------|-------|------|------|
| avoid-ai-writing | ⭐2.2K | 49个AI写作模式，v3.15活跃，多平台通用 | **推荐安装**，比 humanizer-zh 更全面 |
| OfficeCLI | ⭐14.3K | Word/Excel/PPT 全能 CLI，无需 Office 安装 | 非 SKILL.md 格式，是二进制 CLI，用 `brew install officecli` 独立使用 |

## 安装方法

### 优先顺序
1. `hermes skills install skills-sh/<owner>/<repo>/<skill-name> --force`
2. `hermes skills install official/<category>/<skill-name> --force`
3. 直接下载 SKILL.md（当所有 CLI 方式都超时）

### 直接下载示例（已验证）
```bash
# avoid-ai-writing (Python urllib 最稳)
python3 -c "
import urllib.request, os
url = 'https://raw.githubusercontent.com/conorbronsdon/avoid-ai-writing/main/SKILL.md'
path = '/Users/aimac/.hermes/skills/avoid-ai-writing/SKILL.md'
os.makedirs(os.path.dirname(path), exist_ok=True)
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=15) as r:
    with open(path, 'wb') as f: f.write(r.read())
"
```

## 路径规律（踩坑总结）

- skills-sh 标识符路径 ≠ GitHub 实际路径，需 web_search 二次确认
- `skills-sh/<owner>/<repo>/<skill>` 中 `<repo>` 常是复数（如 `skills`）而非 skill 名本身
- `.agents/` 前缀常被忽略（warpdotdev 用 `.agents/skills/` 而非 `skills/`）
- `hermes skills install --source skills-sh` 报错 `unrecognized arguments`，skills-sh 格式不需要 `--source`
- curl exit code 56 = libcurl 读超时，改用 `execute_code` + Python urllib
