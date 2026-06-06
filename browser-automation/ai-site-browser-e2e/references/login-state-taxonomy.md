# AI Site Login-State Taxonomy (2026-06-05)

## How to verify login state

Do NOT rely on tab titles alone. A tab showing the correct title may still be on a login page or a temporary-incognito state. The correct approach:

1. `browser_cdp(method="Target.createTarget", params={"url": "<site>"})` — open a new tab (or use existing tab)
2. `browser_navigate(url)` — navigate to the site's main chat URL
3. `browser_snapshot(full=false)` — read the AX tree
4. Look for account-indicator elements in the sidebar/header area

## The 6 sites — verified login indicators (2026-06-05)

| Site | Logged-in AX signal | Logged-out AX signal |
|------|--------------------|--------------------|
| **Poe** | `button "K H"` in sidebar + user greeting text | `button "登录"` / `button "注册"` |
| **Claude** | `StaticText "Hey there, <name>"` + `button "<name>, Settings"` | `link "Sign up"` / `link "Log in"` |
| **Gemini** | `link "Google Account: <name> (<email>)"` in sidebar | `button "登录"` + no account link |
| **豆包** | `button "用户<number>"` in sidebar + history list | Login modal overlay, no history |
| **智谱清言** | `StaticText "GLM-5.1"` in chat UI (logged-in model badge) | `link "登录"` / `link "注册"` in header |
| **Grok** | Chat UI with `textbox "Ask Grok anything"` + model picker | `button "登录"` + `button "注册"` in nav bar |

## Common login-state patterns

**Definitely logged in:**
- User's name/email in sidebar or header (`link "K H (hanlukebu@gmail.com)"`)
- Personalized greeting (`"Hey there, keke"`)
- Chat history list visible in sidebar
- Account-specific model badge (`GLM-5.1`, plan tier labels like `Free plan`)

**Definitely NOT logged in:**
- Login/register buttons visible in nav
- "Sign up for free" / "Log in" as primary CTA
- Empty chat UI with no history on a site that normally shows history
- Redirect to `/login` or `/sign_in` URL

**Ambiguous / needs more checks:**
- Paywall modal: shows chat UI but `button "Upgrade"` is prominent — user may be on free tier but still logged in
- Temporary chat mode: `button "Temporary chat"` visible — user is logged in but using incognito mode

## Workflow: bulk-verify all 6 logins

```python
import sys
sys.path.insert(0, "/Users/aimac/.hermes/hermes-agent")
from hermes_tools import browser_cdp, browser_navigate

SITES = [
    ("Poe", "https://poe.com", "button \"K H\""),
    ("Claude", "https://claude.ai", "keke"),
    ("Gemini", "https://gemini.google.com/app", "K H"),
    ("豆包", "https://www.doubao.com/chat", "用户320735"),
    ("智谱清言", "https://chatglm.cn/main/alltoolsdetail", "GLM-5.1"),
    ("Grok", "https://grok.com/", "登录"),
]

for name, url, logged_out_signal in SITES:
    # Open new tab
    tab = browser_cdp(method="Target.createTarget",
        params={"browserContextId": "...", "url": url})
    browser_navigate(url=url)
    # Get AX tree — check for user account indicator
    body_text = browser_console(expression="document.body.innerText")
    if logged_out_signal in body_text:
        status = "❌ NOT LOGGED IN"
    else:
        status = "✅ LOGGED IN"
    print(f"{name}: {status}")
```
