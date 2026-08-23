# WeChat/Weixin iLink Bot Architecture — Critical Facts

## Core Limitation
**iLink is 1 token = 1 WeChat account — NOT 1:N like Telegram**

- Telegram: 1 bot token = unlimited users (platform bot model)
- WeChat iLink: 1 token = exactly 1 specific personal WeChat account
- Other users must add this WeChat account as friend to interact with the bot

## Implication for Multi-Bot Setup
| Scenario | Feasible? | Notes |
|----------|-----------|-------|
| 1 WeChat → N Hermes agents (same account, diff users) | ✅ Yes | Route by sender openid to different agent profiles |
| 1 WeChat → N Hermes processes (same account) | ❌ No | iLink token can only be used by one process |
| N WeChat accounts → N Hermes | ✅ Yes | N iLink tokens = N independent bots |
| N WeChat → 1 Hermes (multi-account) | ✅ Yes | `hermes-weixin-multi` plugin or `WEIXIN_ACCOUNTS` env |

## Hermes Multi-Agent Routing (Same WeChat, Different Users)
Config: `routes` in config.yaml with `peer.id` matching sender openid.
```yaml
agents:
  assistant: {}
  coder: { home_dir: ~/.hermes/profiles/coder }
routes:
  - match: { platform: weixin, peer: { kind: direct, id: "用户A的openid" } }
    agent: coder
  - match: { platform: weixin, peer: { kind: direct, id: "用户B的openid" } }
    agent: assistant
```
This works because WeChat DMs from different users route to different agents.

## Key Reference
- Hermes Issue #29144: `self.adapters[Platform.WEIXIN]` hard-coded to single instance
- Storage layer already multi-account ready: `weixin/accounts/*.json` exists but not loaded at runtime
- Community plugin: `hyonex/hermes-weixin-multi` — one Hermes, unlimited WeChat accounts

## OpenClaw vs Hermes on WeChat
OpenClaw solved the multi-account problem by running parallel poll loops per account.
Hermes storage layer supports it; runtime adapter loading is the blocker.
