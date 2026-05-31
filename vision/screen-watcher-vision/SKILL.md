---
name: screen-watcher-vision
description: Screen watcher vision handler - screen变化检测后用smolvlm2分析屏幕内容
trigger: screen_watcher触发screen_trigger_handler后调用
---

# Screen Watcher Vision Handler

## 核心能力
使用 qwen3-vl:2b 分析屏幕截图，进行场景分类和内容理解。
（2026-06-02：smolvlm2-agentic-gui 从 Ollama registry 下线，完全切换到 qwen3-vl:2b）

## 已知问题：smolvlm2 幻觉
smolvlm2 是一个小模型，存在明显幻觉问题，尤其在简单场景（计算器、空白桌面）上会生成不存在的湖光山色等描述。

### 关键发现：smolvlm2 适合场景分类（2026-05-30 修正）

**⚠️ 2026-06-02 切换回 qwen3-vl:2b 的结论已被推翻（2026-05-30 实测）**

**症状（2026-05-30 实测）**：`get_scene_type()` 使用 smolvlm2-agentic-gui：
```
python3 /tmp/test_scenetype.py → Scene type: 'browser', Time: 17.9s ✅
```

同一截图 qwen3-vl:2b 响应超时（60s+，Read timeout）。

**根因**：qwen3-vl:2b 在 900x506 缩略图上仍需 46s+ 响应，远超 cron 60s 限制。
smolvlm2-agentic-gui 在相同分辨率下 17.9s 返回准确分类结果。

**结论**：smolvlm2 适合 `get_scene_type()`（场景分类），qwen3-vl:2b 因延迟过高无法在此场景使用。

### 重要说明：单模型架构（2026-06-02 确认，2026-05-31 实测完善）

**smolvlm2-agentic-gui 已从 Ollama registry 永久下线**（pull 返回 404，2026-06-02 确认），
两个函数已统一使用 qwen3-vl:2b：

| 函数 | 模型 | 速度 | 用途 |
|------|------|------|------|
| `get_scene_type()` | qwen3-vl:2b | **35-47s** (2026-06-01产线实测) | 场景分类，返回英文单词 |
| `ask_screen()` | qwen3-vl:2b | **~35s** | GUI 内容分析 |
| 合计 | — | **70-84s** | 单次完整处理周期 |

**⚠️ 换模型后的陷阱：分支逻辑也是死代码（2026-05-31 发现并修复）**
`on_trigger()` 的场景分支原匹配中文关键词（`"浏览器" in scene_type`），但 `get_scene_type()` 始终返回英文（`"browser"`）。这意味着：
- smolvlm2 时代：分支逻辑从未生效，全部走 `else` 分支
- 换模型后：必须把分支逻辑改为英文精确匹配才能生效
- 修复方式：`if scene_type in ("browser", "jingdong", "1688"):` 替代 `if "浏览器" in scene_type:`

**过去的两模型对照（历史记录，不再适用）：**
之前曾尝试 qwen3-vl:2b（ask_screen）+ smolvlm2（get_scene_type）的分工架构，但 smolvlm2 已永久下线，此分工已废弃。

### ⚠️ 场景分类 smolvlm2 幻觉缓解（2026-05-30 实测有效）

**验证有效的 prompt**（smolvlm2 输出 "browser" 等英文单词，无乱码）：
```python
"What is shown in this screenshot? Choose ONE from: browser, wechat, desktop, calculator, jingdong, 1688, dingtalk, telegram, other. Reply with ONLY the word."
```

温度 0.1，30s timeout，smolvlm2 在 scene classification 任务上实测无幻觉。

**模型状态（2026-05-31 实测更新 — 修复了 get_scene_type 仍指向已下线 smolvlm2 的 bug）：**
| 函数 | 模型 | 速度 | 状态 |
|------|------|------|------|
| `get_scene_type()` | qwen3-vl:2b | ~24s | **在用**（smolvlm2 已从 Ollama registry 下线，2026-06-02确认） |
| `ask_screen()` | qwen3-vl:2b | ~24s | **在用**，GUI内容分析 |
| smolvlm2-agentic-gui | — | — | ❌ 已从 Ollama registry 下线（pull 返回 404），不再可用 |

