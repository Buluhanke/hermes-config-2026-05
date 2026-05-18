# Hermes Agent Hacking Session Log

## 2026-05-18: 实现 /reload-plugins 命令 + 目录监控

### 目标
为 Hermes Agent 添加插件热重载能力和目录变更自动监控。

### 核心实现

**1. `_reload_plugins()` 方法（cli.py ~line 10090）**

核心调用：
```python
def _reload_plugins(self):
    from hermes_cli.plugins import get_plugin_manager
    mgr = get_plugin_manager()
    # discover_and_load(force=True) 清空缓存重新加载所有插件
    mgr.discover_and_load(force=True)
    
    # 打印 diff（新增/移除插件数）
    # 队列通知延迟到下一 process_loop
```

**2. 目录监控（background threading）**

参考现有模式：`_check_config_mcp_changes()`

关键代码模式：
```python
self._plugins_changes_timer = None
self._plugins_last_mtime = {}

def _schedule_plugins_check(self):
    self._plugins_changes_timer = threading.Timer(10.0, self._check_plugins_and_skills_changes)
    self._plugins_changes_timer.start()

def _check_plugins_and_skills_changes(self):
    current = self._get_plugins_mtimes()
    changed = any(t != self._plugins_last_mtime.get(p) for p, t in current.items())
    if changed:
        print(colored('[Hermes] Plugins/Skills changed. Reloading...', 'cyan'))
        self._reload_plugins()
    self._schedule_plugins_check()  # 重新调度，继续监控
```

**3. `COMMAND_REGISTRY` 注册**

确认注册前检查：
```python
from cli import COMMAND_REGISTRY
cmds = [c.name for c in COMMAND_REGISTRY]
# 'reload-plugins' not in cmds
```

### 验证结果

```
✅ /reload-plugins registered
✅ /reload-skills present
✅ /reload-mcp present
✅ discover_and_load(force=True) available
```

### 文件修改

- `~/.hermes/hermes-agent/cli.py` — 添加 `_reload_plugins()` 和目录监控逻辑
- 改完后需重启 gateway：`pkill -f gateway && cd ~/.hermes/hermes-agent && python3 -m hermes_cli serve &`

### 生效方式

- **手动触发**：`/reload-plugins` 命令立即重载
- **自动监控**：每 10 秒检查 `~/.hermes/plugins/` 和 `~/.hermes/skills/` 目录变更，有变更自动重载

### 关键引用

- 模式来源：`cli.py` 中 `_check_config_mcp_changes()` 的 background thread 模式
- `discover_and_load(force=True)`：来自 `hermes_cli/plugins.py` 的 PluginManager
- 颜色输出：`from hermes_cli.utils import colored`