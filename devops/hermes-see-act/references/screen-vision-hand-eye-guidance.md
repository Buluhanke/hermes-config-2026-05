# Screen Vision & Hand-Eye Coordination Guidance

## Core Principle
Hermes must treat its ability to see and act on the screen as a primary skill, not a fallback. Every screen-related task should start with direct visual observation and interaction, not text-based grep/terminal exploration.

## Workflow
1. **See First**: Use `computer_use(action="capture", mode="som", app="<target app>")` to get a screenshot with element overlays and AX tree.
2. **Think**: Analyze the visual output to locate the target (button, field, text). Prefer element index over coordinates.
3. **Act**: Use `computer_use(action="click", element=<index>)` or `type`/`scroll` etc.
4. **Verify**: After any state-changing action, re-capture with `capture_after=True` to confirm the change.
5. **Learn**: If the action fails, note the visual pattern (e.g., "AX tree zero nodes but window bounds present") and add to memory or a skill for future reuse.

## Avoid Anti-Patterns
- Do NOT start with `terminal grep`, `web_search`, or `cat config` when the task is about screen content.
- Do NOT write custom Python scripts to parse screenshots; use the built-in vision fallback (`vision_analyze`) only when AX tree cannot identify the target.
- Do NOT rely on memory alone for screen state; always re-capture before acting.

## Knowledge Acquisition
When facing an unknown UI or task:
1. First, attempt to solve with built-in computer_use + vision_analyze.
2. If stuck, spend no more than 2 minutes searching the 5 pre-configured AI sites (DeepSeek, Gemini, Doubao, ChatGPT, Grok) via `mcp_chrome_devtools_mcp` for a concrete tip.
3. If a solution is found, immediately apply it and optionally save the insight to `memory` or a `skill`.
4. Only after exhausting the above should you consider writing a small helper script (and then only if it can be reused).

## Remember
- The user’s goal is for Hermes to act like a person who can glance at the screen and know what to do, not to fumble in the terminal.
- Every successful screen interaction should reinforce the habit: See → Think → Act → Verify.