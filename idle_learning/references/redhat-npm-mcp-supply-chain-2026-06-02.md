# Red Hat npm Supply Chain Attack — MCP Packages Targeted

**Source**: GitHub Issue #492 (RedHatInsights/javascript-clients)
**HN Score**: 640 pts (June 2, 2026 #1 story)
**Verification**: browser_navigate + browser_snapshot to GitHub issue
**Tags**: supply-chain, npm, MCP, direction-C, real-world-validation

## Summary

29 npm packages in the `@redhat-cloud-services/` scope were compromised with malicious versions. Each package had 3 compromised versions following the pattern `X.Y.1`, `X.Y.2`, `X.Y.4` (systematically skipping patch `.3` — suggesting organized compromise, not random).

## MCP-Specific Relevance

Three compromised packages are **MCP servers**:
- `@redhat-cloud-services/hcc-feo-mcp` (0.3.1, 0.3.2, 0.3.4)
- `@redhat-cloud-services/hcc-kessel-mcp` (0.3.1, 0.3.2, 0.3.4)
- `@redhat-cloud-services/hcc-pf-mcp` (0.6.1, 0.6.2, 0.6.4)

This is **direct real-world confirmation** of the MCP Tool Poisoning attack surface documented in `ai-agent-security-2026-attack-surfaces.md`. The threat model is no longer theoretical.

## Affected Package Categories

| Category | Count | Examples |
|----------|-------|---------|
| Frontend components | 8 | `frontend-components`, `frontend-components-config`, `frontend-components-utilities`, etc. |
| Client libraries | 5 | `compliance-client`, `config-manager-client`, `entitlements-client`, `host-inventory-client`, etc. |
| MCP servers | 3 | `hcc-feo-mcp`, `hcc-kessel-mcp`, `hcc-pf-mcp` |
| Utilities | 3 | `javascript-clients-shared`, `eslint-config-redhat-cloud-services`, `frontend-components-testing` |
| Others | 10 | `chrome`, `notifications-client`, `patch-client`, `rbac-client`, `insights-client`, etc. |

## Impact on Hermes

| Dimension | Assessment |
|-----------|-----------|
| Direct risk | LOW — Hermes tools are defined locally, MCP servers configured in config.yaml are user-approved |
| Indirect risk | MED — If Hermes ever auto-discovers MCP servers (via mcp.so registry or similar), this attack pattern becomes a direct threat |
| Action | Reference this incident in direction C security monitoring. No config change needed. |
| Lesson | Supply chain attacks on npm packages used by MCP servers is a real, validated attack vector — not theoretical |

## Attack Pattern

The compromised packages:
- Systematically skipped patch version `.3` (X.Y.1, X.Y.2, X.Y.4) — likely maintainer/OIDC credential theft
- Targeted Red Hat Cloud Services infrastructure users (high-value enterprise target)
- Affected both client-side (frontend-components) and server-side (MCP servers) packages

## References
- GitHub Issue: https://github.com/RedHatInsights/javascript-clients/issues/492
- StepSecurity Blog: https://www.stepsecurity.io/blog/multiple-redhat-cloud-services-npm-packages-compromised (timed out on access)
- Related: `references/ai-agent-security-2026-attack-surfaces.md` — MCP Tool Poisoning theoretical analysis (this incident validates that analysis)
