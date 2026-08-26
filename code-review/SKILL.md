---
name: code-review
description: "双轴代码评审 自固定点起的 diff。Standards轴(是否守仓库规范+Fowler坏味基线) + Spec轴(是否实现原issue/spec)。两轴并行sub-agent，并排汇报。Use when 用户要审分支/PR/WIP、说'review since X'、或提交前自查"
triggers:
  - 审查 / code review / 评审 / 自查
  - review 分支 / review PR / 审改动
  - "review since <commit/branch/tag>"
  - 提交前过一遍 / 合并前检查
  - 代码质量门 / 规范扫描
pitfalls:
  - name: 两轴混排成单一排名
    description: |
      把 Standards 与 Spec 的发现合并、重排、挑一个「最严重」 winner。
      两轴刻意分离就是为了防止一轴掩盖另一轴。
    fix: |
      最终报告严格分 `## Standards` 与 `## Spec` 两节，原样或轻洁呈现，
      不合并不重排。结尾各轴一行总结 + 轴内最坏项，绝不选跨轴冠军。
  - name: 固定点没验证就派 sub-agent
    description: |
      坏 ref 或空 diff 进了并行 sub-agent 才报错，浪费两轮。
    fix: |
      先 `git rev-parse <ref>` 确认可解析，再 `git diff ...HEAD` 确认非空。失败在此处，不进 sub-agent。
  - name: 把坏味当硬违规
    description: |
      Fowler 基线每条是带标签的启发式（「可能 Feature Envy」），不是硬违规。
      文档化仓库规范永远优先于基线。
    fix: |
      Standards sub-agent 提示里写清：文档化仓库规范永远赢；基线坏味永远是可判断项；
      工具已强制的跳过。区分 hard violation 与 judgement call。
  - name: Spec 源找不到就硬审
    description: 没有 issue/spec 却让 Spec sub-agent 瞎找。
    fix: |
      按序找：commit message 里的 issue 引用 → 用户给的路径 → docs/specs/.scratch 下匹配分支名的 spec 文件。
      都没有就跳过 Spec sub-agent，在报告注明「no spec available」。
---

# Code Review — 双轴评审

源自 Matt Pocock `skills/engineering/code-review`，改写为 Hermes 技能。对 `HEAD` 与用户给的**固定点**之间的 diff 做双轴评审：

- **Standards**：代码是否符合本仓库文档化编码规范？
- **Spec**：代码是否忠实实现了原始 issue / spec？

两轴跑**并行 sub-agent**，互不污染上下文，本技能汇总。

## 流程

### 1. 钉死固定点
用户说的固定点（commit SHA / 分支名 / tag / `main` / `HEAD~5` 等）。没指定就问。

抓一次 diff 命令：`git diff <ref>...HEAD`（三点，对 merge-base 比较）。同时 `git log <ref>..HEAD --oneline` 列提交。

**先验证**：`git rev-parse <ref>` 可解析 + `git diff ...HEAD` 非空。坏 ref / 空 diff 在此失败，不进 sub-agent。

### 2. 找 Spec 源（按序）
1. commit message 里的 issue 引用（`#123` / `Closes #45` / GitLab `!67`）
2. 用户作为参数传的路径
3. `docs/` `specs/` `.scratch/` 下匹配分支名或 feature 的 spec 文件
4. 都没有 → 问用户 spec 在哪；说没有 → Spec sub-agent 跳过，报告注明

### 3. 找 Standards 源
仓库里任何写「代码该怎么写」的文件：`CODING_STANDARDS.md` / `CONTRIBUTING.md`。

此外 Standards 轴**永远带 Fowler 坏味基线**（即使仓库啥都没写）。两条约束：
- **仓库覆盖**：文档化仓库规范永远赢；它认可基线会标的东西时，压制该坏味。
- **永远判断项**：每条坏味是带标签启发式（「可能 Feature Envy」），非硬违规。工具已强制的跳过。

坏味清单（每条 *是什么* → *怎么修*）：
- **Mysterious Name** 名不表意 → 改名；起不出诚实名 = 设计本身糊
- **Duplicated Code** 同逻辑形状出现在多处 → 抽共享形状，两处都调
- **Feature Envy** 方法伸进别的对象数据多于自己的 → 把方法移到它羡慕的数据上
- **Data Clumps** 几个字段/参数总一起走（想成为类型的类型）→ 打包成一个类型
- **Primitive Obsession** 原始值/字符串顶替该有自己类型的领域概念 → 给概念独立小类型
- **Repeated Switches** 对同一类型的相同 switch/if 级联反复出现 → 多态，或两处共享一个 map
- **Shotgun Surgery** 一个逻辑改动逼得 diff 里多文件散改 → 把一起变的收进一个模块
- **Divergent Change** 一个文件因几个不相关原因被改 → 拆，使每模块只因一种原因变
- **Speculative Generality** 为 spec 没有的需求加的抽象/参数/hook → 删，内联回真实需求出现
- **Message Chains** 长 `a.b().c().d()` 导航调用方不该依赖 → 在第一对象上藏一层方法
- **Middle Man** 类/函数基本只往后委托 → 砍了，直调真目标
- **Refused Bequest** 子类/实现者忽略或覆盖大部分继承 → 丢继承，用组合

### 4. 并行派两个 sub-agent
**Standards sub-agent** 提示含：完整 diff 命令 + 提交列表 + 步骤3找到的 standards 文件列表 **+ 完整粘贴上面的坏味基线**（sub-agent 无其他途径拿到）。任务：「逐文件/hunk 报 (a) 每处违反文档化规范：引规范(文件+规则)；(b) 任何基线坏味：命名+引 hunk。区分 hard violation 与 judgement call；文档化仓库规范覆盖基线；工具已强制的跳过。400 词内。」

**Spec sub-agent** 提示含：diff 命令 + 提交列表 + spec 路径或内容。任务：「报 (a) spec 要求但缺失/部分实现；(b) diff 里没被要求的行为(范围蔓延)；(c) 看似实现但实现看起来错的。每条引 spec 原文。400 词内。」spec 缺失则跳过并注明。

### 5. 汇总
在 `## Standards` 与 `## Spec` 标题下原样或轻洁呈现两份报告。**不合并不重排**——两轴刻意分离。

结尾一行总结：每轴发现总数 + 轴内最坏项（若有）。**不选跨轴冠军**——那正是分离要防的重排。

## 为什么两轴
一次改动可过一轴败另一轴：
- 守尽规范但实现错东西 → Standards 过，Spec 败
- 完全按 issue 来但破项目约定 → Spec 过，Standards 败

分开报阻止一轴掩盖另一轴。

## Hermes 落地
- 用 `delegate_task` 并行派两个 leaf sub-agent（互不可见，天然隔离）。
- 固定点验证、spec/standards 源定位在主会话做（需用户交互），再派 sub-agent。
- 汇总在主会话，严格双节、不重排。
