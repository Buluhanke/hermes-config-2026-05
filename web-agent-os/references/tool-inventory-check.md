# 工具清单核查记录

## 快速核查命令

```python
# 在 hermes-agent 目录运行
cd ~/.hermes/hermes-agent && python3 -c "
import sys; sys.path.insert(0, '.')
from tools.registry import discover_builtin_tools, registry
discover_builtin_tools()
all_tools = sorted(registry.get_all_tool_names())
print(f'总工具数: {len(all_tools)}')
cats = {}
for t in all_tools:
    ts = registry.get_toolset_for_tool(t)
    cats.setdefault(ts, []).append(t)
for ts, tools in sorted(cats.items(), key=lambda x: -len(x[1])):
    print(f'[{ts}] {len(tools)}个')
"
```

## 68工具分类（2026-05-31）

| 工具集 | 数量 | 核心工具 |
|--------|------|---------|
| browser | 14 | snapshot/navigate/click/type/vision + **dom工具4个** |
| kanban | 9 | list/create/complete/heartbeat等 |
| hermes-yuanbao | 5 | query/send_dm/send_sticker |
| feishu_drive | 4 | add_comment/list_comments/reply |
| homeassistant | 4 | list_entities/list_services/get_state |
| file | 4 | patch/read_file/search_files/write_file |
| skills | 3 | skill_manage/skill_view/skills_list |
| browser-cdp | 2 | browser_cdp/browser_dialog |
| terminal | 2 | process/terminal |
| web | 2 | web_extract/web_search |
| 其他单工具 | 14 | send_message/computer_use/cronjob等 |

## DOM工具核查

```python
# 直接调用验证
from tools.dom_tools import dom_snapshot, dom_click, dom_fill, dom_tabs
t = dom_tabs()  # ✅ 列出标签页
s = dom_snapshot()  # ✅ 提取元素
```

## dispatch() 空跑说明

registry.dispatch() 在独立子进程执行，环境变量不传递。
- 空跑失败 ≠ 实际故障（进程隔离机制）
- 真正可用性看 browser_snapshot / dom_snapshot / session_search / skills_list

## websockets 修复

```bash
uv pip install websockets==15.0.1 -p ~/.hermes/hermes-agent/.venv/bin/python
```
- 修复 browser_dialog_tool 加载失败
- dom_tools 不受影响（自己的 WS 连接）