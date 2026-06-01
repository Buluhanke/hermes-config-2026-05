# MCP Security Crisis: Systemic Design Flaws in AI Agent Infrastructure

**来源**: https://labs.cloudsecurityalliance.org/research/csa-research-note-mcp-security-crisis-20260504-csa-styled/
**作者**: Cloud Security Alliance AI Safety Initiative
**日期**: 2026-05-04

## 核心发现

### MCP STDIO Transport 根本性设计缺陷

- STDIO transport 执行 OS 命令**无 sanitization/validation**
- 任何影响 MCP 配置文件的攻击者 → 任意代码执行
- 200K+ vulnerable instances, 150M+ package downloads

### 已确认 CVE（7 个以上）

| 平台 | 严重性 |
|------|--------|
| MCP Inspector | Critical |
| LiteLLM | High |
| Cursor IDE | High |
| LibreChat | High |
| Windsurf | High |
| Flowise (April 2026) | Critical — 需紧急补丁 |

### 拓扑级问题

- 1,862 公开可访问无认证 MCP 服务器（July 2025 扫描）
- OAuth 2.1 协议定义但**标记为可选** → 服务器暴露无认证
- Anthropic 拒绝修改协议架构（责任留给下游开发者）

### Hermes 影响评估

- Hermes 使用 MCP 工具（Chrome/GitHub/Filesystem via native-mcp）
- **缓解因素**：Hermes 运行在本地 M4 Mac（非 cloud deployment）
- **风险**：如果 MCP server 配置被篡改（如通过供应链攻击），攻击面存在
- **建议**：定期审计 MCP server 配置完整性，不信任未经验证的 MCP 包
