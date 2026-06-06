# STAR-4D 学习循环 — 跨站 AI 交叉验证成果（2026-06-04）

## 来源

三站 AI 交叉验证：
- **DeepSeek** → STAR-4D 框架 + 失败规则 + 避坑飞轮
- **豆包** → 反思式增量 Prompt 进化 + 工具函数自扩充
- **ChatGLM** → 经验/技能进化路线 + MemSkill 闭环 + 分层记忆

## STAR-4D 框架

```
Search → Try → Adjust → Record
  ↓
4D: Detect → Diagnose → Do → Document
```

### 4D 详解

| 阶段 | 含义 | 自我进化中的落地 |
|------|------|-----------------|
| **Detect** | 错误日志有哪些模式？首次还是重复？资源耗尽？ | hourly 模式匹配 |
| **Diagnose** | 查 logs/gateway.log 定位层级；查 fact_store 是否有类似经历 | daily 分析 |
| **Do** | 先自动修复（重启/清理/重载），一次只改一个变量，立即验证 | hourly/daily 执行 |
| **Document** ⭐ | 写情景记忆到 fact_store；提炼规则更新 SOUL.md 或写 skill | daily weekly Record |

### 失败规则

- 失败一次 → 换一种方法
- 失败三次 → 上报用户 + 记录为高价值失败案例

### 避坑飞轮

```
坑点入库 → fact_store（带标签：应用+操作类型+错误模式）
行动前检索 → 每次行动计划前 FTS5 搜 "应用+操作类型+坑点"
代码化固化 → 稳定解决方案硬编码为脚本/SOP，不再每次推理
定期审查 → daily 拉"本周坑点"，分析为何预防失败
```

## 反思式增量 Prompt 进化（豆包补充）

- 单次新增 ≤ 1500 token
- 常驻内存 < 300MB，适合 Mac mini M4 24GB
- 每次失败后提炼一句话教训写入 Prompt
- 不重复同样的失败模式

## MemSkill 闭环（ChatGLM 补充）

- Memory → Skill → Memory 循环
- 从 fact_store 提取模式 → 硬编码为 skill
- skill 再被调用 → 结果写回 fact_store
- 形成自我强化的学习闭环

## 本次执行总结（2026-06-04）

| 阶段 | 动作 | 结果 |
|------|------|------|
| Search | 访问 DeepSeek + 豆包 + ChatGLM 三站 | 获得 STAR-4D + 轻量化进化 + 分层记忆三套方案 |
| Try | 更新 self_evolution.sh + 创建 `.pitfalls_checklist.txt` | 坑点检索升级为快速 checklist |
| Adjust | 发现 checklist 比 FTS5 查询更快 | 改用直接文件查找，实时性更强 |
| Record | 写入 Obsidian + 更新 SOUL.md + 写 5 条 fact | 情景记忆 + 语义记忆双更新 |

**新增产出物**：
- `.pitfalls_checklist.txt` — 6 条初始坑点
- 5 条新 fact 入库（STAR-4D、坑点飞轮、代码化、Prompt 进化、失败驱动记忆）
- self_evolution.sh 坑点检索飞轮（修复前查 + 修复后写）