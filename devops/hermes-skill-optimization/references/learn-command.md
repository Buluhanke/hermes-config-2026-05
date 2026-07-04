# `/learn` Slash Command — 实战 SOP (v0.17.0+)

**来源**: Hermes Agent v0.17.0 (2026.6.19 release) 官方 docs

---

## 这是什么

`/learn` 是 Hermes Agent 的内置 slash command, 把**任何可描述的 source** 转换成**可复用的 SKILL.md**, 无需手写 frontmatter 或章节结构。

**底层调用**: `skill_manage` tool → 受 write-approval gate 约束 → 写入 `~/.hermes/skills/<name>/SKILL.md`

**可用平台**: CLI / TUI / messaging gateway (Telegram/Discord/QQBot 等) / Dashboard (有 "Learn a skill" 按钮)

---

## 四类 Source (官方文档分类)

### 1. URL — 在线文档/文章
```bash
/learn https://docs.example.com/api/quickstart
/learn https://hermes-agent.nousresearch.com/docs/user-guide/features/skills
```
- 适用: 官方文档, 博客教程, API reference, 论文 PDF (extract 后)
- 优势: source URL 自动嵌入 SKILL.md frontmatter, 后续可追源
- 注意: URL 必须 public 可访问 (无 auth wall)

### 2. 本地目录 — 已有代码/文档
```bash
/learn the REST client in ~/projects/acme-sdk, focus on auth + pagination
```
- 适用: 本地 SDK, 已读过的源码目录, 公司内部文档目录
- 优势: 自动读 README + sample + 关键文件, 提炼核心模式
- 注意: 目录不能太大 (>1000 文件会超时), 用 `focus on X` 限定范围

### 3. 对话工作流 — 当前会话里刚做的事
```bash
/learn how I just deployed the staging server
```
- 适用: 本次会话刚跑通的工作流, 想沉淀下来
- 优势: agent 从上下文提炼步骤, 不需要再写一遍
- 注意: 适合"一次性跑通, 想以后复用"的场景

### 4. 纯文字 — 任意描述
```bash
/learn filing an expense: open the portal, New > Expense, attach the receipt, submit
```
- 适用: 内部流程, 用户口述的步骤, 没有 source 链接的工作流
- 优势: 最低成本, 直接写
- 注意: 描述要具体到步骤级别, "怎么报销" 不够, "打开 X 门户 → 新建 → 选 X → 提交" 才够

---

## vs 手写 SKILL.md 的对比

| 维度 | 手写 `skill_manage create` | `/learn` |
|---|---|---|
| 思考成本 | 想 frontmatter / 章节 / 触发词 | 0 (house standards 自动应用) |
| 一致性 | 跨 skill 不一致 (我之前写过的就格式混乱) | 标准 ≤60-char description + 章节顺序 |
| 引用追踪 | 手动加链接 | 自动从 URL 嵌入 |
| 适用场景 | 高度定制的内部 skill | 通用知识/工作流固化 |
| 写完速度 | 5-10 分钟 | 30 秒 |
| 适用频率 | 低 (一次性深度 skill) | 高 (任何新知识都可固化) |

**结论**: 我之前 100% 走"手写"路径是低效的. 默认应该 `/learn`, 只有需要高度定制 (e.g. 自定义 frontmatter 元数据, 跨平台特殊处理) 时才手写.

---

## 实际命令模板

### 模板 A — 从官方 docs 学
```bash
# Step 1: 读文档
web_extract https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp
# Step 2: 提炼成 skill
/learn https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp
# Step 3: 验证
ls ~/.hermes/skills/mcp/SKILL.md  # 注意命名可能跟 URL 末段不一致
skill_view name=mcp
```

### 模板 B — 从刚跑通的工作流沉淀
```bash
# Step 1: 完成工作流 (e.g. 部署 staging)
/learn how I just deployed the staging server with helm + kubectl rollout
# Step 2: 验证
ls ~/.hermes/skills/staging-deploy/SKILL.md
```

### 模板 C — 从纯口述步骤固化
```bash
/learn weekly team sync: 1) read last week notes 2) update roadmap 3) call team channel 4) write summary
```

---

## 验证清单 (写完必走)

1. **存在性**: `ls ~/.hermes/skills/<name>/SKILL.md` 存在
2. **内容完整**: `head -50 <SKILL.md>` 有 frontmatter (name/description/version) + "When to Use" + "Procedure" + "Pitfalls" + "Verification" 章节
3. **触发词覆盖**: SKILL.md 里的 triggers 覆盖日常使用场景
4. **可加载**: `hermes chat --toolsets skills -q "load <name> skill"` 能正常返回内容
5. **可调用**: 在 prompt 里说 "use <name> skill" 能触发对应行为

---

## 已知坑 (2026-07-01)

- **URL 末段命名**: 跟 `hermes skills install` 同样的问题 (见 SKILL.md pitfall #8) — URL 末段可能不是 skill 真实名字. 装完 `ls ~/.hermes/skills/` 检查实际目录名, 不对就 `mv` 修正
- **`/learn` 不读二进制**: PDF/图片不能直接学, 要先 `web_extract` 转 markdown 再喂
- **嵌套 source**: 不能 `/learn <a-skill-that-uses-/learn>` (递归依赖), 走手写
- **触发词覆盖**: 自动生成的触发词不一定覆盖你日常用语, 写完自己 grep 验证 + patch

---

## 关联

- SKILL.md pitfall #10 — 主条目
- `hermes-skill-optimization` 整体 SOP — `/learn` 是三条路径之一 (Hub install / 手写 / `/learn`)
- `idle-learning-rounds` — 4 方向扫描找到新知识后, 可用 `/learn` 固化 (而非只写日志)