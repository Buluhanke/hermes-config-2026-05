# Marketing vs Code — 真实案例库

> 项目宣传语与实际代码库的差异记录。用于未来 vetting 时对照。

## 案例 1：ECC (everything-claude-code) — 2026-06-06

| 维度 | 宣传 | 实际 (git ls-tree -r HEAD) | 差距 |
|------|------|---------------------------|------|
| Stars | 182K+ | 182K+ | ✓ 准确 |
| "63个专业子Agent" | 63 agents | `.agents/skills/` 下 33 个 SKILL.md 文件 | **夸大** — "agent"是提示词文件，不是可执行程序 |
| "1282个安全测试用例" | 1282 tests | tests/ 下 157 个测试文件，其中 20 个 blob 缺失 | **夸大+不完整** |
| "Agent Harness 操作系统" | 操作系统级平台 | 配置集/提示词合集 | **定位夸大** — 本质是 config-pack |
| "12+ 语言生态系统" | 12 种语言 | 12 种 AI 工具适配目录 | **语义偷换** — 是 harness 数不是编程语言 |
| 文件总数 | — | 2,914 个文件 | 信息量真实 |
| License | MIT | MIT | ✓ |
| 维护者 | — | 单人维护 ("a single maintainer ships weekly") | 信息真实 |

### 检测信号

1. **"Agent/Agent System" 类项目**：90% 概率是提示词/配置文件，不是可执行程序。用 `git ls-tree -r HEAD` 搜 `.bin`/`.py`/`.js` 二进制或脚本确认。
2. **"X 个 Agent/工具"**：查目录结构而非 README。`find . -name "*.md"` 数量通常远小于宣传。
3. **"Y 个测试用例"**：数 `*.test.*` / `*_test.*` / `test_*.*` 文件数。检查 git 中是否有 missing blob。
4. **GitHub 仓库文件少但 star 多**：star/fork 比偏高 → 可能有水军或 bot star。
5. **missing blob 是最强信号**：tree 中有记录但 blob 缺失 → CI 可能没跑全，代码库不完整。

### 结论模板

```
值不值得用：
✅ 适合：[实际用途]
⚠️ 别被宣传误导：[夸大部分]
⚠️ 代码质量信号：[missing blob / CI 状态等]
结论：[一句话总结真实定位]
```
