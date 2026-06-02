# MCP Security CVEs — 2026-06-03

## CVE-2026-23744 — MCPJam Inspector RCE

- **CVE ID**: CVE-2026-23744
- **来源**: Strobes VI / ZDI May 2026 Security Update Review
- **产品**: MCPJam inspector（MCP server 本地开发平台）
- **受影响版本**: ≤ 1.4.2
- **漏洞类型**: Remote Code Execution (RCE)
- **技术详情**: MCPJam inspector 是本地优先的 MCP server 开发平台，支持实时调试和检查 MCP server 行为。受影响版本在处理特定输入时允许远程代码执行。
- **攻击向量**: 攻击者通过恶意构造的 MCP 请求触发 inspector 组件中的代码执行漏洞
- **Hermes 风险**: **LOW** — Hermes 不使用 MCPJam，无 MCP server 开发依赖
- **缓解**: 升级到 MCPJam > 1.4.2

## CVE-2026-42271 — LiteLLM Unauthenticated RCE（链式利用）

- **CVE ID**: CVE-2026-42271
- **来源**: Horizon3.ai
- **产品**: LiteLLM（AI gateway/proxy，用于统一管理多个 LLM 提供商）
- **受影响版本**: 受限版本（需结合 Starlette auth bypass）
- **漏洞类型**: Unauthenticated Remote Code Execution
- **攻击链**: 
  1. CVE-2026-48710 (BadHost): Starlette < 1.0.1 的 Host header auth bypass
  2. CVE-2026-42271 (LiteLLM): 利用 BadHost 绕过认证，执行任意代码
- **技术详情**: 
  - LiteLLM 部署通常依赖 Starlette/FastAPI 作为 HTTP 框架
  - 当 Starlette 版本存在 BadHost 漏洞时，攻击者可通过单个畸形 HTTP header 绕过 LiteLLM 的认证层
  - 绕过后可通过 LiteLLM 的 /api/chat/completions 或 /key/generate 等端点执行系统命令
- **攻击场景**: 
  - 内网环境下：直接攻击未修复的 LiteLLM 实例
  - 外网场景：通常 LiteLLM 部署在有认证保护的网络中，但 BadHost 可绕过部分认证检查
- **Hermes venv 状态**: 
  - starlette=1.2.1 ✅（已修复 CVE-2026-48710 BadHost）
  - Hermes 不使用 LiteLLM（使用自己的 gateway 架构）
- **Hermes 风险**: **LOW** — Hermes 有自己的 httpx/uvicorn 栈，不依赖 LiteLLM；starlette 已修复
- **缓解**: 
  1. 升级 Starlette ≥ 1.0.1
  2. 不要将 LiteLLM 直接暴露在公网
  3. 使用 API key 认证 + IP 白名单

## 关联 MCP CVE 速查

| CVE | 产品 | 严重性 | Hermes 影响 | 记录位置 |
|-----|------|--------|-------------|---------|
| CVE-2026-27825 | MCP Atlassian Server | Critical | LOW | csa-mcp-security-crisis-2026-06-02.md |
| CVE-2025-6514 | mcp-remote | Critical (9.6) | MED | direction-b-cves-2026-06-03.md |
| CVE-2026-23744 | MCPJam Inspector | High | LOW | 本文件 |
| CVE-2026-42271 | LiteLLM | Critical | LOW | 本文件 |
| CVE-2026-48710 | Starlette (BadHost) | High | LOW (已修复) | badhost-cve-2026-48710-starlette-2026-06-02.md |

## 总结

**链式利用成为主流**：
- CVE-2026-48710 + CVE-2026-42271 组合：先利用 Starlette auth bypass 绕过认证，再利用 LiteLLM RCE 获取系统权限
- 这种"认证绕过 + 代码执行"的链式模式是 2026 年 AI 安全漏洞的典型特征
- 防御重点：不能只修一个 CVE，需要同时修依赖链上的所有漏洞

**Hermes 架构优势**：
- Hermes 使用自己的 httpx/uvicorn 栈，不依赖 Starlette（虽然 starlette 在 venv 中但不是 gateway 核心组件）
- 不使用 LiteLLM、MCPJam 等第三方 AI gateway
- 攻击面相对较小

**持续监控建议**：
- 关注 ZDI/Zero Day Initiative 每月安全更新回顾
- Horizon3.ai 的 CVE 分析文章
- MCP 安全生态仍在快速成熟中，新 CVE 预计会持续出现
