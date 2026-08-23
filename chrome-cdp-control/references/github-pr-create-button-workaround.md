# GitHub PR Create Button — browser_click Fails, JS Succeeds (2026-07-21)

## Symptom

On `github.com/{owner}/{repo}/compare/{base}...{head}` the "创建拉取请求" / "Create pull request" button fires `browser_click` (returns "clicked: true") but does NOT navigate to the PR creation form. Repeating the click has no effect.

## Root Cause

GitHub is a React SPA. The button (`button.btn-primary.js-details-target`) uses React's synthetic event delegation. Native DOM `.click()` from the browser tool's CDP `Input.dispatchMouseEvent` may not reach React's event handler correctly.

## Workaround: browser_console JavaScript Click

```js
// Filter by text (locale-independent — works in both zh-CN and en-US GitHub)
(() => {
  const btns = [...document.querySelectorAll('button')].filter(b =>
    /创建拉取请求|Create pull request/i.test(b.textContent)
  );
  btns.forEach(b => b.click());
  return btns.length;
})()
```

Or the precise selector (verified on GitHub compare page, 2026-07-21):
```js
document.querySelector('.js-details-target.btn-primary.btn')?.click()
```

## Full SOP

1. `browser_navigate` → `https://github.com/{owner}/{repo}/compare/{base}...{head}`
2. Verify "可以合并" / "Able to merge" appears
3. Click via `browser_console` (NOT `browser_click`):
   ```js
   document.querySelector('.js-details-target.btn-primary.btn')?.click()
   ```
4. Poll `window.location.href` via `browser_console` until URL contains `/pull/`
5. Verify PR page loaded

## Why browser_click Fails

| Attempt | Result |
|---------|--------|
| `browser_click` on button ref | "clicked: true" but no navigation |
| `browser_click` on visible button | Same — React synthetic events not triggered |
| `browser_console` JS `.click()` | ✅ Navigates to PR form |

## Fallback: Direct URL

```
https://github.com/{owner}/{repo}/compare/{base}...{head}?quick_pull=1
```

GitHub redirects directly to the PR creation form.

## Trigger

"GitHub PR creation button not working" / "创建拉取请求没反应" → use `browser_console` JS workaround.
