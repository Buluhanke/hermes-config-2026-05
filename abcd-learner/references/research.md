# abcd-learner 研究参考

## AgentFactory (ACL 2026) — 核心参考

**Repo**: https://github.com/zzatpku/AgentFactory
**Paper**: arXiv:2603.18000, ACL 2026 System Demonstrations
**Stars**: 57 | License: MIT

### 核心思想
- 把成功任务解法保留为**可执行子agent代码**（Python + SKILL.md），不是文本经验
- Self-Evolve phase：遇到类似任务 → 检索已有subagent → 检测局限 → 自主修改
- Deploy phase：导出为独立 Python 模块供其他框架用

### Skill 格式（直接复用）
```
skills/
  subagents/
    audio_transcriber/
      SKILL.md        # 元数据 + 描述
      audio_transcriber.py  # 可执行代码
```

SKILL.md 结构：
```yaml
---
name: skill-name
description: Problem Category + Applicable Questions + Key Features
entry_file: skill-name.py
---
# skill-name

## Description
**Problem Category**: ...
**Applicable Questions**: ...
**Skills Used**: ...
**Reasoning Pattern**: ...
```

### Hermes 落地
- `abcd-learner.py`：主 orchestrator，解析日志提取 fact
- 当 fact retrieval_count ≥ 3 → crystallize 为 skill → `~/.hermes/skills/`
- SKILL.md + executable stub 写入 skill 目录

---

## cve_lite.py — CVE 扫描参考

**Repo**: https://github.com/Scottcjn/Rustchain (tools/cve_lite.py)
**License**: MIT | 依赖：仅 Python 标准库

### 关键特性
- OSV.dev 公开 API（无需 key）
- 支持 PyPI / npm / crates.io / Go
- Batch query（chunk 到 1000/请求）
- CVSS v3 计算（纯数学实现）
- 离线模式支持

### SSL 修复
macOS 防火墙导致 `ssl.SSLError: UNEXPECTED_EOF_WHILE_READING`。
修复：`_http_json()` 加 SSL CERT_NONE fallback。

```python
import ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
    ...
```

### Hermes 落地
- 路径：`~/.hermes/scripts/cve_lite.py`
- 调用：`python3 cve_lite.py scan <venv-path> --severity HIGH --timeout 20`
- 已在 `idle_learning_wrapper.sh` 中同步调用

---

## 其他参考项目

### cve-intel-agent (EPSS Top 150 CVE)
- https://github.com/systemBoam-KU-AICS306-25Fall/cve-intel-agent
- 多源爬取 + LLM 提取 + ReAct agent
- EPSS 打分优先级

### Yuning-J/CVE-KGRAG (知识图谱+RAG)
- https://github.com/Yuning-J/CVE-KGRAG | ⭐17
- CVE 知识图谱 + 语义搜索
- Llama3 集成
