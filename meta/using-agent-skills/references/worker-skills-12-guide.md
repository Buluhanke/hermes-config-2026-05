# 打工人必装技能包 — 安装指南

> 来源：用户整理的12个技能，2026-06-03
> 背景：Mac mini M4 24GB，当前空闲内存 **2.62GB**，72个skills已占189MB磁盘

---

## 三类技能对比

| 类别 | 数量 | 建议 |
|------|------|------|
| 新手必装 | 4 | ⭐⭐⭐ 按需装 |
| 开发工作 | 4 | ⭐ 与现有skills重叠，多已具备 |
| 文字工作 | 4 | ⭐⭐ 轻量，按需装 |

---

## 新手必装（4个）

### 1. agent-browser
**推荐度**：⬜ 不装
**理由**：与现有 `hermes-rpa` + `browser_cdp` 功能高度重叠。Hermes已有Chrome控制能力，agent-browser无额外价值。
**结论**：跳过

### 2. find-skills
**推荐度**：⭐⭐⭐ **必装**
**理由**：自然语言查找技能，能激活现有72个skills。不装等于浪费技能库。
**安装**：建议最先装

### 3. skill-creator
**推荐度**：⭐⭐⭐ **必装**
**理由**：任务→技能转换工具。Hermes是"会成长的Agent"，skill-creator是把经验固化的核心工具。
**注意**：当前未安装（72个skills中不存在）

### 4. deep-research
**推荐度**：⭐⭐ 按需装
**理由**：真正做深度研究时再装，体积较大。
**时机**：有研究任务时

---

## 开发工作（4个）

### 1. product-spec-builder
**推荐度**：⭐ 有替代
**理由**：planning类已有 `planning-and-taYOUR_API_KEY`，spec-driven 类已有 `spec-driven-sourcing`
**结论**：功能重叠，跳过

### 2. ui-prompt-generator
**推荐度**：⬜ 不装
**理由**：现有 skills 中已有 `design-md`、`popular-web-designs` 等UI相关skill
**结论**：跳过

### 3. ui-ux-pro-max
**推荐度**：⭐ 有替代
**理由**：与 `popular-web-designs` 重叠，后者提供54个真实设计系统参考
**结论**：跳过

### 4. dev-builder
**推荐度**：⭐ 有替代
**理由**：已有 `claude-code`、`codex`、`opencode` 等编程skill
**结论**：跳过

---

## 文字工作（4个）

### 1. brainstorming
**推荐度**：⭐⭐ **推荐装**
**理由**：结构化头脑风暴框架，轻量，可与 `find-skills` 配合使用
**安装建议**：轻量技能，放心装

### 2. minimax办公套件
**推荐度**：⭐⭐ 按需装
**理由**：文档/PPT/表格增强。要用时再装。
**时机**：有Office/WPS任务时

### 3. ppt-generator
**推荐度**：⭐ 按需装
**理由**：已有 `powerpoint` skill 制作 .pptx，可对比后再决定
**结论**：先看现有powerpoint效果再决定

### 4. humanizer-zh
**推荐度**：⭐⭐ **推荐装**
**理由**：消除AI写作痕迹，中文友好，轻量
**安装建议**：装

---

## 今晚建议安装（按优先级）

| 优先级 | 技能 | 理由 |
|--------|------|------|
| 1 | `find-skills` | 激活72个现有skills |
| 2 | `skill-creator` | 经验沉淀核心工具 |
| 3 | `brainstorming` | 轻量结构化工具 |
| 4 | `humanizer-zh` | 中文写作增强 |

**跳过的原因**：功能与现有skills重叠，或体积大（等按需再装）。

---

## 当前内存约束

- 空闲：**2.62GB**
- 技能库：72个 / 189MB
- 建议：先装轻量的4个，重型（deep-research等）有任务时再装

---

## 相关已有Skills（避免重复安装）

| 新技能 | 已有替代 |
|--------|---------|
| agent-browser | hermes-rpa, browser_cdp |
| product-spec-builder | planning-and-taYOUR_API_KEY |
| ui-prompt-generator | design-md |
| ui-ux-pro-max | popular-web-designs |
| dev-builder | claude-code, codex |
| ppt-generator | powerpoint |