⚠️ **smolvlm2-agentic-gui 确认退役**（2026-06-07）：registry.ollama.ai 返回 404，模型已不在 Ollama 官方库。qwen3-vl:2b 已接管所有视觉分析任务。

⚠️ **qwen3-vl:2b 在 900x506 缩略图上响应 ~24s**，虽比 smolvlm2 的 18s 慢，但 GUI 专用能力完整，且本地可用。

**场景分类 prompt**（qwen3-vl:2b 使用，temperature 0.0 确保确定性输出）：
```python
"Classify this screenshot into EXACTLY ONE of: browser, wechat, desktop, calculator, jingdong, 1688, dingtalk, telegram, other. Reply with ONLY the single word."
```

**⚠️ 2026-05-31 修复**：原 smolvlm2 prompt 在代码中仍被使用，但模型已不存在。同时 prompt 输出格式（英文单词）与分支逻辑的中文关键词不匹配——两个 bug 叠加导致分支逻辑形同虚设。修复后全链路统一使用英文场景名。

**⚠️ smolvlm2-agentic-gui 永久下线（2026-06-02 确认退役）**：
smolvlm2-agentic-gui 已从 Ollama registry 永久删除，pull 返回 EOF + 404。
**结论**：smolvlm2 不再可用。qwen3-vl:2b 是当前唯一可用视觉模型，已接管所有视觉分析任务。

**现象**：`curl http://127.0.0.1:11434/api/tags` 返回的模型列表中找不到 `ahmadwaqar/smolvlm2-agentic-gui`。

**临时方案**：
1. `ollama pull ahmadwaqar/smolvlm2-agentic-gui:latest`（需 github.com 恢复）
2. 或改用备选模型（见下方备选表）

**备选模型**（当 qwen3-vl:2b 不够用时）：
| 模型 | 命令 | 适用场景 |
|------|------|---------|
| richardyoung/smolvlm2-2.2b-instruct | `ollama pull richardyoung/smolvlm2-2.2b-instruct` | 通用 SmolVLM2，非 GUI 专用，需测试 |
| moondream:1.8b-v2-q4_K_M | `ollama pull moondream:1.8b-v2-q4_K_M` | 通用视觉，约 1GB，响应快 |
| qwen3-vl:2b | （已安装，~24s 响应，当前在用） | 所有视觉任务（场景分类+内容分析） |

**验证方法**：
```bash
curl -s --max-time 8 http://127.0.0.1:11434/api/tags | python3 -c "
import sys,json
d=json.load(sys.stdin)
for m in d.get('models',[]):
    print(m['name'], '|', round(m['size']/(1024**3), 2), 'GB')
"
```

---

**已确认本地 Ollama 模型**（`http://127.0.0.1:11434/api/tags`，2026-06-07实测）：
```
qwen3-vl:2b                            ✅ 在用（接管所有视觉任务）
qwen2.5:1.5b                           ✅ 在用（小型文本）
smolvlm2-agentic-gui                   ❌ 已从 registry 下线（2026-06-02确认）
nomic-embed-text:latest                ✅ 在用（嵌入模型）
```

**⚠️ 已知 Mac Bug**：blaifa/InternVL3_5:4B（GitHub Issue #12166），Mac 图片理解错误，暂缓部署。

**⚠️ qwen3-vl:4b 不存在**：`ollama pull qwen3-vl:4b` 返回 404，不要尝试。

**待验证项**：
- Edge TTS 是否正常工作（execute_code 里测）
- UI-TARS Desktop Mac M4 安装（github.blocked 无法下载 .dmg）

**下次学习方向**：执行层 — 坐标校准，准备 DRY_RUN=False 切换
| 模型 | 大小 | 状态 | 适用场景 |
|------|------|------|----------|
| qwen3-vl:2b | 1.9GB | ✅ 在用 | 实时GUI监控（~24s响应），所有视觉任务 |
| qwen2.5:1.5b | ~1GB | ✅ 在用 | 小型文本模型 |
| nomic-embed-text | ~274MB | ✅ 在用 | 嵌入模型 |
| blaifa/InternVL3_5:4b | ~3GB | ⚠️ Mac上有图片理解Bug，暂缓 | 基于Qwen3架构，通用视觉 |
| **Qwen 3.6-27B dense** | ~17GB Q4 | ⚠️ 待验证（Ollama支持待确认） | Vision内建于基座，M4 24GB "tight but doable" |
| ui-venus | — | ❌ Ollama无 | 页面404，搜索无结果 |

