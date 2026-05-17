---
name: skill-protocol
description: Skill协议与标准化 — 统一定义skill的输入/输出/依赖/副作用，让Hermes能自动判断调用条件、多Agent协作、跨skill复用。
triggers:
  - "创建新skill"
  - "现有skill行为不符合预期"
  - "需要多个skill协作"
  - "需要给skill写测试"
  -
version: 1.0.0 "skill之间有冲突或重复"
---

# Skill Protocol

## Overview

skill是Hermes的核心能力单元，但95个skill没有统一标准——有的有Process有的没有，有的有Rationalizations有的没有。这导致：skill路由靠猜测、调用条件不明确、多Agent无法协作。

**Skill Protocol**为每个skill定义：标准结构、输入输出schema、依赖条件、副作用边界、重试策略。

## SKILL.md标准格式

每个skill必须包含以下部分：

```yaml
---
name: skill-name              # 唯一标识，kebab-case
description: 一句话描述       # 10-20字
category: category-name      # 分类（engineering/procurement/platform/...）
triggers:                    # 触发条件列表
  - "场景描述"
input_schema:                # 输入参数schema（可选）
output_schema:               # 输出结果schema（可选）
required_context:            # 需要的前置上下文
side_effects:                # 副作用描述
retry_policy:                # 重试策略
---
```

### 必填Section

1. **Overview** — 这个skill解决什么问题，为什么存在
2. **When to Use** — 明确什么情况下调用此skill
3. **Process** — 逐步执行流程，每步可验证
4. **Common Rationalizations** — 反借口表（见下）
5. **Red Flags** — 危险信号，触发时需警惕
6. **Verification** — 完成标准清单

### 选填Section

- **input_schema** / **output_schema** — 结构和约束
- **dependencies** — 依赖的其他skill
- **side_effects** — 对系统/文件/状态的影响
- **retry_policy** — 失败重试策略

## Common Rationalizations（反借口表）

格式：| 常见借口 | 真相 | 反制 |

反借口表是skill最有价值的部分——把执行时的"合理借口"提前暴露，让决策有据可查。

**标准反借口表结构：**

| 借口类型 | 借口内容 | 真相 | 反制措施 |
|---------|---------|------|---------|
| 跳过验证 | "这是我自己的代码，不需要测试" | 自己的代码更容易有盲区 | 强制code review |
| 跳过流程 | "流程太麻烦，先上线再说" | 上线后再补往往不补 | 流程是质量门禁 |
| 过度自信 | "这个bug不可能发生" | 所有bug都是不可能发生的 | 实测验证 |
| 外部归因 | "这是库的bug，不是我写的" | 用了烂库是选择问题 | 选型需验证 |
| 成本削减 | "测试环境足够了" | 测试和生产差异是bug温床 | 缩小环境差异 |

## Red Flags（危险信号）

触发以下情况时，skill执行需高度警惕：

- 列表形式，每条一行
- 具体、可观察、不是泛泛的"注意安全"
- 例如："点击后页面10秒无变化 → 可能网络问题或选择器错误"

## Verification（验证清单）

skill完成后的检查项：
- 每项必须是可验证的（yes/no/数值）
- 包含功能验证 + 质量验证
- 例如：
  - [ ] 功能正确
  - [ ] 无性能退化
  - [ ] 测试覆盖

## input_schema / output_schema 示例

```yaml
input_schema:
  type: object
  required: [query]
  properties:
    query:
      type: string
      description: 搜索关键词
    limit:
      type: integer
      default: 10
      maximum: 50

output_schema:
  type: object
  properties:
    items:
      type: array
      items:
        type: object
        properties:
          title: { type: string }
          url: { type: string }
    total: { type: integer }
```

## Skill命名规范

- **kebab-case**：`code-review-and-quality`
- **动词-名词**：`debugging-and-error-recovery`
- **避免缩写**：`spec-driven-development` 而非 `sdd`

## Skill依赖声明

```yaml
dependencies:
  - skill: source-driven-development  # 修改代码前先读懂代码
  - skill: debugging-and-error-recovery  # 出现问题时走调试流程
```

## Side Effects声明

```yaml
side_effects:
  - "写入文件：~/.hermes/skills/..."
  - "调用外部API"
  - "修改系统剪贴板"
  - "发送消息到QQ"
```

## Retry Policy

```yaml
retry_policy:
  max_attempts: 3
  backoff: exponential
  initial_delay: 2s
  max_delay: 60s
  retry_on:
    - network_error
    - timeout
    - rate_limit
  no_retry_on:
    - auth_failure  # 认证失败需人工介入
    - invalid_input  # 输入错误重试无效
```

## Skill路由协议

当Hermes决定调用哪个skill时：

```
1. 匹配触发条件（triggers）
2. 检查required_context是否满足
3. 检查副作用是否可接受
4. 按dependencies顺序执行依赖skill
5. 执行主skill
6. 验证输出
```

## 验证清单

- [ ] SKILL.md存在且格式完整
- [ ] name/description/triggers必填字段存在
- [ ] Overview + Process + Rationalizations + RedFlags + Verification五部分齐全
- [ ] Rationalizations至少3行
- [ ] 命名符合kebab-case
- [ ] dependencies正确声明
- [ ] side_effects已说明
