---
name: skill-portable-packaging
description: Flatten a Hermes skill into one portable .md for transfer.
category: skill-authoring
---

# Skill Portable Packaging (single-file skill flatten)

## Trigger
User wants a skill bundled into **ONE file** to move to another Hermes/machine: "打包成一个文件" / "只要一个文件" / "装到另一台电脑/另一台 Hermes". Produces a single `.md` with 思路 → 记忆/踩坑 → 使用说明 → 完整脚本 (every script embedded as a fenced code block).

## When to use vs not
- **Use** for cross-machine handoff of a working skill, especially "只要一个文件" requests.
- **NOT** for internal backup → `cp -R` + tar.gz (see source skill's `distributable_skill_packaging` reference).
- **NOT** for hub publishing → `hermes skills install` / skill-creator flow.

## The working method (single-file flatten)
1. **Gather source**: read `SKILL.md`, every `scripts/*.js|*.scpt|*.py`, and the key `references/*.md` worth preserving.
2. **De-hardcode every absolute path** (the #1 cause of "换机器全断"):
   - **Python**: infer from the file's own location:
     ```python
     HERE0 = os.path.dirname(os.path.abspath(__file__))
     SKILL0 = os.path.dirname(HERE0)
     VENV_SP = os.path.join(SKILL0, 'venv', 'lib', 'python3.14', 'site-packages')
     USER_DATA = os.path.join(SKILL0, 'venv', 'drission_user_data')
     ```
   - **AppleScript**: resolve path-relative-to-self:
     ```applescript
     set myPath to POSIX path of (path to me)
     set scriptsDir to do shell script "dirname " & quoted form of myPath
     set x to read (POSIX file (scriptsDir & "/foo.js")) as «class utf8»
     ```
   - **Node/JS**: use `__dirname` / `path.dirname(__filename)`; never hardcode a user home.
   - In **usage examples**, write `~/skillname/scripts/...` (home-relative), never `/Users/aimac/...`.
3. **Embed as fenced code blocks**: one `### filename` heading + ```` ```lang ```` block per file. Keep exact filenames so the installer can save each block to the right path.
4. **Front-load the human part**: 思路 → 记忆/踩坑 → 使用说明 → 完整脚本. A reader on the other machine installs from the top without scrolling to the code.
5. **Verify zero leaks before delivering**:
   ```bash
   grep -rn "/Users/aimac" <output.md>   # must return 0
   ```
   In a builder script, assert `txt.count("/Users/aimac") == 0`.

## Pitfalls
- **Path leak**: any surviving `/Users/xxx` or `/home/xxx` silently breaks the receiving machine. Always grep-verify; treat non-zero count as build failure.
- **Regex backslash doubling**: SOURCE scripts contain regex with `\d \s \.` — copy them **verbatim as bytes**. Corruption only appears if you REGENERATE scripts via `write_file`/heredoc (see 1688 skill 坑22). Copy, don't regenerate.
- **AppleScript `path to me` needs co-located files**: it resolves to the `.scpt`'s own location, so tell the installer to extract ALL blocks into one `scripts/` folder together — otherwise the relative `read` fails.
- **Never bundle credentials/login state**: exclude `drission_user_data`, `.venv`, `storage-state.json`; the receiver re-logs in themselves. Hardcoding a path to someone else's login dir is both a leak and a security mistake.
- **Keep MCP servers / external repos OUT**: a single-file skill stays lean — reference integration steps, don't inline a whole MCP server unless explicitly asked.

## Support files
- `references/worked_example_1688.md` — concrete before/after de-hardcode substitutions from the real 1688 找品 skill flatten, plus the builder verification snippet.
