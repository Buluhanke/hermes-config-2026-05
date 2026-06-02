# MCP Security CVEs — June 2026

## Flowise MCP RCE — CVE-2026-40933
- **Source**: CSO Online, csoonline.com/article/4179309
- **Affected**: Flowise MCP implementation (stdio servers)
- **Impact**: One-click RCE — affects everything Flowise can reach
- **Type**: Ghost commands execution via MCP stdio
- **Hermes relevance**: LOW — Hermes doesn't use Flowise, but MCP stdio architecture is shared
- **Action**: Monitor Flowise CVE patches, note stdio as high-risk pattern

## Anthropic MCP SDK RCE — OX Security Disclosure
- **Source**: gridthegrey.com/posts/anthropic-mcp-design-vulnerability-enables-rce-threatening-ai-supply-chain/
- **Affected**: All implementations using Anthropic MCP SDK
- **Root cause**: Architectural vulnerability in MCP SDK design
- **Impact**: Arbitrary RCE across supply chain
- **Hermes relevance**: MED — Hermes MCP integration pattern may share similar design issues
- **Action**: Review Hermes MCP tool calling implementation for similar attack surface

## LangFlow MCP RCE — CVE-2026-33017
- **Source**: LinkedIn (CPO taxiarchis 93), Ox Security research
- **Affected**: LangFlow MCP server
- **Root cause**: Flawed build_public_tmp endpoint — unauthenticated arbitrary command execution
- **Timing**: Exploitable BEFORE patch applied
- **Hermes relevance**: LOW — Hermes doesn't use LangFlow, but build_public_tmp pattern is common
- **Action**: Audit any Hermes tool that accepts build/tmp paths from external sources

## Risk Matrix

| CVE | Direct Risk | Indirect Risk | Action |
|-----|-------------|--------------|--------|
| CVE-2026-40933 | LOW | MED (stdio pattern) | Monitor |
| Anthropic MCP SDK | LOW | MED (shared arch) | Review MCP implementation |
| CVE-2026-33017 | LOW | LOW | Audit tmp path handling |

## Broader MCP Security Context (from CSA MCP Crisis 2026-05-04)
- 7 CVEs in MCP ecosystem
- 200K+ vulnerable MCP server instances
- STDIO RCE is the primary attack vector
- Hermes currently uses direct function calls, not MCP — risk contained
