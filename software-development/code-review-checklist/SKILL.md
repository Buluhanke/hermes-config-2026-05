# Code Review Checklist Skill

提供系统化的代码审查清单，支持通用审查和专项自动化脚本审查。

## 使用方式

```
review_code <path> [--scope <scope>] [--format <format>]
```

参数:
- `path`: 代码路径或仓库根目录
- `--scope`: 审查范围 `general` | `1688` | `python` | `git` (默认: `general`)
- `--format`: 输出格式 `list` | `table` | `json` (默认: `list`)

---

## 1. 审查维度 (通用)

### 功能性
- [ ] 代码实现了需求文档中的所有功能点
- [ ] 输入验证充分（边界值、空值、非法类型）
- [ ] 错误处理合理，未被吞掉的异常有日志
- [ ] 业务逻辑正确，无语义错误
- [ ] 并发场景考虑线程安全

### 性能
- [ ] 无 N+1 查询问题
- [ ] 循环中无重复的数据库/网络调用
- [ ] 大数据量处理采用分页/流式/批量方式
- [ ] 缓存策略合理，缓存键设计无冲突
- [ ] 无不必要的深拷贝或大对象复制
- [ ] 算法复杂度合理（避免 O(n²) 在大数据场景）

### 安全性
- [ ] 无 SQL/命令注入风险（参数化查询）
- [ ] 用户输入经过校验和清洗
- [ ] 敏感信息（密码、Token、密钥）不硬编码、不打印日志
- [ ] 权限检查在业务逻辑前完成
- [ ] 外部 API 调用使用 HTTPS
- [ ] 文件路径操作防止路径遍历

### 可维护性
- [ ] 函数/类职责单一，控制在 50 行以内
- [ ] 命名规范（变量/函数/类名见名知意）
- [ ] 无重复代码（DRY 原则），重复逻辑超过 3 处需重构
- [ ] 关键逻辑有注释说明 WHY 而非 WHAT
- [ ] 无硬编码配置值（使用配置文件/环境变量）
- [ ] 依赖明确，无隐藏的循环依赖

---

## 2. 1688 自动化脚本专项检查

### Cookie 有效性
- [ ] Cookie 过期时间有监控机制（过期前主动刷新）
- [ ] 过期后自动重试登录并更新 Cookie
- [ ] 多账号场景：Cookie 与账号映射清晰，无混淆
- [ ] 测试环境使用独立的测试账号 Cookie

### 反爬机制应对
- [ ] 请求间隔随机化（避免固定频率，被识别为机器人）
- [ ] User-Agent 轮换（使用真实浏览器 UA 列表）
- [ ] 失败重试使用退避策略（exponential backoff）
- [ ] 页面数据通过解析而非截图 OCR（更稳定）
- [ ] 关键请求前有人工操作模拟（随机鼠标移动、滚动）
- [ ] IP 封禁检测：连续 3 次 403/418 时自动切换策略

### 异常处理
- [ ] 网络超时设置合理（单个请求 ≤ 15s）
- [ ] HTTP 状态码非 200 有分级处理（401 重认证、429 降频、5xx 重试）
- [ ] 解析失败有 fallback（日志关键字段供排查）
- [ ] 任务中断后有 checkpoint 机制，支持断点续跑
- [ ] 异常不向上穿透，需在最外层统一记录

---

## 3. Python 代码审查要点

### 类型提示
- [ ] 函数参数和返回值有类型标注（除非私有函数）
- [ ] Union 类型使用 `|` 而非 `Optional`（Python 3.10+）
- [ ] 泛型容器标注：`list[int]`、`dict[str, Any]`
- [ ] 类型别名用于复杂业务类型（如 `UserId = int`）
- [ ] TypedDict 用于结构化 dict（如 API 响应）

### 异常捕获
- [ ] 捕获具体异常类型，不使用 `except Exception`
- [ ] 异常重抛保留原 traceback（`raise ... from e`）
- [ ] 资源清理使用 `try/finally` 或 context manager
- [ ] 单线程/单进程场景避免 bare `except:`
- [ ] 异常信息包含上下文（参数值、识别码）

### 日志记录
- [ ] 日志级别正确（DEBUG 用于排查、INFO 用于流程节点、WARN 用于可恢复异常、ERROR 用于需关注的故障）
- [ ] 日志格式统一：`[级别] [时间戳] [模块] [操作] [详情]`
- [ ] 敏感字段脱敏（手机号、Token 显示为 `****`）
- [ ] 日志不含大对象完整打印（用 `len()` 或摘要）
- [ ] 生产环境日志量可控（高频循环中避免 INFO 日志）
- [ ] 结构化日志输出 JSON 格式，便于采集分析

### 其他 Python 规范
- [ ] 异步代码正确使用 `await`，无同步阻塞
- [ ] 上下文管理器管理数据库连接、文件句柄
- [ ] 第三方库版本锁定（requirements.txt 或 pyproject.toml）
- [ ] 无 `from module import *` 污染命名空间

---

## 4. Git Commit 规范检查

### Commit Message 格式
```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

### Type 分类
- `feat`: 新功能
- `fix`: 缺陷修复
- `docs`: 文档变更
- `style`: 代码格式（不影响功能）
- `refactor`: 重构（不修复也不加功能）
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建/工具变更

### 规范检查项
- [ ] Subject 不超过 50 字，结尾无句号
- [ ] Subject 描述做了什么，而非怎么做的
- [ ] Body 解释 WHY，不解释 WHAT
- [ ] 提交粒度合理（一个 commit 一个逻辑变更）
- [ ] 无提交未跟踪的大文件（ binary、敏感数据）
- [ ] Footer 中关联 Issue：`Closes #123`
- [ ] 避免 fixup commit（`git rebase -i` 整理后再合入）

---

## 5. 自动化工具集成

### Pre-commit Hook

在仓库根目录创建 `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-json
      - id: check-toml

  - repo: https://github.com/psf/black
    rev: 24.1.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: ["--max-line-length=120", "--extend-ignore=E203,W503"]
```

安装并启用:
```bash
pip install pre-commit
pre-commit install
```

### Commit 规范检查

安装 commitlint:
```bash
npm install -g @commitlint/cli @commitlint/config-conventional
```

在仓库创建 `commitlint.config.js`:
```js
module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [2, 'always', ['feat', 'fix', 'docs', 'style', 'refactor', 'perf', 'test', 'chore']],
    'subject-max-length': [2, 'always', 50]
  }
};
```

集成到 pre-commit:
```yaml
  - repo: https://github.com/alessandrogario/pre-commit-commitlint
    rev: 1.1.0
    hooks:
      - id: commitlint
        stages: [commit-msg]
```

### 自动化审查命令

提供快速审查快捷命令:

```bash
# 全部检查
review-code . --scope general --format table

# 仅 Python 规范
review-code . --scope python --format list

# 仅 1688 脚本
review-code . --scope 1688 --format list

# 仅 Git 规范
review-code . --scope git --format list
```

---

## 输出示例

```
=== 代码审查报告 ===

路径: src/utils/scraper.py
范围: 1688

[功能] ✓ 通过
[性能] ⚠ 警告: 第 45 行循环中调用 API，建议批量处理
[安全] ✓ 通过
[可维护性] ⚠ 警告: 第 78 行 magic number 1024 应提取为常量

总结: 2 通过，2 警告，建议修复后再合并
```