⚠️ **重要**：必须用 `http://127.0.0.1:11434/api/tags` 检查本地模型，不能用 `https://api.ollama.com/api/tags`（后者返回远程库，不等于本地安装）

**qwen3-vl:2b 已知限制**（Ollama）：
- 原生1920x1080截图会超时（>60s）
- 必须缩图到~900x900才能在46s内响应
- 4B版本（3.3GB，90% ScreenSpot）待验证

**qwen3-vl:2b 响应时间实测范围（2026-05-30 更新，smolvlm2 已退役）**：
- 简单桌面/壁纸：~5-8s
- 中等复杂度（浏览器tabs+导航）：~10-13s
- 高复杂度（移动端UI+商品卡片）：~20-25s
- **复杂桌面截图（壁纸+聊天图标+状态栏）：~64s**（比预期显著更慢）
- 场景复杂度直接影响 token 生成量，从而影响 decode 延迟
- 结论：21.8s 在高复杂度场景属于正常范围，非模型异常
- ⚠️ 复杂桌面截图（湖景壁纸+AIMAC图标）响应达64s，需考虑截图预处理降复杂度

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

### 2026-06-01 补充：Handler 处理周期量化

**产线实测数据**（80分钟窗口，00:04-00:15 抓取 timestamp 分析）：
```
scene classification 耗时：35-47s（包括 resize + Ollama API + 响应解析）
ask_screen 内容分析耗时：~35s
合计单次处理周期：70-84s

watcher 冷却间隔：15s
Handler 仍在运行抑制次数：302次

每次完整 handler 执行期间，watcher 触发约 5 次"Handler仍在运行"
302 ÷ 5 ≈ 60 次实际执行 × 80s ≈ 80 分钟 CPU / Ollama 被占用
```

**与"昨夜死机"根因的关系**：死机时 handler 处理速度是 smolvlm2 的 10-15s/次，现在 qwen3-vl:2b 的 70-84s/次慢 5-7x，虽不会直接死机但 CPU/Ollama 占用大幅增加。

**2026-06-01 已实施**：`is_dark_screenshot()` 快速检测锁屏/黑屏，直接跳过 scene classification + ask_screen。
夜间每次触发从 ~80s 降至 ~0.5s（~98% CPU 节省）。详见 `references/handler-optimizations-dark-screen-cooldown-2026-06-01.md`

## 严重性能 Bug：禁止向 gateway.log 写屏幕分析结果

**⚠️ 已确认问题（2026-05-29）**：
screen_trigger_handler 向 `gateway.log` 写屏幕分析结果（screen_watch 标签），日志审查发现 gateway.log 有 2553 条 screen_watch 记录（1.1MB），这是 gateway 性能下降的根因之一。

**✅ 正确做法**：
- 分析结果写入 `~/.hermes/logs/Screen_analysis.log`（screen-watcher-vision SKILL.md 第14行已定义）
- **绝对禁止**向 gateway.log 写任何屏幕分析内容
- 写日志时用模块级 logger（如 `logger = logging.getLogger("screen_watcher")`），不要用平台通用的 gateway logger

**检查方法**：
```bash
grep -c "screen_watch\|Screen analysis\|screen_trigger" ~/.hermes/logs/gateway.log
# 如果 > 0，说明有 bug，screen_analysis 内容进了 gateway.log
```

## 紧急度分流（2026-05-26 新增）

screen_trigger_handler 对分析结果进行紧急度分级，非紧急内容不推 Telegram：

- **urgent**：关键词命中（错误/崩溃/失败/异常/警告/500/404 等）→ 立即推 Telegram
- **normal**：关键词命中（新消息/订单/付款/发货/回复等）→ 推 Telegram
- **silent**：无关键词 → 静默，仅记日志

关键词库路径：`~/.hermes/scripts/screen_trigger_handler.py` 第171-174行。

### ⚠️ 2026-06-01 发现：unknown/other 场景假阳性 [urgent]

**症状**：所有 "unknown" 和 "other" 场景的 handler 日志都标记 `[urgent]`，即使屏幕实际是空白/锁屏/屏保。

**根因**：qwen3-vl:2b 在空白/锁定屏幕上生成幻觉描述（如 "有异常"、"出现错误"），命中 URGENT_KEYWORDS 中的 "异常" 或 "错误"。

