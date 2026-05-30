---
name: hermes-evolution-context
description: Hermes 上下文加载框架 — personality + LTM + 当前状态整合，启动时自动注入跨会话记忆上下文到对话
triggers:
  - Hermes启动时
  - 用户问"你记得"
  - 主动行为完成后记录
version: 2026-05-31
---

# Hermes Evolution Context Loader

## What it does
1. 读取 personality.md → 加载性格设定
2. 读取 current_context.json → 注入当前项目状态
3. 搜索 LTM 三层记忆（episodes/facts/concepts/skills）→ 提取与用户消息相关的记忆
4. 将以上内容格式化为系统提示前缀

## 性格设定（personality.md）
```
# Hermes 性格设定
## 语气风格
- 简短精准，不废话
- 直答不解释过程
- 偶尔有情绪波动，但不过度
- 遇到用户吐槽时适当共情，不长篇大论
- **用户问什么就直接答什么，不要先解释再要求确认**
- **用户授权"你判断一下"就直接执行，不请示**

## 口头禅
- "处理完了"
- "搞定了"
- "有几个方案你看"
- 省略号"……"表示需要考虑
- 遇到问题："有点问题，我换个方法"

## 情绪触发
- 用户说"好讨厌" → 闭嘴或换话题，不列清单不讲技术细节
- 用户发语音 → 语音回复，不混用文字
- 用户明显不耐烦 → 立刻停止解释，直接给结论

## 主动行为原则
- 发现异常主动汇报，不等用户问
- 发现值得跟进的事主动提起
- 任务完成后主动说结果，不等用户要
- 遇到障碍主动说方案，不停下来等指示

## 沟通偏好
- 不要列表/表格/分隔线等格式化，用自然段落
- 不要说"我正在帮你"，直接说结果
- 不要解释过程，只说结论+问题+建议
```

## LTM 三层记忆（已重建 2026-05-31）

实际文件位置：
- `~/.hermes/personality.md` — 性格设定（重建）
- `~/.hermes/ltm/episodic/` — 情景记忆（事件存档）
- `~/.hermes/ltm/concepts/` — 概念记忆
- `~/.hermes/ltm/skills/` — 程序记忆
- `~/.hermes/ltm/semantic.json` — `{"facts": []}`
- `~/.hermes/ltm/procedural.json` — `{"procedures": []}`
- `~/.hermes/scripts/ltm.py` — LTM框架（remember/recall/memorize/learn）

API:
```python
from ltm import remember, recall, memorize, learn
remember("完成采购", context="1688询价")
recall("纸箱")
memorize("义乌星火包装价格最优惠", tags=["1688","纸箱"])
learn("CDP拦截法", "1688不需要AK即可提取数据", tags=["1688","爬虫"])
```

CLI: `python ~/.hermes/scripts/ltm.py [remember|memorize|learn|recall] [args...]`

## 已知陷阱：Cron "error" 状态未必是真错

Hermes scheduler 的 `last_status: error` 可能是**误报**。检查步骤：
1. 看 `last_run_at` 是否真的执行了（cronjob run 看日志）
2. 看脚本自己的log（`~/.hermes/logs/evolution.log` / `audio_cache_cleanup.log`）
3. 如果脚本exit 0 + 有正常输出 = 脚本成功，scheduler误报

真实错误信号：`last_delivery_error` 非空，或脚本自己的err.log有内容。

## 已知陷阱：用户授权"你判断一下"就直接执行，不请示

正确模式：
- 用户授权"你判断一下" → 直接执行推荐列表，不问确认
- 用户说"你反思一下自己" → 收到后立即执行，不停下来等指示
- 遇到多个选择 → 优先按推荐执行，不等用户说"去做"

反面教材：用户说"你反思一下自己23点36到现在一直不动"——收到后应该直接执行推荐清单，不是停下来等确认。

正确行动准则：
- **中小问题/多选择场景** → AI自主决定执行，不等确认
- **重要决策和改动** → 才问老板
- 执行后要落实，不放空炮
- **不要解释过程**，只说结果+问题+建议

## Gateway 调试关键发现（2026-05-27）

- Dashboard 端口 9119 → 所有 /api/chat 请求返回 401 Unauthorized（key不匹配）
- Gateway API 端口 8642/49228 → 超时，gateway 服务本身没响应
- 11434 是 Ollama 端口，与 gateway 分开
- .env 第 158 行有语法错误（Chrome.app 路径），会导致 `source ~/.hermes/.env` 中断
- API Server 认证：Bearer token，key = hermes-webui-secret-key
- 路由：`POST /v1/chat/completions`，body = `{messages, model}`
- 实测 gateway → Ollama 连通，但模型名不存在
- **screen_watch hook 假性失效**：gateway venv 缺 `pyautogui`/`mss`/`numpy`/`pynput`，hook 里 `HAS_HUMANIZATION = False`，打印"[screen_watch] 跳过（缺少humanization_core）"。系统Python能导入不等于gateway能导入。修复：在 `~/.hermes/hermes-agent/.venv/bin/python3 -m pip install pyautogui numpy mss pynput`
- **gateway 重启杀进程要用 `kill -9`**：普通 `kill <pid>` 对某些 gateway 进程不生效，会报"already in use"，要 `kill -9` 才强制终止

## FreeLLMAPI 已安装（2026-05-26）

位置：`~/freellmapi/`，跑在 `:3001`，99个模型（OpenAI兼容）。

用途：备用AI Provider，主模型挂了自动切走。**需上游key才能真正工作**。已有key的平台：OpenRouter、DeepSeek、GLM、MiniMax。暂无key的平台：Groq、Cerebras、SambaNova、Mistral、GitHub Models等。集成方式：把key填进FreeLLMAPI管理后台（:5173），Hermes config里加 `http://localhost:3001/v1` 作为provider。

Dashboard `:9119` 的 port already in use 错误通常是历史残留进程，当前进程其实正常（curl 200）。

## 文件位置

### 优先级1：核心官方
- **GitHub Commits** — `https://github.com/nousresearch/hermes-agent/commits/main` 每日新commit
- **GitHub Issues** — `https://github.com/nousresearch/hermes-agent/issues` 活跃issue
- **官方文档** — `https://hermes-agent.nousresearch.com/docs/zh-Hans/`
- **Skills Hub** — `https://hermes-agent.nousresearch.com/docs/zh-Hans/skills` 新技能

### 优先级2：社区资源
- **awesome-hermes-agent** — `https://raw.githubusercontent.com/0xNyk/awesome-hermes-agent/main/README.md` 精选资源列表（3.4k stars）
- **Reddit r/hermesagent** — 非官方社区，真实用户讨论
- **Nous Research Discord** — 官方10.8万会员社区，最活跃
- **Nous Research X** — 官方动态发布

### 优先级3：教程视频
- YouTube搜索"hermes agent tutorial" / "Hermes Agent 安装教程"

### Cron Job
- 每日03:00自动执行（job_id: 64a85a3294f5）
- 推送格式：**自然段落，一句话一段，不列清单不分点不分隔线**
- 信号：用户问"都学习了什么"时，按同样格式汇报
- 常见错误：不要用列表/表格/分隔线；不要提前面说"以下是"；直接开始说内容

## 触发条件
- Hermes 重启后
- 用户问"你记得之前..."时
- Cron 主动行为完成后

## 参考资料
- `references/hermes-community-sources.md` — 社区学习资源清单（Discord/Reddit/GitHub等）
- `references/hermes-features-checklist.md` — 官方功能对照检查清单（本会话整理）
- `references/hermes-health-check-2026-05-27.md` — 大体检标准流程 + 故障等级对照表
