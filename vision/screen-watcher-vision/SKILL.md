---
name: screen-watcher-vision
description: Screen watcher vision handler - screen变化检测后用smolvlm2分析屏幕内容
trigger: screen_watcher触发screen_trigger_handler后调用
---

# Screen Watcher Vision Handler

## 核心能力
使用 smolvlm2-agentic-gui 分析屏幕截图，进行场景分类和内容理解。

## 已知问题：smolvlm2 幻觉
smolvlm2 是一个小模型，存在明显幻觉问题，尤其在简单场景（计算器、空白桌面）上会生成不存在的湖光山色等描述。

### 缓解策略
1. **强制选项 prompt**：给出明确的选项列表，限制回答范围
2. **低温参数**：temperature=0.0 减少随机性
3. **场景前缀**：在 prompt 开头加场景描述，强制模型聚焦
4. **时间戳验证**：提示"这是截图而不是风景照"

## 推荐 Prompt 模板

**场景分类**
```
[这是一张真实截图，不是风景照]
看这张截图，判断场景类型。
选项：浏览器/微信/桌面/计算器/京东/1688/钉钉/其他
只说一个词，不要其他内容。
```

**内容分析**
```
[这是一张macOS截图]
截图里有什么需要处理的内容？有没有弹窗、消息、订单？
用中文回答，1-2句话。
如果什么都没有，说"无需处理"。
```

## 触发过滤（重要）
screen_trigger_handler 必须在调用视觉分析前先做场景类型过滤。**不要分析以下类型**：
- 桌面壁纸 / 壁纸切换
- 通知中心（Notification Center）
- 任务栏空白区域
- 截屏本身（避免循环）
- 同一张图像的微小变化（如光标移动但不改变内容）

**判断方法**：先读取截图元数据（尺寸、颜色分布），若判定为静态背景图或与上次分析结果高度相似（SSIM > 0.95），跳过分析直接返回"无需处理"。

**Cooldown 机制**：screen_trigger_handler 在 60 秒内同一场景不重复分析。日志中若出现对"湖景/山脉/岩石"等风景描述的重复分析，说明触发过滤已失效，需检查：
1. screen_watcher 是否重复 spawn handler（Popen 无去重）→ 需在 screen_watcher 加进程级互斥
2. 场景白名单是否正确识别静态背景图

## Handler 重复 spawn 问题（2026-05-26 实测已修复）

**症状**：日志中对同一张"湖景"重复分析几十次，每次屏幕微小变化都触发新的 handler 进程。

**根因**：screen_watcher.py 的 `touch_trigger()` 每次检测到变化都 `subprocess.Popen` 启动新 handler，不检查是否有 handler 已在运行。cooldown 逻辑是进程级别的，跨进程无效。

**解法**：在 screen_watcher 加运行标记文件 `.handler_lock`，启动前检查，运行完删锁。详见 `references/screen-watcher-handler-lock-2026-05-26.md`。

## 紧急度分流（2026-05-26 新增）

screen_trigger_handler 对分析结果进行紧急度分级，非紧急内容不推 Telegram：

- **urgent**：关键词命中（错误/崩溃/失败/异常/警告/500/404 等）→ 立即推 Telegram
- **normal**：关键词命中（新消息/订单/付款/发货/回复等）→ 推 Telegram
- **silent**：无关键词 → 静默，仅记日志

关键词库路径：`~/.hermes/scripts/screen_trigger_handler.py` 第171-174行。

## 性格文件（2026-05-26 新增）

Hermes 性格设定已写入 `~/.hermes/hermes-agent/personality.md`，包含口头禅/情绪触发/主动行为原则。对话系统提示应加载此文件形成固定风格。

## 当前项目上下文（2026-05-26 新增）

跨会话追踪文件：`~/.hermes/current_context.json` — 记录最近项目/订单/待办/用户提过的事，对话开始时扫描相关关键词自动带上上下文。

## 温度参数
```json
{"temperature": 0.0, "num_gpu": 0}
```

## 文件路径
- 截图：`~/.hermes/screenshots/current.png`
- 分析缓存：`/tmp/hermes_trigger_vision.jpg`
- 日志：`~/.hermes/logs/screen_analysis.log`
- Ollama地址：`http://localhost:11434/api/generate`
- 模型：`ahmadwaqar/smolvlm2-agentic-gui:latest`