**实测证据**（80分钟窗口内）：
- 场景分布：301 unknown (51%), 233 browser (39%), 42 desktop (7%), 12 other
- 所有 unknown/other → 标记 `[urgent]` → 尝试推 Telegram
- 但这些只是夜间锁屏/空白桌面，无需任何处理

**影响**：每个假阳性 `[urgent]` 都触发 Telegram Bot API 调用，浪费 API 额度 + IO 时间。

**2026-06-01 已修复**：新增 `is_dark_screenshot()` 暗屏跳过检测 + unknown/other 仅匹配 CRITICAL_KEYWORDS。详见 `references/handler-optimizations-dark-screen-cooldown-2026-06-01.md`

## Auto-Execute 自动执行（2026-05-29 新增）

**断链修复**：原本 screen_trigger_handler 只分析屏幕+推送 Telegram，从不执行任何操作。
现在通过 `auto_execute()` 函数 + `ACTION_WHITELIST` 配置桥接到 hermes_desktop_rpa.py。

**当前状态**：
- `DRY_RUN = True`（安全模式，只记录不执行）
- 白名单场景：browser/wechat/1688/dingtalk/telegram（5个，与 get_scene_type() 英文输出对齐）
- 初始动作均为 `wininfo`（只读获取窗口信息）
- Telegram 推送增加 `[Auto-Exec dry-run for X]` 前缀提示

**切换到执行模式的步骤**：
1. 验证 dry-run 日志输出正常
2. 为每个场景校准坐标（用 `hermes_desktop_rpa.py wininfo` 获取窗口位置）
3. 坐标映射：qwen3-vl:2b 输出 [x,y] on 1000×1000 相对坐标 → 像素映射公式 `x_px = x/1000 × W`（详见 `references/poins-gui-g-coordinate-research-2026-06-01.md`）
4. 将 `DRY_RUN = False`
5. 先在低风险场景（桌面/计算器）测试

**结构化JSON输出发现**（2026-05-29 实测）：
- smolvlm2 可用 JSON prompt 引导输出结构化结果
- 输出始终包裹在 `<code>...</code>` 标签内
- `get_scene_type()` 已有标签清理逻辑：`response.split('</think>')[-1].strip()` + `.split('<code>')[-1].strip()`
- 需增强清理逻辑以处理 `<code>` -> `\n</code>` 尾部

## 链路状态快照（2026-05-30 实测验证）

**验证结论**：screen_watcher 链路已完整激活，所有节点正常工作：

```
screen_watcher.py（PID 61099）
  → 每15秒扫描，检测有效变化则触发
  → touch_trigger() 创建 .changed 文件 + .handler_lock 互斥锁
  → subprocess.Popen(screen_trigger_handler.py)（PID 61146）
      → smolvlm2 分析屏幕（~25s 端到端）
      → auto_execute() dry-run 记录到 ~/.hermes/logs/screen_trigger.log
      → 无匹配场景则 silent（不推 Telegram）
```

**关键验证命令**：
```bash
# 检查进程是否运行
ps aux | grep screen_watcher | grep -v grep
# 检查 screenshots 目录
ls -lt ~/.hermes/screenshots/
# 检查 handler 日志
cat ~/.hermes/logs/screen_trigger.log | tail -10
# 检查 watcher 日志
cat ~/.hermes/logs/screen_watcher.log | tail -15
# 检查 handler 是否还在运行（lock 文件存在）
ls ~/.hermes/screenshots/.handler_lock
```

**⚠️ 场景类型 key 不匹配 bug（2026-05-30 实测，已修复）**

**症状**：日志中从未出现 `[AUTO-EXEC-DRY]` 标记，auto_execute() 静默失效。

**根因**：get_scene_type() 输出**英文单词**（browser/wechat/desktop/calculator/jingdong/1688/dingtalk/telegram/other），但 ACTION_WHITELIST 的 key 是**中文**（浏览器/微信/桌面/计算器/京东/1688/钉钉/Telegram）。两者不匹配 → auto_execute() 第46行 `if scene_type not in ACTION_WHITELIST` 直接 return None。

