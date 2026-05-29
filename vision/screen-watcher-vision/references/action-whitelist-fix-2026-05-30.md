# screen_trigger_handler ACTION_WHITELIST 补全修复
**日期**：2026-05-30 01:06
**问题**：auto_execute dry-run 日志始终为0
**根因**：ACTION_WHITELIST 缺少 "desktop"、"calculator"、"other" 三个场景

## 背景

2026-06-02 已修复 get_scene_type() 从 smolvlm2 切换到 qwen3-vl:2b，场景分类输出英文单词（desktop/calculator/other）。但 ACTION_WHITELIST 在 2026-05-30 初次创建时只包含 5 个场景，未同步更新。

## 修复内容

在 `~/.hermes/scripts/screen_trigger_handler.py` 的 ACTION_WHITELIST 中添加：

```python
ACTION_WHITELIST = {
    "browser": ("wininfo", None),
    "wechat": ("wininfo", None),
    "1688": ("wininfo", None),
    "dingtalk": ("wininfo", None),
    "telegram": ("wininfo", None),
    "desktop": ("wininfo", None),   # 新增（2026-05-30）
    "calculator": ("wininfo", None), # 新增（2026-05-30）
    "other": ("wininfo", None),     # 新增（2026-05-30）
}
```

## 验证

下次 screen_watcher 触发时，日志应出现：
```
[AUTO-EXEC-DRY] Would execute: wininfo for scene=desktop
```

## 遗留问题

### 1. wininfo 命令不在 PATH
wininfo 不在 PATH，DRY_RUN 模式只记录不执行所以未暴露。切换 DRY_RUN=False 前需将 wininfo 替换为实际存在的命令（如 `cliclick`），或在 hermes_desktop_rpa.py 中确保 wininfo 子命令可用。

### 2. osascript 超时（cron 环境限制）
详见 `references/hermes-desktop-rpa-osascript-timeout-2026-06-02.md` — osascript 超时是**环境限制**，前台桌面 session 外无法解决。DRY_RUN=False 切换必须在有活跃桌面 session 的环境。

### 3. RPA_SCRIPT 路径已修正（2026-06-02）
`screen_trigger_handler.py` 中 RPA_SCRIPT 路径已从 `skills/autonomous-ai-agents/` 改为 `autonomous-ai-agents/`。