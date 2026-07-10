# 打工人十大Skills安装记录

## 已确认可安装 ✅

| # | 技能名 | 安装命令 | 状态 | 来源 |
|---|--------|---------|------|------|
| 1 | agent-browser | `hermes skills install skills-sh/101-skills/skills/agent-browser --force` | ✅ 已装 | skills-sh |
| 2 | find-skills | `hermes skills install skills-sh/vercel-labs/skills/find-skills --force` | ✅ 已装 | skills-sh |
| 3 | skill-creator | `hermes skills install skills-sh/anthropics/skills/skill-creator --force` | ✅ 已装 | skills-sh |
| 4 | creative-ideation | `hermes skills install official/creative/creative-ideation --force` | ✅ 已装 | official |
| 5 | brainstorming | 需另找安全源（obra源被block，sickn3源超时） | ⚠️ 待解决 | — |
| 6 | minimax-docx | GitHub直链超时 | ⚠️ 待解决 | MiniMax-AI/skills |
| 7 | minimax-pdf | GitHub直链超时 | ⚠️ 待解决 | MiniMax-AI/skills |
| 8 | minimax-xlsx | GitHub直链超时 | ⚠️ 待解决 | MiniMax-AI/skills |
| 9 | pptx-generator | GitHub直链超时 | ⚠️ 待解决 | MiniMax-AI/skills |
| 10 | humanizer-zh | `official/creative/humanizer` 存在于官方文档（待验证） | 🔍 待装 | official |
| 11 | product-spec-builder | Hub搜索未命中 | ❌ 需自建 | — |
| 12 | ui-prompt-generator | `hermes skills install skills-sh/zinohome/cozyengine/ui-prompt-generator --force` | ✅ 已装 | skills-sh |

## 安装失败诊断

### GitHub直链超时模式
- `github:MiniMax-AI/skills/minimax-docx` → 60s超时
- `github:MiniMax-AI/skills/minimax-pdf` → 60s超时
- `github:MiniMax-AI/skills/minimax-xlsx` → 60s超时
- `https://raw.githubusercontent.com/MiniMax-AI/skills/...` → 60s超时
- `skills-sh/vercel-labs/agent-skills/agent-browser` → 超时（但另一个路径成功）
- `skills-sh/sickn3/antigravity-awesome-skills/brainstorming` → 90s超时

### 被Block模式
- `skills-sh/obra/superpowers/brainstorming` → `BLOCKED — community source + dangerous verdict`

## 备选方案（待验证）

1. **brainstorming**: 尝试 `official/creative/creative-ideation`（已有，官方）作为替代
2. **MiniMax全家桶**: 网络恢复后重试；或找其他镜像源
3. **product-spec-builder**: 需要自己写 SKILL.md
4. **humanizer-zh**: 查 `official/creative/humanizer` 是否已装