**修复方案（2026-05-30 已实施：方案B）**：统一 ACTION_WHITELIST 为英文 key，与 get_scene_type() 输出对齐：
```python
ACTION_WHITELIST = {
    "browser": ("wininfo", None),
    "wechat": ("wininfo", None),
    "1688": ("wininfo", None),
    "dingtalk": ("wininfo", None),
    "telegram": ("wininfo", None),
    "desktop": ("wininfo", None),    # 新增（2026-05-30）
    "calculator": ("wininfo", None), # 新增（2026-05-30）
    "other": ("wininfo", None),      # 新增（2026-05-30）
}
```

**验证方法**：日志中应出现 `[AUTO-EXEC-DRY] Would execute: wininfo for scene=browser`，表示 auto_execute 正常触发。

> ⚠️ **wininfo 命令不在 PATH**：DRY_RUN 模式下只记录不执行所以未暴露。切换 DRY_RUN=False 前需将 wininfo 替换为实际存在的命令（如 cliclick），详见 `references/action-whitelist-fix-2026-05-30.md`

**常见断链故障排查**：
- `screenshots/` 目录不存在 → 手动 `mkdir -p ~/.hermes/screenshots`，watcher 会自动创建
- 无 `screen_watcher` 进程 → 手动启动 `python3 ~/.hermes/scripts/screen_watcher.py &`（用 background=true）
- `.handler_lock` 永久存在（进程被 kill） → 手动 `rm ~/.hermes/screenshots/.handler_lock`
- handler 重复 spawn → 检查 `.handler_lock` 是否正确创建/删除（见 2026-05-26 修复）
- **Ollama 进程被系统 kill → handler Connection refused**（2026-06-01 发现）：
  - 症状：handler 日志显示 `Failed to establish a new connection: [Errno 61] Connection refused`
  - 根因：Ollama 被系统内存压力调度 kill（日志 `err="signal: killed"`），两次发现（23:53 和 00:04）
  - 排查：`ps aux | grep -i ollama | grep -v grep` — 无输出 = 已挂
  - 修复：`open -a Ollama && sleep 5 && curl -s --max-time 3 http://127.0.0.1:11434/api/tags`
  - 注意：handler 本身正常，是上游 Ollama 服务挂了。scenario unknown 激增（超过正常40%基线）时优先查 Ollama
- **dry-run 日志从无 `[AUTO-EXEC-DRY]`** → 检查 scene_type 格式是否与 ACTION_WHITELIST key 匹配（见上方场景类型 key 不匹配 bug）

**启动后状态**：
- `~/.hermes/screenshots/current.png` 存在（3.4MB 截图表当前桌面）
- `~/.hermes/screenshots/.watcher_state.json` 记录上次触发时间
- `DRY_RUN=True` 模式下 auto_execute 只记录不动手，安全验证正常

**可执行改进**：
- ✅ **暗屏检测已实装**：`is_dark_screenshot()` 夜间跳过分析，CPU 节省 ~98%
- ✅ **分类降速已实装**：get_scene_type resize 800→400px，耗时减半
- ✅ **紧急标记修复已实装**：unknown/other 仅匹配 CRITICAL_KEYWORDS
- ✅ **冷却减半已实装**：COOLDOWN 120→60s
- **Bug 修复**：screen_trigger_handler.py 的 get_scene_type() 返回完整描述，但 auto_execute() 期望 app 名称。需要统一格式，或让 auto_execute 接受描述并做模糊匹配
- **moondream cascade（优先级高）**：qwen3-vl:2b 的 24s 延迟过高，moondream:1.8b-v2-q4_K_M 作为 <5s 快速初筛，仅在信心不足时升级到 qwen3-vl:2b。详见 `references/moondream-cascade-2026-06-07.md`
- **confusion_score（优先级高）**：基于 GUIDE Benchmark（CVPR 2026）发现，Frustration 检测比 Intent Prediction 更有价值。建议在 screen_trigger_handler 中增加：操作频率骤降检测、重复点击同一区域、鼠标静止时长。详见 `references/guide-benchmark-cvpr2026.md`
- **Waiting 状态检测**：连续3帧截图相似度 > 95% + 操作频率低 → 跳过 auto_execute（避免在渲染等待时误触发）

**待验证项**：
- Edge TTS 是否正常工作（execute_code 里测，不用 terminal 走代理）
- Noiz API key 是否已配置
- UI-TARS Desktop Mac M4 安装可行性（github.blocked 无法下载 .dmg）

