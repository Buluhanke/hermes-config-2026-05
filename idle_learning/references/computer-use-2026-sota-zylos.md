# Computer Use & GUI Agents 2026 — Zylos Research SotA 综述

**来源**：`browser_navigate` 抓取 zylos.ai/research/2026-02-08-computer-use-gui-agents（2026-06-01 完全抓取，全 26000+ 字符内文）

**核心价值**：2026 年 Computer Use 领域最全面的生产就绪 vs 研究级分水岭判断，验证 Hermes 混合架构方向正确。

---

## 一、生产就绪 vs 研究级（2026年2月分界线）

| 类别 | 状态 | 数据 |
|------|------|------|
| Web Browser Agents | ✅ 生产就绪 | OpenAI Agent 87% JS站点，Google Mariner 83.5% WebVoyager |
| Desktop OS Automation | ❌ 仍研究级 | OSWorld SOTA 20.58%（Agent-S + GPT-4o），人类 72.36% |
| Mobile Agents | ✅ 有突破 | Mobile-use 100% AndroidWorld；DigiRL 67.2% |
| 跨应用工作流 | ❌ 最薄弱 | WindowsWorld 所有 agent < 21% |
| 金融交易 | ❌ 无人信任 | Apple 形式验证 + 多因素确认是最佳实践 |

**核心判断**：Web 可投产（需要监督），Desktop/Mobile 快速进步但仍需人工监督。

---

## 二、混合架构 — 2026 行业共识

Pure vision / pure DOM / pure accessibility tree 都有**致命缺陷**：

| 方法 | 优势 | 致命缺陷 |
|------|------|---------|
| Screenshot Vision | 通用，适配任何界面 | 高 token 成本（单图 15K+ tokens），精度低 |
| Accessibility Tree | 快，准确，token 少 | 覆盖缺口（canvas/自定义UI），平台不统一 |
| DOM Manipulation | 最精确，低延迟 | Web-only，反爬手段多 |

**Hermes 已对齐**：computer_use（accessibility tree）+ screen_watcher（vision）+ Chrome MCP（DOM），三轨混合。

**Hermes 缺失环节**：确定性脚本（deterministic script）做关键路径验证和回放。

**Benchmark 数据**：
- Browser-Use（混合）WebVoyager **89.1%** vs Agent-E（仅accessibility）**73.1%**
- Operator（纯 vision）87% JS 站点 — 足够强的模型也可以纯 vision

---

## 三、验证 = 必选项（2026 行业共识）

**"Fire and forget doesn't work."**

### 三层验证体系
1. **Pre-action verification**: VeriSafe Agent — 基于逻辑推理（非概率），失败时提供反馈让 agent 纠正
2. **Post-action visual confirmation**: 关键操作后重新截图验证（如点击"提交"后检查内容是否发布）
3. **User approval for irreversible**: 不可逆操作必须经过用户确认

### 对 Hermes auto_execute 的启发
- 当前 handler 有 Observe→Plan→Dispatch，**缺少 Verify** 阶段
- GUI-Agent-Harness 的 4-phase loop（Observe→Verify→Plan→Dispatch）可直接借鉴
- negation detection = 基础版 post-action verification

---

## 四、生产级权限模型（Silent/Logged/Confirmed/Blocked）

行业最佳实践（Anthropic + 开源社区共识）：

| 级别 | 操作 | 示例 |
|------|------|------|
| **Silent** | Read-only | 截图分析、场景分类、信息检索 |
| **Logged** | Write to file | 日志写入、文件修改（记录到 activity feed） |
| **Confirmed** | Shell/Network/Cross-app | shell 执行、API 调用、跨项目访问 |
| **Blocked** | Credentials/System | 凭据访问、系统修改、金融交易 |

**对 Hermes DRY_RUN=False 的意义**：
- 这是 DRY_RUN=False 切换需要的**动作分级框架**
- 当前 auto_execute 的 ACTION_WHITELIST 可以映射为 Silent 级（只读动作）
- Confirmed 级动作需要 handler 中实现确认机制（Telegram 推送确认？）

---

## 五、WindowsWorld 基准（arXiv 2604.27776, Apr 2026）

**参数**：
- 181 个任务，平均 5.0 子目标，17 款常见桌面应用
- 78% 是跨应用任务
- 16 种职业场景生成

**关键结果**：
- 所有 agent 在跨应用任务上 **< 21%**
- ≥3 应用跳转的任务几乎全部卡在早期子目标
- 执行效率远低于人类步数

**对 Hermes**：auto_execute 当前只覆盖单场景，跨场景跳转是更难的问题。优先做好单场景单步执行。

---

## 六、DART-GUI-7B

- OSWorld **42.13%**（+14.61% absolute gain over base model）
- RL with verifiable rewards：GUI grounding 天然适合 RL（accuracy-based rewards 可 verify）
- 对 Hermes：未来 DRY_RUN=False 的执行数据可作为 RL reward 信号

---

## 七、Other Notable HN Articles (2026-06-01)

| Score | Title | Relevance |
|-------|-------|-----------|
| 306 | Dav2d (jbkempf.com) | 视频编码，不直接相关 |
| 226 | Cloudflare Turnstile WebGL fingerprint | 已知，auto_execute anti-detection 场景 |
| 209 | London's Free Roof Terraces | 不相关 |
| 103 | 1-Bit Bonsai Image 4B Generation | 图像生成，有限相关 |
| 87 | Creatine & Alzheimer's | 不相关 |
| 81 | United 767 Bluetooth alert | 不相关 |
