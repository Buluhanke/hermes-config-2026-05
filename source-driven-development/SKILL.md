---
name: source-driven-development
description: 源码优先开发 — 先读源码理解现有逻辑，再进行修改。从代码库本身获取真相。
triggers:
  - "需要修改不熟悉的代码"
  - "接手遗留代码"
  - "需要理解系统的真实行为（而非文档描述）"
  - "发现文档和代码不一致"
  - "需要找到某个功能的实现位置"
---

# Source Driven Development

## Overview

源码是唯一的真相。文档会过时，注释会骗人，但运行的代码不会说谎。修改不熟悉的代码之前，先花时间读懂源码，是减少bug的最有效方法。

## When to Use

- 修改任何不熟悉的代码
- 接手遗留代码库
- 发现行为和文档描述不一致
- 需要找到某个功能的实现
- 调试时需要理解真实流程

## Process

### Phase 1: 建立地图

#### 1.1 了解项目结构
- 根目录结构：每个目录是什么？
- 主要的入口文件是什么？
- 配置文件在哪里？
- 测试文件在哪里？

#### 1.2 理解调用链
- 程序的main函数/入口点
- 主要模块之间的调用关系
- 关键类的继承关系

#### 1.3 建立索引
- 全局搜索关键概念
- 找到关键文件和函数
- 标记重要的代码位置

### Phase 2: 深度阅读

#### 2.1 从入口开始
- 从main或入口点开始
- 跟踪每一步调用
- 记录每个关键变量

#### 2.2 边读边验证
- 读一段代码，问：这是什么意思？
- 找到对应的测试用例
- 用测试验证理解

#### 2.3 识别模式
- 代码风格和约定
- 常用的设计模式
- 错误处理模式
- 日志记录模式

### Phase 3: 理解历史

#### 3.1 查看git历史
- 最近的改动是什么？
- 为什么这样改？
- 有没有TODO或FIXME？

#### 3.2 查看issue/PR
- 有没有相关的bug报告？
- 有没有设计决策的讨论？
- 之前的维护者是怎么思考的？

#### 3.3 理解技术债
- 有没有明显的代码异味？
- 有没有绕过的检查？
- 有没有缺失的测试？

### Phase 4: 修改前的准备

#### 4.1 确认理解
- 能用一句话描述代码在做什么吗？
- 能描述关键的数据流吗？
- 能画出简单的调用图吗？

#### 4.2 制定修改计划
- 要改什么？
- 会影响什么？
- 需要改测试吗？

#### 4.3 准备安全网
- 写新的测试覆盖要改的部分
- 确认现有的测试通过
- 准备好回滚方案

## Common Rationalizations

| 常见借口 | 真相 | 反制 |
|---------|------|------|
| "文档说应该这样，我就这样改" | 文档可能过时，代码才是真相 | 先验证文档和代码一致 |
| "我看代码改动很小，直接改" | 微小的改动也可能有大影响 | 必须理解完整上下文 |
| "这是遗留代码，读不懂很正常" | 遗留代码往往是最重要的代码 | 用source-driven方法系统化读懂 |
| "之前的开发者写得烂，我要重写" | 重写风险极高，容易引入新bug | 渐进式改进，不轻易重写 |
| "目录名用 kebab-case 很清晰" | Python import 只认 snake_case | 包目录必须用 `snake_case`，禁止用 `kebab-case` |

## Pitfalls

### Python 包目录命名：必须 snake_case

创建新的 Python 包时，目录名**必须**用 `snake_case`（下划线），**禁止**用 `kebab-case`（连字符）。

```bash
# 错误：kebab-case
mkdir replay-system
python3 -c "import replay-system"  # ModuleNotFoundError

# 正确：snake_case
mkdir replay_system
python3 -c "import replay_system"  # OK
```

原因：Python 的 `import` 语句只认下划线，`import replay-system` 直接报 `ModuleNotFoundError`。这条规则适用于所有平台（macOS/Linux 的文件系统都支持目录名含连字符，但 Python 不认）。

验证：创建目录后立刻 `python3 -c "import my_module"` 确认可导入，再继续写代码。

### 迁移/重构代码时的导入验证

跨目录迁移代码（如 `hermes_v3_demo/` → `hermes-v3/`）时，**不要以为文件写完导入就正确**。必须逐文件验证：

```python
# 1. 先验证顶层导入
from hermes.agent_v3.modules import (
    GoalQueue, ReflectionEngine, MemoryCompressor,
    SkillLibrary, PolicyUpdater, ExplorationManager,
    GoalParser, Visualizer, AgentV3Modules  # 这个可能不存在！
)

# 2. 验证组合类
from hermes.agent_v3 import AgentV3Modules  # 依赖 __init__.py 是否导出
mods = AgentV3Modules()  # 实际实例化，而非只做静态 import

# 3. 验证依赖链路
# SkillLibrary(data_dir=...) → 但实际 __init__ 没有这个参数
```

