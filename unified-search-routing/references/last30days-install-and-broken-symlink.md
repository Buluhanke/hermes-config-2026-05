# last30days 安装规范 + /tmp 软链翻车实录

> 这不是教程，是**踩坑历史**。任何时候怀疑"last30days 找不到了"或"升级后跑不动"，先翻这个文件。

## TL;DR

1. **正确路径**：`~/.hermes/skills/research/last30days-skill-main/skills/last30days/`（持久化 git 副本）
2. **顶层软链**：`~/.hermes/skills/research/last30days` → 上面的真路径（**别指向 /tmp**）
3. **venv**：`~/.hermes/skills/research/last30days-skill-main/.venv/`，用 `~/.local/bin/python3.12` 解释器
4. **依赖**：`uv pip install --python .venv/bin/python requests click rich`

## 2026-06-07 翻车实录（用户报告"last30days 找不到了"）

**初始诊断（错的）**：以为 `~/.hermes/skills/research/last30days/` 目录被删了。

**真实根因**（被 search 工具误报误导）：
- 顶层 `last30days` **不是目录，是软链** → `/private/tmp/last30days-skill-repo/skills/last30days`
- `/tmp` macOS 默认每 90 天清理 + 重启清空
- 软链 target 早就不存在了，但软链本身还在
- 看 `ls ~/.hermes/skills/research/` 列出来是空目录（软链断了表现如此）
- 但 **`find ~/.hermes -type d -name last30days` 能找到真副本**在 `last30days-skill-main/` 子目录

**修法**：
```bash
cd ~/.hermes/skills/research && \
  ln -sfn /Users/aimac/.hermes/skills/research/last30days-skill-main/skills/last30days last30days
```

**验证**：
```bash
readlink ~/.hermes/skills/research/last30days
# → /Users/aimac/.hermes/skills/research/last30days-skill-main/skills/last30days
ls ~/.hermes/skills/research/last30days/SKILL.md  # 必须存在
```

## venv 装依赖（关键坑 3 个）

### 坑 1：uv 默认走 hermes-agent venv（3.11）

```bash
cd ~/.hermes/skills/research/last30days-skill-main
uv pip install requests  # 装到了 ~/.hermes/hermes-agent/venv (3.11)
```

**错在哪**：uv 看到 `hermes-agent` 的 venv 路径就吸过去了，3.11 跑不了 last30days（要求 3.12+）。

### 坑 2：python3 -m venv 不会装 pip

```bash
~/.local/bin/python3.12 -m venv .venv
.venv/bin/pip install requests  # ModuleNotFoundError: No module named pip
```

**错在哪**：modern venv 默认不装 pip。

### 坑 3：直接 `uv venv` 不指定 python

```bash
uv venv  # 用默认 python（系统 3.14 或 hermes 的 3.11）
```

### 正确流程

```bash
cd ~/.hermes/skills/research/last30days-skill-main && \
  rm -rf .venv && \
  uv venv --python /Users/aimac/.local/bin/python3.12 && \
  uv pip install --python .venv/bin/python requests click rich
```

**验证**：
```bash
.venv/bin/python -c "import requests, click, rich; print('OK 3.12')"
```

## 真实验证（每次升级必跑）

```bash
cd ~/.hermes/skills/research/last30days-skill-main
.venv/bin/python skills/last30days/scripts/last30days.py "Hermes Agent" --emit=compact
```

**期望输出**：
- 60 秒左右出结果
- 至少 3 个数据源成功（GitHub / Reddit / Hacker News / YouTube）
- 不报 `ModuleNotFoundError`

**2026-06-07 实测**：
- 4 源：GitHub (8) + HN (8) + Reddit (12) + YouTube (9) 全部成功
- 60.9s 完成
- ⚠️ YouTube degraded：3/6 transcripts captured（yt-dlp 旧版，建议 `pip install -U yt-dlp`）
- ⚠️ X/Twitter 缺失：需要 `XAI_API_KEY` 或浏览器 cookies（不是 bug，是设计）

## 软链绝对禁忌

❌ **绝不用 symlink 到 `/tmp` 或 `/private/tmp`**：macOS 重启清空
❌ **绝不用 symlink 到 `~/.local/share/`**：目标通常不存在
❌ **绝不用相对路径软链**：升级或移动副本后断链

✅ **正确**：硬编码绝对路径 `/Users/aimac/.hermes/skills/research/last30days-skill-main/skills/last30days`

## 升级流程

```bash
# 1. 拉新版
cd ~/.hermes/skills/research/last30days-skill-main
git pull  # 如果有 git remote

# 2. 升级依赖
uv pip install --python .venv/bin/python -U requests click rich

# 3. 重新验证（必须）
.venv/bin/python skills/last30days/scripts/last30days.py "test" --emit=compact --quick

# 4. 检查软链
readlink ~/.hermes/skills/research/last30days
```

## 触发词速查

| 你听到 | 动作 |
|---|---|
| "last30days 找不到了" | `readlink ~/.hermes/skills/research/last30days` + `ls last30days-skill-main/skills/last30days/` |
| "升级 last30days" | 走上面"升级流程"4 步 |
| "last30days 跑不动/报 ModuleNotFound" | 检查 venv 解释器（必须是 3.12） |
| "last30days 软链断了" | 重建软链指向 `last30days-skill-main/skills/last30days` |

## 教训

- **软链+临时目录 = 定时炸弹**。所有 skill 安装路径都必须是持久绝对路径
- **uv 会吸走 venv**——任何 skill 装依赖都要 `--python .venv/bin/python` 强制
- **验证前闭嘴**——"找不到了"先 `find ~/.hermes -type d -name X` 扫全目录，别信单一工具的局部报告