**下次学习方向**：D — 执行层（坐标校准，DRY_RUN=False 前的精度验证测试 + handler 优化效果验证）

## 参考文件

- `references/ollama-api-endpoint-chat-vs-generate-2026-05-30.md` — ⚠️ 重要：/api/chat vs /api/generate 性能差异，错误端点导致120s超时
- `references/insiderllm-m4-2026-guide-2026-05-31.md` — InsiderLLM M4 2026 最新推荐：Qwen 3.6-27B dense（M4 24GB "tight but doable"），vision 内建于基座
- `references/response-normalization-2026-06-02.md` — ⚠️ 重要：get_scene_type() response 标准化，取第一行+小写+trim标点
- `references/screen-trigger-handler-telegram-fix-2026-05-30.md` — Telegram推送失败修复（hermes_tools → 直接Bot API）+ 场景分类prompt幻觉bug修复
- `references/smolvlm2-structured-json-2026-05-29.md` — smolvlm2 JSON 输出测试详情（响应时间、清理函数、可靠性评估）
- `references/screen-trigger-handler-auto-execute-2026-05-28.md` — Auto-Execute 集成设计文档
- `references/screen-watcher-handler-lock-2026-05-26.md` — Handler 重复 spawn 修复
- `references/qwen3vl-vs-smolvlm2-2026-05-30.md` — qwen3-vl:2b vs smolvlm2 实测对比（速度、分辨率、适用场景）
- `references/scene-classification-model-fix-2026-06-02.md` — ⚠️ 重要：get_scene_type() 从 smolvlm2 切换到 qwen3-vl:2b，smolvlm2 在纯分类任务上会产生 final_answer 乱码
- `references/internvl3_5_4b_mac_bug_2026-06-02.md` — ⚠️ Issue #12166 已关闭（2025-09），可重测验证是否仍有问题
- `references/captchas-auto-execute-security-2026-05-30.md` — CAPTCHA agent 检测研究，DRY_RUN=False 时需考虑的 anti-detection 对策
- `references/hermes-desktop-rpa-osascript-timeout-2026-06-02.md` — osascript 超时是 cron 环境限制（非 PATH 问题），DRY_RUN=False 切换必须在有活跃桌面 session 的环境

## 温度参数
```json
{"temperature": 0.0, "num_gpu": 0}
```

## 文件路径
- 截图：`~/.hermes/screenshots/current.png`
- 分析缓存：`/tmp/hermes_trigger_vision.jpg`
- 日志：`~/.hermes/logs/screen_analysis.log`
- Ollama地址：`http://localhost:11434/api/chat`（⚠️ 必须用 `/api/chat`，不能用 `/api/generate`）
- 模型：`qwen3-vl:2b`（smolvlm2-agentic-gui 已从 Ollama registry 永久下线）

## ⚠️ Ollama API 端点关键陷阱（2026-05-30 实测）

**禁止使用 `/api/generate`**：处理 1920x1080 截图需 41.6s，容易触发 120s 超时。

**必须使用 `/api/chat`**：相同截图只需 31.7s，快 24%，且响应格式更干净。

**payload 格式差异**：
```python
# ❌ /api/generate 格式（已废弃）
{"model": "...", "prompt": "...", "images": [b64], "stream": False, ...}

# ✅ /api/chat 格式（当前使用）
{"model": "...", "messages": [{"role": "user", "content": "...", "images": [b64]}], "stream": False, ...}

# response 格式差异
# /api/generate:  data['response']
# /api/chat:      data['message']['content']
```

**测试方法**（验证 endpoint 选择正确）：
```python
# /tmp/test_endpoint.py — 对比两个端点速度
import requests, base64, time

OLLAMA_HOST = "http://localhost:11434"
with open("/tmp/hermes_trigger_vision.jpg", "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode()

payload = {
    "model": "ahmadwaqar/smolvlm2-agentic-gui:latest",
    "messages": [{"role": "user", "content": "Describe in one sentence.", "images": [img_b64]}],
    "stream": False, "options": {"temperature": 0.0}
}

# /api/chat（正确）
t0 = time.time()
r = requests.post(f"{OLLAMA_HOST}/api/chat", json=payload, timeout=60)
print(f"/api/chat: {time.time()-t0:.1f}s, status={r.status_code}")
```