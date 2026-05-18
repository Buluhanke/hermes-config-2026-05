---
name: hermes-agent-hacking
description: Hermes Agent 自身修改与扩展 — 添加命令、插件热重载、目录监控、CLI hack
triggers:
  - 修改 Hermes CLI
  - 添加新命令
  - 插件热重载
  - 目录变更监控
  - Hermes 源码修改
version: 2026-05-18
---

# Hermes Agent 自身修改与扩展

## 核心原则

修改 Hermes 自身 = 修改 `cli.py` + 可选 `plugins/` 目录。
改完必须重启 gateway 进程才生效（`ps aux | grep gateway` 确认）。

## 标准工作流：添加新命令

```
1. 读 cli.py，找到现有命令的模式（如 _reload_mcp, _check_config_mcp_changes）
2. 在 HermesCLI 类中新增方法（如 _reload_plugins）
3. 注册到 COMMAND_REGISTRY（确认 'reload-plugins' 不重复）
4. 测试：触发命令，观察输出
5. 如果需要热重载功能，同时实现目录监控（见下方）
```

## 标准工作流：目录变更自动监控

模式来自 `_check_config_mcp_changes()` 的 background thread 模式：

```python
# 1. 在 __init__ 中启动监控线程
self._plugins_changes_timer = None
self._plugins_last_mtime = {}
self._start_plugins_monitoring()

# 2. 监控方法（在 class 中定义）
def _start_plugins_monitoring(self):
    self._plugins_last_mtime = self._get_plugins_mtimes()
    self._schedule_plugins_check()

def _schedule_plugins_check(self):
    self._plugins_changes_timer = threading.Timer(10.0, self._check_plugins_and_skills_changes)
    self._plugins_changes_timer.start()

def _check_plugins_and_skills_changes(self):
    # 检测变更 → reload → 打印通知 → 重新调度
    current = self._get_plugins_mtimes()
    if changed:
        print(colored('[Hermes] Plugins/Skills changed. Reloading...', 'cyan'))
        self._reload_plugins()
    self._schedule_plugins_check()

def _get_plugins_mtimes(self) -> dict:
    paths = [PLUGINS_DIR, SKILLS_DIR]
    return {p: os.path.getmtime(p) for p in paths if os.path.exists(p)}
```

## 关键实现点

### discover_and_load(force=True)
用于清空缓存重新加载所有插件：
```python
from hermes_cli.plugins import get_plugin_manager
mgr = get_plugin_manager()
mgr.discover_and_load(force=True)
```

### COMMAND_REGISTRY 注册
通过 `@root_cmd.register` 装饰器自动注册命令。确认命令名不重复：
```python
# 检查是否已注册
cmds = [c.name for c in COMMAND_REGISTRY]
assert 'reload-plugins' not in cmds
```

### 队列通知机制
不希望在命令执行时输出 → 延迟到下一轮 process_loop：
```python
self._pending_plugins_reload_note = colored('[Hermes] Plugins reloaded +X/-Y.', 'cyan')
```

## 目录结构

```
~/.hermes/
├── plugins/          # 插件目录（监控目标）
├── skills/           # 技能目录（监控目标）
└── config.yaml       # 配置文件
```

## 验证命令

```bash
# 检查 gateway 进程
ps aux | grep gateway

# 重启 gateway（改完代码后必须）
pkill -f gateway && cd ~/.hermes/hermes-agent && python3 -m hermes_cli serve &

# 验证命令注册（Python REPL）
cd ~/.hermes/hermes-agent && python3 -c "
from cli import COMMAND_REGISTRY
print([c.name for c in COMMAND_REGISTRY])
"
```

## 已知模式

| 需求 | 实现位置 |
|------|---------|
| 添加新命令 | `cli.py` - HermesCLI 类的新方法 |
| 注册命令 | `@root_cmd.register` 装饰器 → COMMAND_REGISTRY |
| 插件热重载 | `plugins.py` - `discover_and_load(force=True)` |
| 目录监控 | background `threading.Timer`，每10秒检查 |
| 延迟输出 | 队列 `_pending_xxx_note`，process_loop 下轮取用 |
| 颜色输出 | `hermes_cli.utils import colored` |

## 常见陷阱

- **改完不重启**：cli.py 修改后必须重启 gateway 进程
- **命令名重复**：注册前先检查 `COMMAND_REGISTRY`
- **fire 模块**：全局 python 无 fire，CLI 在 venv 中运行
- **目录不存在**：`os.path.exists()` 检查后再调用 `getmtime()`