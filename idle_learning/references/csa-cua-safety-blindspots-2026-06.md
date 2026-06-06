# CSA Computer-Use Agent Safety Blind Spots — June 2026

**来源**: Cloud Security Alliance (CSA) Research
**URL**: https://labs.cloudsecurityalliance.org/research/csa-research-note-computer-use-agent-safety-blindspots-20260/
**日期**: June 2026

## 核心发现

### CSA CUA 安全盲点
- **Zero-Click 数据泄露**：从 Microsoft 365 等应用实现零点击数据外泄
- **Human-in-the-Loop Bypass**：人类确认机制被视觉层攻击绕过
- **Agent 持久化行为**：agent 可以跨 session 持久化记忆和行为链

### 与 Microsoft Taxonomy v2.0 的关系
CSA 发现与微软新增的 #4 (CUA Visual Attack) 和 #6 (Zero-Click HitL Bypass) 高度互补，提供了 CSA 视角的安全盲点分析。

## Hermes 映射

| 维度 | 评估 |
|------|------|
| Direct risk | LOW（Hermes 当前无 CUA 执行能力） |
| Indirect risk | MEDIUM（screen_watcher + delegate_task 架构有类似脆弱性） |
| Action | 跟踪 CSA 后续报告，DRY_RUN=False 前加防护 |
