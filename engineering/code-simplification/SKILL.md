---
name: code-simplification
description: 代码简化 — 识别过度工程，把复杂的代码变简单。简单是代码最重要的质量。
triggers:
  - "代码过于复杂，难以理解"
  - "有人写了过度设计的代码"
  - "需要重构时"
  - "代码评审发现过度工程"
  - "有重复代码需要抽象"
---

# Code Simplification

## Overview

简单是代码最重要的质量。写出别人能理解的代码比写出"聪明"的代码更重要。过度工程的代码往往比过度简单的代码更难维护。

## When to Use

- 代码难以理解
- 需要重构时
- 发现重复代码
- 代码评审发现过度设计
- 要在"简单方案"和"通用方案"之间选择

## Process

### Phase 1: 评估复杂度

#### 1.1 复杂度指标
- 函数长度（建议<50行）
- 圈复杂度（建议<10）
- 参数数量（建议<4）
- 嵌套深度（建议<3）
- 文件长度（建议<300行）

#### 1.2 理解代码意图
- 这个函数在做什么？
- 有没有更好的名字？
- 注释和代码一致吗？

#### 1.3 识别过度工程信号
- 为了"未来可能的需求"写的代码
- 无法说清楚为什么要这样设计
- 过度抽象导致难以理解
- 用复杂方式实现简单功能

### Phase 2: 简化策略

#### 2.1 函数简化
```python
# 简化前
def process_user_data(user_data: dict) -> dict:
    result = {}
    if user_data.get('name'):
        result['name'] = user_data['name'].strip()
    if user_data.get('email'):
        result['email'] = user_data['email'].strip().lower()
    if user_data.get('age'):
        result['age'] = int(user_data['age'])
    return result

# 简化后
def process_user_data(user_data: dict) -> dict:
    return {
        'name': user_data.get('name', '').strip(),
        'email': user_data.get('email', '').strip().lower(),
        'age': int(user_data.get('age', 0))
    }
```

#### 2.2 去除不必要的抽象
```python
# 简化前
class UserDataProcessor:
    def __init__(self, config: ProcessorConfig):
        self.config = config
    def process(self, data: dict) -> dict:
        return self._process_impl(data)
    def _process_impl(self, data: dict) -> dict:
        # ... 50行代码

# 简化后
def process_user_data(data: dict) -> dict:
    # ... 20行代码
```

#### 2.3 拆分复杂函数
- 一个函数只做一件事
- 每个函数可以被单独测试
- 函数名清晰表达意图

### Phase 3: 验证简化

#### 3.1 功能保持
- 简化后功能必须完全一致
- 运行所有测试确认
- 对比新旧代码的输出

#### 3.2 可读性提升
- 其他人能理解吗？
- 注释是否变少但更清晰？
- 命名是否更直观？

#### 3.3 性能检查
- 简化后性能是否下降？
- 如果性能重要，对比基准测试

## Common Rationalizations

| 常见借口 | 真相 | 反制 |
|---------|------|------|
| "这个设计更通用，以后能扩展" | YAGNI原则：不要写你不需要的 | 先简单，需求来时再扩展 |
| "这段代码我以后还要用" | 实际上很少会复用 | DRY，但不要过度抽象 |
| "简单代码显得我不专业" | 专业是能解决实际问题 | 简单是最难写的 |
| "这个框架就是这样用的" | 框架不等于最佳实践 | 基于具体场景判断 |

## Red Flags

- 无法在30秒内解释一个函数
- 有"以后可能用到"的代码
- 过度使用设计模式
- 函数名是动词而非描述
- 有注释说明"这段代码很复杂"
- 测试比实现代码还难懂
- 重构后代码比之前还复杂

## Verification

验证清单：

- [ ] 圈复杂度降低
- [ ] 函数长度缩短
- [ ] 测试覆盖率没有下降
- [ ] 功能完全一致
- [ ] 代码意图更清晰
- [ ] 没有引入新的概念
- [ ] 其他开发者能理解
