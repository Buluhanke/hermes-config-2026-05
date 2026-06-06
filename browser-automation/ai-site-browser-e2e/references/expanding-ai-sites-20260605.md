# Expanding AI Sites — 2026-06-05 Verification Results

## Workflow (don't skip step 1)
1. **Always probe existing logins first** — the user's Chrome likely already has most sites logged in. Navigate and read AX tree for account indicators. Never assume or ask the user to re-login sites already authenticated.
2. **Bulk-open unknown sites** via `browser_navigate(url)` — resilient because it auto-acquires the fresh CDP context (see `browserContextId` staleness pitfall in parent SKILL.md).
3. **One-time login for any remaining unauthenticated sites** — tell user once, cookies persist in Chrome profile.

## Full verified roster (11 sites, 2026-06-05)

| # | Site | URL | Login | Account | CF? |
|---|------|-----|-------|---------|-----|
| 1 | Gemini | gemini.google.com/app | ✅ | K H (hanlukebu@gmail.com) | No |
| 2 | Doubao | doubao.com/chat | ✅ | 用户320735 | No |
| 3 | ChatGLM | chatglm.cn/main/alltoolsdetail | ✅ | GLM-5.1 | No |
| 4 | DeepSeek | chat.deepseek.com | ✅ | (unverified) | No |
| 5 | ChatGPT | chatgpt.com | ✅ | keke | No |
| 6 | Grok | grok.com | ✅ | lukebu (hanlukebu@gmail.com) | No |
| 7 | Perplexity | perplexity.ai | ✅ | K H | **Yes → resolves ~5s** |
| 8 | Kimi | kimi.moonshot.cn | ✅ | 登月者6283 | No |
| 9 | Tongyi | tongyi.com | ✅ | Qwen1929 | No |
| 10 | Copilot | copilot.microsoft.com | ❌ | Guest | No |
| 11 | Poe | poe.com | ✅ | K H | **Yes → resolves ~5s** |

CF = Cloudflare challenge fires on first navigation. Not a login failure — page auto-resolves after ~5s; re-navigate if needed.

## Key lessons from this session

### browserContextId staleness (critical)
`Target.getTargets` returns a `browserContextId` that changes every time the CDP connection is re-established. When stale:
- `Target.createTarget` → `Failed to find browser context with id ...`
- `Target.getTargets` → returns only service workers, zero page tabs

**Always use `browser_navigate(url)`** for opening new tabs — it uses the currently active CDP connection and auto-resolves the context. Only use `Target.createTarget` directly when you already have a fresh context ID from a recent `Target.getTargets` call.

### Cloudflare on first navigation
Perplexity and Poe trigger Cloudflare on first open per session. The AX tree shows "正在进行安全验证" with a CAPTCHA iframe. This is not a login issue. Wait ~5s and re-navigate — the challenge resolves automatically and the logged-in state appears.

### Kimi URL is kimi.moonshot.cn (not kimi.com)
The redirect from kimi.com lands on the login wall. Always use the full `kimi.moonshot.cn` domain.
