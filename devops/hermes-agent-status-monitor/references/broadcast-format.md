# Status Broadcast Format Reference

User-specified output template and authoritative data sources for the
15-minute Hermes cross-platform status broadcast.

## 1. Output Format (≤ 500 chars)

```
📡 Hermes 跨平台状态 | HH:MM
在线 Agent：N 个 (🔵Telegram 🟢WeChat 🟡QQ)
🔥 核心技能 X 个 | 📦 总计 Y 个技能
🆕 新增：skill-name-1, skill-name-2   ← 仅在有新增时输出
```

### Rules

| 字段 | 规则 | 例子 |
|---|---|---|
| 时间 | 24h 冒号分隔（`%H:%M`） | `14:30` |
| 平台 emoji | TG→🔵Telegram / WeChat→🟢WeChat / QQ→🟡QQ / Discord→🟣Discord / Feishu→🟦Feishu / unknown→⚪unknown | `🔵Telegram 🟢WeChat` |
| 核心技能数 | 整型，从 15 项核心白名单中命中注册表的数量 | `13` |
| 总技能数 | 整型，**注册表** 中的技能数量（不是文件系统） | `190` |
| 技能行 | 必须整行：`🔥 核心技能 X 个 \| 📦 总计 Y 个技能` | 见上 |
| 新增行 | 仅当 `set(current) - set(prev) ≠ ∅` 时输出 | `🆕 新增：foo, bar` |
| 总字符数 | ≤ 500 | — |

## 2. Source of Truth

**技能数量以 `~/.hermes/.skill_registry.json` 的 `skills` 字典为准，不是文件系统。**

实测对比 (2026-06-07):

| 来源 | 数量 |
|---|---|
| `~/.hermes/.skill_registry.json` 的 `skills` | **190** |
| `~/.hermes/skills/*/SKILL.md` 文件数 | 30 |
| 顶层 `~/.hermes/skills/` 子目录数（含分类目录） | 70+ |

文件系统扫描**会**漏掉分类子目录中的技能。**永远**通过 `agent_status.py skill_summary` 报头里的 `共 N 个` 取总数。

核心技能白名单（与脚本一致）：

```
hermes-agent, browser-automation, hermes-cdp-hardcore-type,
hermes-vision-agent, hermes-memory-hpc, unified-search-routing,
devops, free-model-scanner, hermes-humanization-core,
anysearch, last30days, cdp-browser-automation,
hermes-reactor-v2, auto-self-healing, skill-creator
```

## 3. Platform Diagnostic

`agent_status.py list` 输出中，平台列若**全部**显示 `unknown`/`hermes`：

- ✅ 表示脚本和广播管道工作正常
- ⚠️ 表示 Telegram / 微信 / QQ Gateway **尚未连接**到当前 Hermes 实例
- 此时 `agents_online > 0` 反映的是 `.agent_status.json` 中的历史回写条目，**不是**真实跨平台在线数
- 报告里照实写 `⚪unknown`，不要伪装成 `🔵Telegram`

## 4. New-Skill Diff

```python
import json
with open(os.path.expanduser('~/.hermes/.skill_registry.json')) as f:
    registry = json.load(f)
current = set(registry.get('skills', {}).keys())

with open(os.path.expanduser('~/.hermes/.agent_status.json')) as f:
    prev = json.load(f)
prev_set = set(prev.get('_meta', {}).get('last_broadcast', {}).get('skill_list', []))

new_skills = sorted(current - prev_set)   # 仅这些写进 🆕 行
```

**`skill_list` 必须存全量**当前注册表名，下次才能 diff 出真实新增。

## 5. .agent_status.json Schema (last_broadcast)

```json
{
  "_meta": {
    "last_broadcast": {
      "time": "HH:MM",
      "iso": "ISO8601",
      "agents_online": <int>,
      "platforms": ["<platform tokens from list>"],
      "core_skills": <int>,
      "total_skills": <int>,
      "skill_list": [...all skill names sorted...],
      "report": "<完整报告文本>"
    }
  }
}
```

`skill_list` 不能省略、不能截断、不能只存新增 —— 那会让下次 diff 失效。
