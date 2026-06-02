# Hermes 版本升级误报 — `.update_check` 缓存陷阱

## 问题现象

`hermes --version` 显示 `Update available: N commits behind`，但 git 确认 HEAD 已是最新的。

```bash
$ hermes --version
Hermes Agent v0.15.1 (2026.5.29)
Update available: 151 commits behind — run 'hermes update'
```

```bash
$ git -C ~/.hermes/hermes-agent log --oneline -1
a5aecf2 feat(kanban): gate notifier watcher on dispatch_in_gateway

$ git -C ~/.hermes/hermes-agent log --oneline origin/main -1
a5aecf2 feat(kanban): gate notifier watcher on dispatch_in_gateway  # 同一个commit，HEAD=origin/main
```

**结论**：本地已是最新的，但版本命令误报。

## 根因

`~/.hermes/.update_check` 缓存升级检查结果：

```json
{"ts": 1780361406.390379, "behind": 151, "rev": null, "ver": "0.15.1"}
```

缓存有效条件：
1. timestamp 距离现在 < `_UPDATE_CHECK_CACHE_SECONDS`（6小时）
2. 缓存的 `rev` 与嵌入 rev 相同
3. 缓存的 `ver` 与当前 `VERSION` 相同

三个条件都满足时直接返回 `cached["behind"]` 而不查 git。升级后若不清理缓存，持续误报。

## 精准诊断

```bash
# 确认真实状态（不依赖 hermes --version 缓存）
cd ~/.hermes/hermes-agent
git fetch origin main
git log --oneline origin/main..HEAD  # 无输出 = 对齐
git log --oneline HEAD..origin/main  # 无输出 = 对齐

# 查看缓存
cat ~/.hermes/.update_check
```

## 修复

```bash
rm ~/.hermes/.update_check
hermes --version  # 应显示 "Up to date"
```

## 触发场景

| 场景 | 是否误报 |
|------|---------|
| 手动 git fetch && checkout origin/main 后立即查版本 | ✅ 误报 |
| `hermes update` 执行后立即查版本 | ✅ 误报 |
| 源码克隆后从未清理缓存 | ✅ 误报（缓存ts可能已失效但rev仍匹配） |

## 源码定位

`hermes_cli/banner.py`:
- `_check_via_local_git()` — 查 git rev 数
- `get_update_result()` — 读写 `.update_check` 缓存