本 session 的具体错误：
- `AgentV3Modules` 类在 `modules.py` 末尾不存在 → 补充添加
- `__init__.py` 导出 `AgentV3Modules` 但文件里没有 → 报 ImportError
- `SkillLibrary.__init__(data_dir=...)` 但实际签名不接受此参数 → TypeError

教训：**每写完一个模块类，立即 `python3 -c "from module import ClassName; ClassName()"` 验证**，不等所有文件写完再一起测。

### `__init__.py` 必须与实际文件内容保持同步

常见陷阱：写了新类 `MyClass` 在 `module.py` 里，但忘记在 `__init__.py` 中导出。

```python
# module.py
class MyClass:
    ...

# __init__.py  ← 容易遗漏
from module import MyClass  # ← 漏了这条就 from package import MyClass 失败
```

最佳实践：先写 `__init__.py` 的导出列表作为 checklist，每添加一个类就在那里注册。

### 不存在的类/函数被引用时静默失败

Python 的 `import` 只检查**语法正确性**，不检查**类是否存在**。所以 `from foo import Bar` 在 Bar 不存在时不会报错，只有真正调用 `Bar()` 时才报错。这导致迁移代码时静默失败。

解决方案：用 `python3 -c "from x import Y; Y()"` 做实际实例化验证，而非只做 `import x`。

### 远程编辑文件的陷阱

通过 SSH 修改远程文件时，用 Python 而不是 shell 工具（sed、awk）：

```bash
# 危险：macOS 用 sed -i ''，Linux 用 sed -i（无参数）
# 危险：sed 正则中的括号、斜杠容易转义出错
sed -i '' 's/old/new/' file   # macOS
sed -i  's/old/new/' file     # Linux

# 安全：Python heredoc 直接写远程文件
ssh kk@192.168.8.236 "~/.hermes/hermes-agent/venv/bin/python3 - << 'PYEOF'
with open('/path/to/file.py', 'r') as f:
    content = f.read()
content = content.replace('old_string', 'new_string')
with open('/path/to/file.py', 'w') as f:
    f.write(content)
PYEOF"
```

**本 session 具体教训：**
- 修改 `threat_patterns.py`（安全敏感文件）用了 `//` 注释，Python 报错 `SyntaxError: invalid syntax`，直到运行 hermes CLI 时才发现
- 教训：在 SSH heredoc 里写 Python 时，`//` 不是注释，要用 `#`
- 验证语法：用 `py_compile.compile()` 在远程验证后再执行关键路径

### 文件同步到远程的正确路径

```bash
# 危险：直接 rsync 到 ~/.hermes/scripts（权限、目录不存在）
rsync script.py kk@192.168.8.236:~/.hermes/scripts/

# 正确：先 rsync 到 /tmp，再在远程 cp/mv
rsync script.py kk@192.168.8.236:/tmp/
ssh kk@192.168.8.236 "cp /tmp/script.py ~/.hermes/scripts/"
```

**本 session 教训：** fact_backup.json 在本机 `/tmp/`，rsync 到远程 `/tmp/` 成功；但直接同步到远程 `~/.hermes/` 可能因目录权限或 ssh 配置失败。`/tmp` 是通用写入位置。

### 远程 Python 环境隔离

远程 Hermes 用独立 venv，不在系统 PATH 里：

```bash
# 错误：系统 python3，缺少 hermes 依赖
ssh kk@192.168.8.236 "python3 -c 'import sqlite3'"  # 可能缺少模块

# 正确：用 hermes venv 的 python
ssh kk@192.168.8.236 "~/.hermes/hermes-agent/venv/bin/python3 -c '...'"

# 远程创建 cron 时也需要 venv
ssh kk@192.168.8.236 "~/.hermes/hermes-agent/venv/bin/hermes cron create ..."
```

**本 session 教训：** 所有远程 Python 调用（cron job creation、database operations、script execution）都必须用 `~/.hermes/hermes-agent/venv/bin/python3`，不能用 `python3` 或 `python`。

## Red Flags

- 修改代码时发现和文档描述不一致
- 无法用一句话描述代码在做什么
- 改动后发现有未考虑的边界情况
- 改动后测试失败但不知道为什么
- 接手代码时没有任何测试
- 发现代码中有TODO但不知道是否还相关
- 需要猜测某个变量的含义

## Verification

验证清单：

- [ ] 能画出关键模块的调用关系图
- [ ] 能描述关键数据流
- [ ] 找到了对应的测试文件
- [ ] 识别了代码的设计模式
- [ ] 理解了错误处理方式
- [ ] 了解了最近的改动历史
- [ ] 有测试覆盖要改的部分
- [ ] 修改计划已验证
