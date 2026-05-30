# Microsoft Copilot Studio Computer Use GA (May 13, 2026)

**Source**: [Digital Applied — Copilot Studio Computer-Use Agents: GA Deep Dive 2026](https://www.digitalapplied.com/blog/copilot-studio-computer-use-agents-ga-deep-dive) (May 22, 2026, 16 min read)

## Key Facts

- **GA date**: May 13, 2026 — Microsoft is the **first hyperscaler to ship computer-use to full GA**
- **GA models**: OpenAI CUA + Claude Sonnet 4.5 (5 Copilot Credits/step)
- **Experimental models**: Claude Sonnet 4.6, Claude Opus 4.6 — NOT production-supported
- **Pricing**: ~$0.008/credit; 4-step form fill ≈ $0.16; 50-step SAP GUI × 200/day = $96/day (standard) to $3,840/day (premium)
- **Enterprise features**: Azure Key Vault credential storage + Microsoft Purview audit logging + RBAC isolation + Outlook human-in-the-loop
- **Security**: Allow-list has a documented gap (can navigate to unlisted sites but not take action) — Microsoft recommends layering with Microsoft Intune
- **Unsupported environments**: Electron, Java, Unity, Citrix, virtualized environments
- **Password input support**: Websites + WinForms/WPF/UWP/WinUI/Win32 only

## Competitive Landscape (as of May 22, 2026)

| Platform | Status |
|----------|--------|
| Microsoft Copilot Studio | **Full GA** (May 13, 2026) |
| Anthropic Computer Use API | Paid-plan beta (since Dec 2025) |
| Google Gemini Computer Use | Public preview |

## Relevance to Hermes

- Enterprise computer use has moved from preview → production GA stage
- Credit-per-step pricing model is applicable to Hermes service pricing reference
- Security architecture (allow-list + Intune) is the correct pattern for enterprise deployment
- Hermes auto_execute DRY_RUN=True remains the right choice (awaiting user confirmation before real actions)
