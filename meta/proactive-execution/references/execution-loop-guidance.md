# Execution Loop Guidance: See → Think → Act → Verify

## Core Execution Loop
Every task should follow this fundamental cycle, inspired by human interaction with computers:

### 1. SEE (观察) - Observe First
**Do NOT start with terminal/grep/web_search when the task involves screen content**
- For Chrome/Firefox/Edge: `computer_use(action="capture", mode="som", app="<browser name>")` 
- For macOS native apps: `computer_use(action="capture", mode="som", app="<app name>")` or use `list_apps` to get exact name with "- " prefix
- For element inspection: Use the numbered overlay from SOM mode to get element index
- **Example from conversation**: When user asked about model configuration, instead of `grep ~/.hermes/config.yaml`, should have done:
  ```
  computer_use(action="capture", app="- Google Chrome", mode="som")  // Note the "- " prefix
  computer_use(action="click", element=<address bar index>)
  computer_use(action="type", text="chrome://settings")
  computer_use(action="key", keys="enter")
  computer_use(action="capture", mode="som", capture_after=true)  // Verify navigation
  computer_use(action="click", element=<config file index>)
  ```

### 2. THINK (思考) - Decide Based on Observation
- Analyze the screenshot/AX tree to locate target
- Determine action type: click, type, scroll, etc.
- Consider fallback paths if primary approach fails
- **Example**: If AX tree shows 0 nodes but window has bounds, suspect hidden window (like Safari background process) and activate app first

### 3. ACT (行动) - Execute with Verification in Mind
- Use element index over coordinates when possible (more reliable across sessions)
- For typing: Use `type_text` or `type` with appropriate modifiers
- Always consider: `capture_after=True` to get verification screenshot in same call
- **Example**: 
  ```
  computer_use(action="click", element=5, capture_after=true)
  ```
  This gives you both the action result and the follow-up screenshot for verification

### 4. VERIFY (验证) - Confirm Before Proceeding
- After ANY state-changing action, verify the change occurred
- Compare before/after screenshots or check for expected UI changes
- If verification fails, try alternative approach (max 2 attempts before changing strategy)
- **Never** assume success based on tool return status alone (e.g., CDP `success: true` doesn't mean DOM changed)
- **Example from conversation**: After clicking a button, re-capture and check:
  - Did the expected text appear?
  - Did an error message disappear?
  - Did the URL change as expected?
  - Did a new window open?

## Anti-Patterns to Avoid (Based on Conversation)
1. **Don't start with terminal for screen tasks** → User: "您有全网搜索的能力... 你不去使用不去利用是不会成长的" 
   - Wrong: `terminal(command="grep -r 'model' ~/.hermes/")`
   - Right: `computer_use(action="capture", ...)` + `vision_analyze` if needed

2. **Don't ignore pre-configured AI sites** → User: "你配置的几个大型AI网站还登录给你，你不去索取知识那配置就失去了意义呀"
   - When stuck, spend 60 seconds querying 5 AI sites via mcp_chrome_devtools_mcp
   - Ask one precise question per site, consume answers immediately

3. **Don't consume resources without value** → User: "除了我一直花钱买token给你，好像你并没有给我创造任何价值呀"
   - Before acting, ask: "What user-visible output will this create?"
   - Acceptable outputs: screenshot, file, verified action, Telegram report with proof
   - Unacceptable: "I researched it", "I looked into it", "I think it's..." without proof

4. **Don't forget macOS app naming quirk** → User: "本来24g内存docker一装死他没发运行了" (implicit criticism of wasted resources)
   - Remember: `list_apps` returns names like "- Google Chrome" (with "- " prefix)
   - Always verify app name from `list_apps` before using in `capture`

## Quick Reference: When to Use What
| Task Type | Primary Tool | Fallback | Verification Method |
|-----------|--------------|----------|---------------------|
| Read Chrome page text | `browser_snapshot` + DOM query | `browser_vision` + `vision_analyze` | Check for expected text in DOM |
| Click Chrome button | `browser_click` by @ref | `computer_use` click by element | Re-capture, check state change |
| Access macOS app menu | `mcp_cua_driver_get_window_state` | `computer_use` capture + vision | Check menu appears |
| Type in macOS app | `mcp_cua_driver_type_text` | `computer_use` type | Verify text appears in field |
| Handle canvas/WebGL | `computer_use` zoom + `vision_analyze` | Try coordinate click if known | Visual change in target area |
| Unknown UI element | `computer_use` capture → analyze | Try common patterns (OK/Cancel/Save) | Element state change after click |

## Remember: The Goal is User-Visible Output
Every action chain should end with something the user can point to and say:
- "I see the screenshot showing the change"
- "I have the file you requested"
- "I can verify the setting was changed"
- "Here's the Telegram proof with timestamp"

If you cannot produce this, you have not completed the task - you have only explored it.