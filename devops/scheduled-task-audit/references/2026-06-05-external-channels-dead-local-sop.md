# 外部渠道全死时，本地 3 路比远程 6 站更准（2026-06-05）

## 场景

用户要求"启动多 AI 站交叉问 + 联网搜来验证/修正某个运维结论"。
实际操作中**外部 3 通道大概率全死**：

| 通道 | 失败模式 | 原因 |
|---|---|---|
| 6 AI 站（Gemini/Doubao/ChatGLM/DeepSeek/ChatGPT/Grok）| `❌ <site>: tab不存在` | Chrome 浏览器被关了/没登录/会话过期 |
| `web_search` 工具 | `0 条` 结果 | 搜索引擎后端无响应或查询被限 |
| `web_extract`（走 Firecrawl）| `402 Payment Required: Insufficient credits` | 余额耗尽 |

**不要继续尝试外部** — 3 通道同时死是常态，**降到本地 4 路**。

## 本地 4 路降级（按价值排序）

### 1. 本地源码（最权威）
```bash
# 找问题对应的框架代码
grep -rn "问题关键字" ~/.hermes/hermes-agent/ 2>/dev/null
# 或定位文件
find ~/.hermes/hermes-agent -name "*.py" | xargs grep -l "关键字" 2>/dev/null
```
**比 6 AI 站准的原因**：你跑的就是这版框架，6 AI 站答的是"通用最佳实践"，可能跟你版本不一致。

### 2. 本地 errors.log（真实运行数据）
```bash
python3 -c "
from pathlib import Path
import re
from collections import Counter
text = Path.home() / '.hermes' / 'logs' / 'errors.log'
# 按异常类/模块/小时分桶
"
```
**核心问题不是"这个错误叫啥"，是"在我这台机器上跑出来啥"**。

### 3. 本地 memory + fact_store（历史经验）
```bash
session_search(query="错误模式", limit=3)
# 或直接读 ~/.hermes/memory_store.db
```
**好处**：你之前踩过的坑已经写进 fact_store 了，AI 站不知道。

### 4. 本地 git log / Obsidian（如果用户写日记）
```bash
ls ~/Obsidian/迅龙贸易/AI进化/  # 你之前的每周 W22/W23 笔记
```

## 决策表

| 3 路外部状态 | 本地 4 路 | 行动 |
|---|---|---|
| 全死 | 都通 | **直接本地分析** — 不浪费时间重试外部 |
| 全死 | 部分通 | 走通的那 1-2 路 + 标注"外部不可用" |
| 部分活 | 都通 | 外部补缺，本地兜底 |
| 部分活 | 部分通 | 拼凑够用即可 |

## 关键判断

**0 个真问题 ≠ 任务失败**。
今早 errors.log 274 条分析中，3 个看起来严重的问题经本地源码 + 本地数据交叉验证后，**全是误判**：
- tool_executor 218 条 = 框架设计的 3 次警告（不是 8 次硬停）
- config 32 条 unknown = 6/4 的历史 `alias:` 字段
- QQ 67 次 unauthorized = 你自己 EC16BFF09280BE2186FA33BB7432BCCA 的 cron 触发

**如果按外部 6 AI 站的"通用建议"，会真去修这 3 个伪问题 → 浪费 30+ 分钟**。

## 何时重试外部

- 用户明确说"我开 Chrome + 登录" → 重新跑 multi_ask_v3.py
- 用户充值 Firecrawl → 重试 web_extract
- 后端搜索引擎恢复 → 重试 web_search

否则**别主动重试** — 一次失败 = 该降级。
