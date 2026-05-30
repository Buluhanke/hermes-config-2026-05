# AI Computer Use 三层架构与 Hermes 定位（2026-05-31）

**来源**：AI Magicx Complete Guide 2026 — "AI Computer Use and Desktop Agents: The Complete Guide for 2026"

## 三层架构

| Level | 名称 | 可靠性 | 技术方案 | 代表产品 |
|-------|------|--------|---------|---------|
| 1 | API integration | 95%+ | Zapier/Make/自定义代码 | — |
| 2 | Browser automation | 85-95% | AI 控制浏览器，填表单、导航网页 | OpenAI Operator, Google Mariner |
| 3 | OS-level desktop control | 70-90% | AI 看到屏幕像素，直接控制鼠标键盘 | Claude Computer Use, Meta My Computer, **Hermes** |

**Hermes 定位**：Level 3（OS-level desktop control），与 Claude Computer Use 同级。

## 可靠性差距的根因

OS-level desktop control（Level 3）比 Browser automation（Level 2）低 10-20pp，因为：
- 基于像素的理解存在不确定性
- GUI 框架多样性（Qt/WPF/Cocoa/Web...）
- 状态验证困难（agent 需要确认动作效果）
- 非标准 UI 框架适配成本高

## 对 Hermes 的实践意义

**1688 采购场景**：Browser automation（Level 2）比 OS-level control 更稳定：
- mcp_chrome_* 工具链属于 Level 2 方案
- 可靠性高 15-25pp
- 适合：表单填写、页面导航、数据抓取

**双轨并行策略**：
- Browser automation（Level 2）：高可靠性，1688 等 web-based 任务优先
- OS-level dry-run（Level 3）：实验性，桌面软件场景探索
- 两者互补，不是替代关系

## Desktop Agent 通用失败模式

- CAPTCHAs / 滑动验证码（1688 是阿里自研壁垒，NopeCHA 不支持）
- 动态 UI（JavaScript SPA 频繁变化）
- 多因素认证（2FA）
- 非标准 GUI 框架

## CLI/Desktop Agents 2026 SOTA

详见 `computer-use-agents-leaderboard-2026-06-03.md` 和 `computer-use-agents-2026-06-02.md`。

**关键基准**：
- WebVoyager: Browser-Use (hybrid) **89.1%** vs Agent-E (accessibility-only) 73.1%
- OSWorld: 人类 72.36%，最佳 agent ~12.24%（grounding 差距大）
- AndroidWorld: Mobile-use 达 100%

**2026 技术共识（Hybrid 架构）**：
- Screenshot-Based（通用但 token 高、延迟高）
- Accessibility Tree（高效精确但平台受限）
- DOM/View Hierarchy（网页最精准但仅限 Web）
- 生产系统默认 DOM/accessibility，vision 降级到非标准布局
