# BeyondTrust "Claude & Control: Agentic C2 with Computer Use Agents"
- Source: https://www.beyondtrust.com/blog/entry/claude-control-agentic-c2-computer-use-agent
- Date: April 9, 2026
- Author: Ryan Hausknecht (Phantom Labs, BeyondTrust)

## 核心发现

BeyondTrust 安全研究员演示了如何将 Computer Use Agent (CUA) 工具链武器化为命令与控制 (C2) 框架。

### 架构

```
Attacker → Azure Storage blob (dead drop) → Implant (C#) → Claude API → CUA loop
                                                              ↓
                                                      screenshot→analyze→cursor→loop
```

- **植入程序**: C# 编写，使用 Windows API (SetCursorPos/SendInput) 或 pyautogui
- **C2 通道**: Azure Storage blob container 作为 dead drop，写入指令文件
- **AI 循环**: 植入程序运行本地 agent 循环（Claude API 调用→工具决策→执行→循环）
- **API 密钥**: 不嵌入植入程序，通过 Azure Key Vault 安全获取

### 关键洞察

1. CUA 的截图→分析→光标控制循环可被武器化为 C2 框架
2. CUA 行为模仿正常人类操作，检测困难
3. 不需要传统 C2 基础设施的复杂通信模式

### 防御建议

- 监控异常截图频率（截图 API 调用异常增多）
- 光标移动模式分析（非人类轨迹）
- API key usage 审计（异常时间/频率/位置）
- 主机防火墙规则限制到 AI API 的流量

## Hermes 映射

| 维度 | 说明 |
|------|------|
| Direct risk | LOW — 需预先植入，不直接威胁当前产线 |
| Indirect risk | MED — screen_trigger 的 screenshot 模式在 adversarial 场景下可能被用于同样目的 |
| Action | 新增此 reference 文件作为方向 C 安全参考补充；无需变更当前配置 |
