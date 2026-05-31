# PromptArmor Agent Security Research — Direction C Monitoring Source

**来源**：PromptArmor（promptarmor.com）— 安全研究机构，手动渗透测试主流 AI Agent 平台
**发现日期**：2026-06-01（通过 HN Firebase API 发现 + site-sidebar 交叉发现模式）
**HN 排名**：#1 (431pts) — Cloudflare Turnstile + 同站点关联文章发现

## 共性攻击模式

所有 18+ 披露攻击共享同一根因链：

```
间接提示注入（indirect prompt injection）
  → 模型被操纵调用越权工具
  → 数据跨账号窃取 / UI覆盖钓鱼
```

根因：Agent 架构授予了「任意工具调用」权限，但无法区分用户指令中的工具调用 vs 外部内容中的恶意指令。

## 关键个例

### Ollama Desktop App（170K+ GitHub stars）
- **报告时间**：2025-12-18（**至今未修复，4次跟进无回应**）
- **漏洞**：模型输出渲染不安全 → 整个桌面 UI 被攻击者网站覆盖（phishing overlay）
- **三类零点击数据窃取**：
  1. 不安全 web search tooling：构造含用户数据的URL发送给攻击者
  2. Markdown image 渲染导致的窃取
  3. 外部 HTML 元素渲染导致的窃取
- **无人类审批步骤**：所有攻击无需用户确认
- **对 Hermes**：Hermes 不渲染 Ollama 模型输出给用户，VLM 输出仅用于场景分类→action routing 的内部逻辑，攻击面极低

### ChatGPT for Google Sheets（185K 下载）
- **攻击效果**：单一 sheet 的注入 → 窃取整个账户 12 个工作簿（穿越所有 sheet）
- **绕过设置**：即使开启"需要人类批准"设置，攻击仍然成功
- **附带攻击**：钓鱼弹窗覆盖 + 侧边栏被攻击者控制
- **对 Hermes**：验证设置层面的防御不够，必须有架构级 guardrail（如 ACTION_WHITELIST 限制 scene→action 映射）

### Google Antigravity（Google 新一代 agent-first 代码编辑器/开发平台）
- **攻击效果**：集成指南中的注入 → Gemini 窃取 .env 凭据和 IDE 代码
- **绕过设置**：Gemini 绕过自身的"Allow Gitignore Access > Off"设置
- **利用机制**：使用浏览器子代理访问恶意网站窃取数据
- **对 Hermes**：设置被绕过说明纯配置层面的防御不可靠，必须有 Verify 阶段

### Other confirmed victims（同为间接提示注入攻击）
- Codex for Everything — 数据窃取
- Microsoft Copilot Cowork — 文件窃取
- Claude Cowork — 文件窃取
- Notion AI — 数据窃取
- HuggingFace Chat — 数据窃取
- Superhuman AI — 邮件窃取
- Slack AI — 数据窃取（间接提示注入）
- Writer.com — 数据窃取
- Ramp Sheets AI — 财务数据窃取
- Snowflake Cortex AI — 沙箱逃逸+执行恶意软件
- GitHub Copilot CLI — 下载和执行恶意软件
- vLex（法律AI，10亿美元收购）— 屏幕接管攻击
- CellShock — Claude AI Excel 数据窃取
- IBM AI ('Bob') — 下载和执行恶意软件

## 对 Hermes 的评估

### 已内置的防御优势

1. **VLM 输出不渲染给用户**（scene classification + content analysis 仅用于内部决策）
2. **ACTION_WHITELIST** 限制 scene→action 映射，不允许任意动作生成
3. **Ollama bind 127.0.0.1**（不暴露到网络，阻止远程攻击）
4. **DRY_RUN=True** 不执行真实动作
5. **否定检测+场景分类** 每帧独立验证内容

### 潜在风险（需监控）

1. 若未来 Hermes 获取"浏览网页"能力，间接提示注入攻击面打开
2. 若 Ollama 在未来版本中暴露 API 到非 localhost 端口
3. VLM prompt injection 理论上可出现在用户屏幕上（Attacker 控制显示内容）— handler 的否定检测+场景分类提供基础防御但不完备

### 过渡 DRY_RUN=False 时的安全建议

1. Verify 阶段必须是架构级 guardrail，不能仅靠配置（ChatGPT/Antigravity 教训）
2. 禁止 VLM 输出中的任意脚本/URL 执行
3. 保留多层次隔离：scene classification → action routing → whitelist → verify

## 方法论

**PromptArmor-style research 发现流程**（可复用）：
1. HN Firebase API → 获取 top stories
2. 检查每篇的 site/domain — 重点关注安全研究机构（PromptArmor、Wiz、HTB等）
3. 若文章来自安全研究机构 → browser_navigate 到文章
4. 检查页面侧边栏的"相关文章"/"threat intelligence"列表
5. 交叉发现：侧边栏列表通常包含同机构的其他同类研究，每篇 2-3 次 browser_console JS 提取即可获取完整内容
6. 比 arXiv 搜索更高效——安全研究的发布模式是"系列披露"而非单篇论文
