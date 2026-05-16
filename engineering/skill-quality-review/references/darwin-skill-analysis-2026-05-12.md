# darwin-skill Analysis (2026-05-12)

## Source
- GitHub: https://github.com/alchaincyf/darwin-skill
- 星标: 2.4k
- Fork: 281
- 作者: 花叔 (alchaincyf, Twitter @AlchainHust)
- 许可: MIT
- 最后更新: 2026-04-21（3周前）

## What It Does

把 Karpathy autoresearch 的「实验→测试→保留改进」循环搬到 Skill 优化领域。自动评估 SKILL.md 质量，提出改进，测试效果，只保留真实提升。

## 核心循环

```
评估（8维度评分） → 诊断最低维度 → 提出1个改进 → 编辑SKILL.md
→ 重新评估 → 新分>旧分? keep : revert → 生成成果卡片
```

## 8维度 Rubric

| 维度 | 权重 | 类型 |
|------|------|------|
| Frontmatter质量 | 8 | 结构 |
| 工作流清晰度 | 15 | 结构 |
| 边界条件覆盖 | 10 | 结构 |
| 检查点设计 | 7 | 结构 |
| 指令具体性 | 15 | 结构 |
| 资源整合度 | 5 | 结构 |
| 整体架构 | 15 | 效果 |
| 实测表现 | 25 | 效果 |

## 安装方式

```bash
npx skills add alchaincyf/darwin-skill
```

安装后 SKILL.md 在 `~/.claude/skills/darwin-skill/SKILL.md`。Hermes 路径在 `~/.hermes/skills/`，需要适配。

## GitHub连通性问题（本机）

这个网络 GitHub 443 超时，`npx skills add` 可能克隆失败。2026-05-12 尝试时成功克隆了（耗时较长），但无法保证下次还能成功。

如果装不上，用 skill-quality-review 的流程手动执行——8维度评分 + 测试prompt + 棘轮机制，效果一样。

## 与现有技能的关系

| Skill | 覆盖范围 | 互补说明 |
|-------|---------|---------|
| skill-vetter | 安全审查 | darwin关注质量，vetter关注安全，不重叠 |
| hermes-agent-skill-authoring | 怎么写 | darwin关注怎么优化，authoring关注怎么写 |
| skill-protocol | 格式规范 | darwin关注效果+迭代，protocol关注结构标准化 |
| skill-quality-review | 质量评审 | 本skill，将darwin思路适配到Hermes生态 |

## 值得借鉴的设计决策

1. **棘轮机制（ratchet）**：分数只升不降。git revert 而非 reset --hard，保留失败记录可追溯。
2. **独立评分**：用子 agent 评，避免「自己改自己评」的偏差。效果维度用带/不带 skill 的 A/B 测试。
3. **测试 prompt 先行**：评估前先设计测试用例，保证评估有依据、可复现。
4. **人在回路**：每个 skill 优化完展示 diff，等用户确认。不搞全自动。
5. **成果卡片**：生成视觉化结果卡片（SVG横幅），但不是必需品，Hermes可跳过。
