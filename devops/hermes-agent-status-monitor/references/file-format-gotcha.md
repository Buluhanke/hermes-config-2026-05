# `.agent_status.json` 文件结构详解

## 背景

`agent_status.py` 是个跨 agent 共享脚本，靠**单一扁平 JSON 文件**做公告板：`announce` 加条目，`list` 列条目，**没有任何内建命名空间或 schema 校验**。

这意味着任何 agent 写这个文件时如果没有约定结构，就会相互污染。

## 文件实际结构（运行 2-3 次后）

```json
{
  "telegram-12345": {
    "platform": "telegram",
    "message": "📡 14:30 状态广播：...",
    "category": "general",
    "updated": "2026-06-07T14:30:12",
    "pid": 12345
  },
  "qq-67890": {
    "platform": "qq",
    "message": "...",
    "category": "general",
    "updated": "...",
    "pid": 67890
  },
  "unknown-78899": {
    "platform": "unknown",
    "message": "📡 14:30 状态广播：...",
    "category": "general",
    "updated": "2026-06-07T14:30:33",
    "pid": 78899
  },
  "_meta": {
    "last_broadcast": {
      "time": "14:30",
      "iso": "2026-06-07T14:30:33",
      "agents_online": 2,
      "platforms": ["telegram", "qq"],
      "core_skills": 13,
      "total_skills": 190,
      "skill_list": [
        "1688-open-platform-api",
        "1688-search-data-extract",
        "...",
        "yolo-object-detection"
      ],
      "new_skills": ["hermes-new-skill"],
      "removed_skills": [],
      "report": "📡 Hermes 状态广播 @ 14:30\n👥 ..."
    }
  }
}
```

## 为什么必须用 `_meta` 命名空间

**反面教材**（首次运行踩坑）：

```json
{
  "last_broadcast": {
    "time": "14:30",
    "report": "..."
  },
  "unknown-78899": {...}
}
```

`list` 命令跑出来：

```
Agent ID                       平台         状态                        更新时间
  last_broadcast               ?                                    3秒前
  unknown-78899                unknown    📡 14:30 状态广播...        3秒前
  共 2 个 agent 在线
```

`共 2 个` —— 多了一个假 agent。原因：

1. `load_status()` 直接返回整个 dict 给你
2. `list_agents()` 用 `for agent_id, info in sorted(status.items())` 遍历，**不知道也不在乎这个 key 是不是 agent**
3. 它还会把这个 `last_broadcast` 当真 agent 一样尝试 `datetime.fromisoformat()` 解析 `updated` 字段（不存在，捕获异常后 time_str 为空）

## 正确做法

1. 元数据塞进 `_meta` 这个**带下划线前缀的命名空间**（约定俗成，未来好识别）
2. 读取真实 agent 列表时用 `if k == "_meta": continue` 过滤
3. 写文件时只把真 agent 条目放顶层，元数据放 `_meta` 里

## `_meta.last_broadcast` 字段说明

| 字段 | 类型 | 用途 |
|------|------|------|
| `time` | str `"14:30"` | 显示用 |
| `iso` | str ISO 8601 | 机器解析、排序 |
| `agents_online` | int | 5 分钟内更新的真实 agent 数 |
| `platforms` | list[str] | 去重后的平台列表 |
| `core_skills` | int | 当前存在于注册表的核心技能数 |
| `total_skills` | int | 注册表总技能数 |
| `skill_list` | list[str] | **baseline diff 用**，存当前注册表所有 skill name |
| `new_skills` | list[str] | `current - prev` |
| `removed_skills` | list[str] | `prev - current` |
| `report` | str | 完整可发的报告文本 |

## 写入代码模板

```python
status = json.loads(STATUS_FILE.read_text()) if STATUS_FILE.exists() else {}

# 分离真实 agents 和元数据
agents = {k: v for k, v in status.items() if k != "_meta"}
prev_meta = status.get("_meta", {}).get("last_broadcast", {})
prev_skill_list = set(prev_meta.get("skill_list", []))

# 算 diff
current_skills = set(registry["skills"].keys())
new_skills = sorted(current_skills - prev_skill_list)
removed_skills = sorted(prev_skill_list - current_skills)

# 重构
new_status = dict(agents)
new_status["_meta"] = {
    "last_broadcast": {
        "time": datetime.now().strftime("%H:%M"),
        "iso": datetime.now().isoformat(),
        "agents_online": len(online_agents),
        "platforms": sorted(set(a["platform"] for a in online_agents)),
        "core_skills": core_count,
        "total_skills": len(current_skills),
        "skill_list": sorted(current_skills),
        "new_skills": new_skills,
        "removed_skills": removed_skills,
        "report": report_text,
    },
    "generated": datetime.now().isoformat(),
}
STATUS_FILE.write_text(json.dumps(new_status, ensure_ascii=False, indent=2))
```

## 其它 agent 读取这份文件时的兼容策略

- **不要假设 `_meta` 存在** —— 旧版可能没有，老 agent 只会写顶层 agent 条目。读时 `status.get("_meta", {})` 容错。
- **不要假设 `skill_list` 存在** —— 首次或老版本无 baseline 时 `prev_skill_list = set()`，diff 全是新增属正常。
- **不要修改别人的 agent 条目** —— 你只该写自己的 `agent_id`（基于 `HERMES_PLATFORM + pid`），不要清理别人的。
