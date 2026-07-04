# Hermes Skill 深层整理方案（2026-06-10 00:14）

## 摸清的现状

| 指标 | 数据 |
|---|---|
| 物理 SKILL.md | 199 |
| registry 收录 | 198（差1个 = `humanizer/SKILL.md` 没 description 的孤儿副本）|
| 一级目录 | 75 个（30 个单 skill 目录 + 12 个空目录 + 33 个有 ≥2 skill）|
| 路径深度 ≥3 | 11 个（含 `research/last30days-skill-main/skills/last30days/` 4 层）|
| 父子重名 | 17 处（如 `vision/` 父目录 vs `vision/hermes-ocr` 子目录；`mattpocock/` 父目录 vs `mattpocock/diagnose`）|
| name 包含关系冲突 | 11 对（vision ⊃ hermes-vision-agent/vision-cache/...）|

## 4 大问题

1. **目录污染**：外部 skill（BytesAgain vision/）占用了一级目录名，导致分类容器被破坏
2. **嵌套路径**：git clone 出来的 last30days 整包占 4 层目录
3. **孤儿副本**：humanizer 装了 2 份
4. **空目录 12 个**：cross-platform-awareness/cua-driver/diagramming/domain/... 等没清理

## 整理方案（3 步）

### 第 1 步：清理重复/孤儿（风险：低）

- **删 `humanizer/SKILL.md`**（孤儿的旧版本，registry 收录的是 `creative/humanizer/`）
- **删 12 个空目录**

### 第 2 步：3 层分类 frontmatter（风险：低）

给每个 skill 的 SKILL.md frontmatter 加 3 个字段：

```yaml
l1: 🌐联网获取知识          # 任务场景
l2: search-web                # 能力领域
l3: specific                  # core/automation/specific
```

**L1（12 类任务场景）**：
- 🌐联网获取知识 / 🤖 AI站点对话 / 🖥浏览器桌面控制 / 📝编程工程化 / 🧠记忆自我进化 / 💬通讯消息 / 🎨创作设计 / 📊数据ML / 🛠运维部署 / 📚文档笔记 / 🛒采购电商 / 🎮娱乐游戏

**L2（13 类能力领域）**：browser-cdp / vision-ocr / ai-sites / search-web / code-engineering / memory-fact / messaging / creative-art / data-ml / macos-ops / productivity / external-services / hermes-internals

**L3（3 类生命周期）**：core / automation / specific

### 第 3 步：路由索引（关键）

- 在 skill_registry.py 加 `route <query>` 命令 — 按 L1 分组找 skill
- 更新 `using-agent-skills/SKILL.md` 加完整 3 维索引表

## 我会做的事

### 立即（自动）
1. ✅ 摸清现状（已完成）
2. ✅ 找到真问题（不是分类缺失，是 4 大具体问题）
3. ⏳ 第 1 步：清孤儿 + 空目录
4. ⏳ 第 2 步：给每个 skill 加 l1/l2/l3 字段
5. ⏳ 第 3 步：更新 skill_registry.py 加 `route` 命令
6. ⏳ 更新 using-agent-skills 加 3 维路由表

### 不动
- 物理目录结构（保留现有嵌套，用户已经习惯了）
- 任何 SKILL.md 的内容（只加 frontmatter 3 字段）
- 任何模型配置

## 验证清单

- [ ] `python3 skill_registry.py refresh` → 198 个 skill 全部收录
- [ ] `python3 skill_registry.py route "搜个资料"` → 返回 L1=🌐联网获取知识的所有 skill
- [ ] `python3 skill_registry.py categories` → 按 L1 列出 12 个分组
- [ ] `skill_view karpathy-guidelines` → 仍能正常加载
- [ ] `python3 ~/.hermes/skills/vision/hermes-ocr/scripts/ocr.py read <png>` → OCR 仍能用

## 时间预估

- 第 1 步：1 分钟（10 个 rm）
- 第 2 步：10 分钟（198 个 SKILL.md 加字段）
- 第 3 步：5 分钟（改 registry 加 route 命令 + 改 using-agent-skills）

总计 ~20 分钟，自动跑完汇报。