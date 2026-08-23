# Worked example: flattening the 1688 找品 skill into a single portable .md

Source: `~/.hermes/skills/1688-search/1688-search-cn-gb-region-skill/` (USER-OWNED — do not patch in place; this is the package-out copy).

## Step A — AppleScript de-hardcode (run_search.scpt / check_batch_optimized.scpt)

Before (breaks on any machine ≠ /Users/aimac):
```applescript
set jsExtract to read (POSIX file "/Users/aimac/.hermes/skills/1688-search/1688-search-cn-gb-region-skill/scripts/extract_ids.js") as «class utf8»
```

After (path-relative-to-self):
```applescript
set myPath to POSIX path of (path to me)
set scriptsDir to do shell script "dirname " & quoted form of myPath
set jsExtract to read (POSIX file (scriptsDir & "/extract_ids.js")) as «class utf8»
```
Same pattern for `check_batch_optimized.scpt` (`check_spec.js` instead of `extract_ids.js`).

## Step B — Python de-hardcode (login_1688.py)

Before:
```python
VENV_SP = '/Users/aimac/.hermes/1688-mcp/venv/lib/python3.14/site-packages'
USER_DATA = '/Users/aimac/.hermes/1688-mcp/repo/drission_user_data'
```

After (infer from __file__, works on any machine):
```python
HERE0 = os.path.dirname(os.path.abspath(__file__))
SKILL0 = os.path.dirname(HERE0)
VENV_SP = os.path.join(SKILL0, 'venv', 'lib', 'python3.14', 'site-packages')
USER_DATA = os.path.join(SKILL0, 'venv', 'drission_user_data')
```

## Step C — Builder verification (python3)

Concatenate header + each embedded script block, then:
```python
txt = "".join(parts)          # all sections + code blocks
assert txt.count("/Users/aimac") == 0, "hardcoded path leaked!"
```
Real run result for the 1688 mini package: `WROTE /Users/aimac/Desktop/1688找品技能mini.md bytes 47976` / `hardcoded /Users/aimac occurrences: 0`.

## Step D — Embedding order in the single .md
1. 核心思路 (why this approach beats API/headless/MCP-search)
2. 记忆/踩坑大全 (the 29 pitfall lines, condensed)
3. 使用说明 (prereqs, install `mkdir -p ~/skill/scripts`, extract blocks, run commands, verify)
4. 完整脚本 (one `### filename` + fenced block per file: extract_ids.js, verify_carton.js, verify_carton_matrix.js, price_clean3.js, price_clean2.js, check_spec.js, run_search.scpt, check_batch_optimized.scpt, drive_playwright.js, login_1688.py)

## Note on the matrix-size fix
The package included the matrix-SKU fix (`verify_carton_matrix.js`: long×wide axis `8x8（长宽）` + height axis `9cm（高）` combine to 8×8×9cm; regex must allow full-width open paren `（`). That fix lived in the user-owned skill's `scripts/` and is carried forward verbatim in the package.
