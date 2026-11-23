---
name: dogfood
description: "web app探索性QA 找bug留证据出报告。Use when 给web产品做探索性测试找bug"
version: 1.0.0
author: Teknium (teknium1), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [qa, testing, browser, web, dogfood]
    related_skills: []
---

# Dogfood: Systematic Web Application QA Testing

## Overview

This skill guides you through systematic exploratory QA testing of web applications using the browser toolset. You will navigate the application, interact with elements, capture evidence of issues, and produce a structured bug report.

## Prerequisites

- Browser toolset must be available: use `browser_exec` (Python code with helpers `new_tab`, `goto_url`, `js`, `fill_input`, `cdp`, `page_info`, `capture_screenshot`); optional `browser` MCP tools if configured
- A target URL and testing scope from the user

## Inputs

The user provides:
1. **Target URL** — the entry point for testing
2. **Scope** — what areas/features to focus on (or "full site" for comprehensive testing)
3. **Output directory** (optional) — where to save screenshots and the report (default: `./dogfood-output`)

## Workflow

Follow this 5-phase systematic workflow:

### Phase 1: Plan

1. Create the output directory structure:
   ```
   {output_dir}/
   ├── screenshots/       # Evidence screenshots
   └── report.md          # Final report (generated in Phase 5)
   ```
2. Identify the testing scope based on user input.
3. Build a rough sitemap by planning which pages and features to test:
   - Landing/home page
   - Navigation links (header, footer, sidebar)
   - Key user flows (sign up, login, search, checkout, etc.)
   - Forms and interactive elements
   - Edge cases (empty states, error pages, 404s)

### Phase 2: Explore

For each page or feature in your plan:

1. **Navigate** to the page:
   ```
   browser_exec(code="new_tab(\'https://example.com/page\')")
   ```

2. **Take a snapshot** to understand the DOM structure:
   ```
   browser_exec(code="print(page_info())")
   ```

3. **Check the console** for JavaScript errors:
   ```
   browser_exec(code="cdp(\'Runtime.evaluate\', ...)")
   ```
   Do this after every navigation and after every significant interaction. Silent JS errors are high-value findings.

4. **Take an annotated screenshot** to visually assess the page and identify interactive elements:
   ```
   capture_screenshot()  # 保存后用 vision_analyze 看图,识别交互元素与视觉问题
   ```
   `capture_screenshot()` 返回截图路径;把路径传给 `vision_analyze` 即可获得 AI 描述。

5. **Test interactive elements** systematically:
   - Click buttons and links: `browser_exec(code="js(\'document.querySelector(...).click()\')")`
   - Fill forms: `browser_exec(code="fill_input(selector, \'test input\')")`
   - Test keyboard navigation: `browser_exec(code="cdp('Input.dispatchKeyEvent', type='keyDown', key='Tab')")` then `keyUp` (same for Enter)
   - Scroll through content: `browser_exec(code="js(\'window.scrollBy(...)\')")`
   - Test form validation with invalid inputs
   - Test empty submissions

6. **After each interaction**, check for:
   - Console errors: `browser_exec(code="cdp(\'Runtime.evaluate\', ...)")`
   - Visual changes: `capture_screenshot()` + vision_analyze
   - Expected vs actual behavior

### Phase 3: Collect Evidence

For every issue found:

1. **Take a screenshot** showing the issue:
   ```
   capture_screenshot()  # 再用 vision_analyze 看图
   ```
   Save the `screenshot_path` from the response — you will reference it in the report.

2. **Record the details**:
   - URL where the issue occurs
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Console errors (if any)
   - Screenshot path

3. **Classify the issue** using the issue taxonomy (see `references/issue-taxonomy.md`):
   - Severity: Critical / High / Medium / Low
   - Category: Functional / Visual / Accessibility / Console / UX / Content

### Phase 4: Categorize

1. Review all collected issues.
2. De-duplicate — merge issues that are the same bug manifesting in different places.
3. Assign final severity and category to each issue.
4. Sort by severity (Critical first, then High, Medium, Low).
5. Count issues by severity and category for the executive summary.

### Phase 5: Report

Generate the final report using the template at `templates/dogfood-report-template.md`.

The report must include:
1. **Executive summary** with total issue count, breakdown by severity, and testing scope
2. **Per-issue sections** with:
   - Issue number and title
   - Severity and category badges
   - URL where observed
   - Description of the issue
   - Steps to reproduce
   - Expected vs actual behavior
   - Screenshot references (use `MEDIA:<screenshot_path>` for inline images)
   - Console errors if relevant
3. **Summary table** of all issues
4. **Testing notes** — what was tested, what was not, any blockers

Save the report to `{output_dir}/report.md`.

## Tools Reference

| `browser_exec` helper | Purpose |
|------|---------|
| `new_tab(url)` / `goto_url(url)` / `wait_for_load()` | Open and load a page |
| `js("document.body.innerText")` / `page_info()` | Read DOM/text state (prefer over screenshots) |
| `fill_input(sel, text)` / `click_at_xy(x,y)` / `js("el.click()")` | Interact |
| `cdp("Runtime.evaluate", params)` | Raw CDP when helpers are insufficient |
| `capture_screenshot()` | Screenshot evidence (save path, inspect via vision when needed) |

## Tips

- **Always check `browser_exec(code="cdp(\'Runtime.evaluate\', ...)")` after navigating and after significant interactions.** Silent JS errors are among the most valuable findings.
- **Use `annotate=true` with `capture_screenshot()`** when you need to reason about interactive element positions or when the snapshot refs are unclear.
- **Test with both valid and invalid inputs** — form validation bugs are common.
- **Scroll through long pages** — content below the fold may have rendering issues.
- **Test navigation flows** — click through multi-step processes end-to-end.
- **Check responsive behavior** by noting any layout issues visible in screenshots.
- **Don't forget edge cases**: empty states, very long text, special characters, rapid clicking.
- When reporting screenshots to the user, include `MEDIA:<screenshot_path>` so they can see the evidence inline.
