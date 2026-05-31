# Direction C 行业动态：GPT-5.5 Harness + Context Window W20 + Codex Sudo

**发现日期**：2026-06-01 03:27 (idle_learning方向C巡检)

---

## ⭐ GPT-5.5 Computer Use Agent Harness (Cobus Greyling, May 1 2026)

**来源**：cobusgreyling.substack.com/p/gpt-55-computer-use-agent-harness
**核心论点**：**"模型不是产品，闭环才是"**

### CUA 四步循环

截图 → 模型推理 → 结构化动作 → 环境执行 → 新截图 → ...

- API：`tools: [{type: "computer"}]` → 返回 `computer_call` 动作数组
- 动作类型：click, type, scroll, keypress, drag, move, wait, screenshot
- 模型从不直接接触环境 — 看见像素，发出结构化指令

### 关键引用

> "The model gives you vision. The harness gives you agency."
> "The model sees and reasons. The harness acts and constrains."
> "This is computer use as a systems engineering problem, not a model capability problem."

### 对 Hermes 的启示

1. **验证架构**：screen_watcher → handler → auto_execute 正是 CUA 循环
2. **Harness = 安全边界**：ACTION_WHITELIST 思路正确，安全由 harness 强制执行，非 prompt
3. **错误恢复由 harness 决策**：self-correct vs rollback vs escalate
4. **Reasoning effort 分级**：五级控制 → 与 AVR routing 对应
5. **坐标映射关键**：截图分辨率=执行环境分辨率
6. **截图画质决定推理质量**：压缩伪影、mid-render 时机都影响判断

### 关键数据

- GPT-5.5 OSWorld-Verified: **78.7%**（超越人类基线 72.4%）
- Terminal-Bench 2.0: **82.7%**
- 1M token context, 10.24M pixels 截图细节保留

---

## ⭐ Context Window — W20 2026 (Simone Basso, May 20)

**来源**：medium.com/@smnbss/context-window-w20-2026-083a751529a3

**Hermes 被列为 "open-source agent OS"**：
- "The SOUL/memory/skills triad is the most replicable blueprint in the wild"
- "Stop waiting for 'the open Claude.' It shipped."

**MCP vs Code Mode 数据对决**（Akshay Pachaar）：
- Playwright MCP: 13.7K tokens | Five-server stack: 55K tokens | Drive→Salesforce: 150K tokens
- **Code Mode：2K tokens（98.7% 缩减）**
- Tool definitions belong in code, not schemas

**行业趋势**：
- Anthropic 6/15: paid Claude 含独立 agent API 额度 → "agents as a line item"
- MCP SDK 下载量 100M→300M（2026 年）— MCP 没死，全量加载模式死了

---

## ⭐ Codex sudo Workaround (Son Luong, May 30)

**来源**：x.com/sluongng/status/2060746160558543217
**数据**：914K views, 13K likes

Agent 安全边界是当前社区最关注的问题。验证动作分级 Silent/Logged/Confirmed/Blocked 是必要条件。

---

## ⭐ OSU-NLP-Group GUI Agents Paper List (537 papers)

**来源**：github.com/OSU-NLP-Group/GUI-Agents-Paper-List
**Web 版**：osu-nlp-group.github.io/GUI-Agents-Paper-List

**数据**：537 papers | Desktop 124 | Safety 29 | Planning 10 | 804 stars
**使用**：按 Desktop + safety/planning 筛选，网站版支持全文搜索 + 多轴过滤
