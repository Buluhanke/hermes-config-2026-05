---
name: mac-maintenance
description: "Mac例行维护 brew升级清repo倒垃圾。Use when 维护Mac开发环境清理空间"
triggers:
- Use when mac maintenance
trigger_type: general
---

# Mac Maintenance

Use when Peter asks for Mac cleanup, maintenance, or package/repo refresh.

## Run

1. Homebrew:

```bash
brew update && brew upgrade
```

2. Repos under `~/Projects`:

```bash
for repo in ~/Projects/*/.git; do
  dir=${repo:h}
  git -C "$dir" status --short --branch
  git -C "$dir" pull --ff-only
done
```

Skip dirty repos unless Peter explicitly asked to handle them. Report skipped paths.

3. Empty Trash:

```bash
osascript -e 'tell application "Finder" to empty trash'
```

4. Finish with terse counts:

- brew: upgraded / already current
- repos: pulled / skipped / failed
- trash: emptied / failed
