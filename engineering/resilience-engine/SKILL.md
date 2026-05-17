---
name: resilience-engine
description: 生存引擎 — 自动恢复能力，处理卡死、白屏、验证码、登录失效等异常，让任务不卡死。
triggers:
  - "任务执行超过30秒无响应"
  - "页面白屏或加载失败"
  - "遇到验证码或风控"
  - "登录态失效"
  - "网络断开"
  - "任何可能导致任务卡死的情况"
---

## Implementation Status (2026-05-17) — UPDATED

**2026-05-17: 六大模块全部实现并验证可导入。**

实际文件（`~/.hermes/skills/engineering/resilience_engine/`）：
- `watchdog.py` — 核心看门狗（超时检测 + 策略执行 + 熔断）
- `stuck_detector.py` — 卡死检测器（鼠标静止、页面僵死、JS无响应）
- `blank_screen_detector.py` — 白屏检测器（纯白/黑屏、DOM空、渲染失败）
- `captcha_router.py` — 验证码路由（滑块/点选/短信/二维码 → 策略分发）
- `login_detector.py` — 登录失效检测 + 自动重登
- `network_handler.py` — 网络异常分类 + 恢复执行
- `checkpoint.py` — 断点续传（状态快照 + 恢复 + 跨会话）
- `__init__.py` — 统一导出

**使用方式：**
```python
import sys
sys.path.insert(0, "/Users/aimac/.hermes/skills/engineering")
from resilience_engine import (
    Watchdog, get_watchdog,
    get_stuck_detector, StuckType,
    get_blank_screen_detector, BlankScreenType,
    get_captcha_router, CaptchaType,
    get_login_detector, LoginState,
    execute_network_recovery, NetworkErrorType,
    get_checkpoint_manager, CheckpointStatus,
)

# 1. 卡死检测
detector = get_stuck_detector()
is_stuck, stuck_type, reason = detector.check_mouse_stuck(current_pos=(500, 400))
is_stuck, stuck_type, reason = detector.check_page_stuck(url, screen_hash)

# 2. 白屏检测
blank_detector = get_blank_screen_detector()
is_blank, blank_type, reason = blank_detector.check_by_dom(dom_text, images_count=3)
recovery_plan = BlankScreenRecovery.format_recovery_plan(blank_type, reason)

# 3. 验证码路由
router = get_captcha_router()
is_captcha, captcha_type, hint = router.detect_captcha(page_text, page_url)
route = router.get_route(captcha_type)

# 4. 登录检测
login_detector = get_login_detector()
state, reason = login_detector.check_by_page_text(page_text, url)
if state in [LoginState.LOGGED_OUT, LoginState.EXPIRED]:
    relogin = AutoRelogin()
    success, msg = relogin.relogin(login_fn)

# 5. 网络异常
recovered, msg = execute_network_recovery(network_error, max_retries=3)

# 6. 断点续传
cp_manager = get_checkpoint_manager(task_id="task_001", task_name="批量操作", total_steps=10)
cp_manager.set_steps(["打开页面", "搜索商品", "点击详情", ...])
cp_manager.start_step(1)
cp_manager.complete_step(1, output={"商品ID": "123"})
cp_manager.save()  # 手动保存
# 失败后恢复：
cp_manager = get_checkpoint_manager.resume(task_id="task_001")
```

---

# Resilience Engine — 完整规格

## Overview

人类的行动遇到障碍时，会自动调整策略：
- 门推不开，会拉一下试试
- 验证码出现，会想办法识别
- 登录失效，会重新登录
- 网络断了，会等恢复后重试

**Resilience Engine是Hermes的"生存本能"——遇到异常时不卡死，自动进入恢复流程。**

### 六层保障体系

```
┌─────────────────────────────────────────────────────────────┐
│  1. StuckDetector (卡死检测)                                 │
│     鼠标静止 / 页面僵死 / JS无响应 / 窗口失焦                   │
├─────────────────────────────────────────────────────────────┤
│  2. BlankScreenDetector (白屏检测)                            │
│     纯白/黑屏 / DOM空 / 资源加载失败 / 验证码页                │
├─────────────────────────────────────────────────────────────┤
│  3. CaptchaRouter (验证码路由)                               │
│     滑块 / 点选 / 短信 / 二维码 → OCR/人工/跳过                │
├─────────────────────────────────────────────────────────────┤
│  4. LoginDetector + AutoRelogin (登录失效+重登)               │
│     Cookie/Session失效 → 自动重登 → 恢复任务                  │
├─────────────────────────────────────────────────────────────┤
│  5. NetworkHandler (网络异常处理)                             │
│     DNS/超时/SSL/代理/限流 → 分类 → 执行恢复                   │
├─────────────────────────────────────────────────────────────┤
│  6. CheckpointManager (断点续传)                              │
│     定期快照 / 失败恢复 / 跨会话 / 状态完整保留                 │
└─────────────────────────────────────────────────────────────┘
```

### 决策流程

```
异常发生
    ↓
┌─────────────────┐
│  StuckDetector  │ → 记录卡死类型 → 应用恢复策略
└─────────────────┘
    ↓
┌─────────────────────┐
│ BlankScreenDetector │ → 判断白屏类型 → 执行对应恢复
└─────────────────────┘
    ↓
┌───────────────┐
│ CaptchaRouter │ → 检测验证码类型 → 路由到OCR/人工/跳过
└───────────────┘
    ↓
┌──────────────────┐
│ LoginDetector    │ → 检测登录失效 → AutoRelogin
└──────────────────┘
    ↓
┌──────────────────┐
│ NetworkHandler   │ → 分类网络错误 → 执行对应恢复
└──────────────────┘
    ↓
所有恢复失败
    ↓
┌──────────────────────┐
│ CheckpointManager     │ → 保存完整状态 → 通知人工
└──────────────────────┘
```

---

## 模块详解

### 1. StuckDetector — 卡死检测

**检测类型：**

| 类型 | 触发条件 | 检测方式 |
|------|----------|---------|
| `MOUSE_STUCK` | 鼠标位置X/Y变化 < 5px 持续 > 30s | 坐标对比 |
| `PAGE_STUCK` | URL + 屏幕内容hash不变 持续 > 30s | 哈希对比 |
| `ELEMENT_STUCK` | 目标元素僵死、无响应 | DOM监测 |
| `JS_STUCK` | JS执行无响应 > 超时 | CDP执行测试JS |
| `WINDOW_FOCUS_LOST` | 窗口失去焦点 + 长时间无操作 | 焦点监测 |

**接口：**
```python
# 检测鼠标是否卡死
is_stuck, reason = detector.check_mouse_stuck(current_pos=(500, 400))

# 检测页面是否卡死
is_stuck, reason = detector.check_page_stuck(current_url, screen_hash)

# 综合检测
is_stuck, stuck_type, reason = detector.is_stuck()

# 重置检测器
detector.reset()
```

---

### 2. BlankScreenDetector — 白屏检测

**白屏类型：**

| 类型 | 特征 | 恢复策略 |
|------|------|---------|
| `PURE_WHITE` | 截图文件 < 30KB，像素>85%白色 | 刷新+检查网络 |
| `PURE_BLACK` | 截图文件极小，像素>90%黑色 | 检查显示器 |
| `EMPTY_DOM` | DOM文本 < 50字符 | 等待JS渲染 |
| `RENDER_FAILED` | 多个JS错误 | 禁用扩展重试 |
| `RESOURCE_LOAD_FAILED` | CSS/JS/图片加载失败≥3 | 检查代理 |
| `CAPTCHA_PAGE` | 含验证码关键词 | 人工介入 |
| `LOGIN_REDIRECT` | 跳转登录页 | 检查登录态 |

**接口：**
```python
# 通过DOM检测
is_blank, blank_type, reason = detector.check_by_dom(
    dom_text="页面文本",
    images_count=3,
    scripts_count=5
)

# 获取恢复计划
plan = BlankScreenRecovery.format_recovery_plan(blank_type, reason)
print(plan)
```

---

### 3. CaptchaRouter — 验证码路由

**支持的验证码类型：**

| 类型 | 关键词 | 路由策略 |
|------|--------|---------|
| `SLIDER` | 滑动验证、滑块拼图 | OCR轨迹生成 |
| `CLICK_SELECT` | 依次点击、文字点选 | 图像匹配 |
| `SMS_CODE` | 短信验证码 | 等待短信 |
| `EMAIL_CODE` | 邮件验证码 | 读取邮箱 |
| `QR_SCAN` | 二维码扫码 | 人工扫码 |
| `BEHAVIOR` | 极验、行为验证 | 等待/人工 |

**滑块轨迹生成（模拟人类）：**
```python
from resilience_engine import SliderTrajectoryGenerator

points = SliderTrajectoryGenerator.generate_trajectory(distance=300, duration_ms=1500)
# 返回: [(x, timestamp_ms), ...] — 非直线，有加速/减速曲线
```

---

### 4. LoginDetector + AutoRelogin — 登录失效检测与重登

**检测方式：**

1. **页面文本检测** — 通过关键词判断（"登录"vs"退出"）
2. **API检测** — 调用用户信息API验证（最可靠）
3. **HTTP状态码** — 401/403 = 认证失败

**自动重登流程：**
```python
# 检测
state, reason = login_detector.check_by_page_text(page_text, url)

if state in [LoginState.LOGGED_OUT, LoginState.EXPIRED]:
    # 重登
    relogin = AutoRelogin()
    relogin.load_credentials()  # 从 ~/.hermes/login_credentials.json 加载
    success, msg = relogin.relogin(login_fn=my_login_func)
```

**凭证存储：** `~/.hermes/login_credentials.json`（需手动或首次登录时保存）

---

### 5. NetworkHandler — 网络异常处理

**错误分类：**

| 类型 | 关键词 | 恢复策略 |
|------|--------|---------|
| `DNS_FAILURE` | DNS解析失败 | 清除DNS缓存+备用DNS |
| `CONNECTION_TIMEOUT` | 连接超时 | 增加超时+检查代理 |
| `CONNECTION_REFUSED` | 连接被拒绝 | 检查目标服务 |
| `SSL_ERROR` | 证书错误 | 检查系统时间+更新CA |
| `PROXY_ERROR` | 代理认证失败 | 切换代理 |
| `RATE_LIMITED` | 429限流 | 等待+降低频率 |
| `BROKEN_PIPE` | 连接重置 | 重建连接 |
| `NETWORK_UNREACHABLE` | 网络不可达 | 等待网络恢复 |

**统一入口：**
```python
recovered, msg = execute_network_recovery(error, max_retries=3)
```

---

### 6. CheckpointManager — 断点续传

**核心功能：**

- **自动保存**：每隔30秒自动保存（可配置）
- **状态完整**：保存任务步骤、执行历史、世界状态、恢复指令
- **跨会话恢复**：Hermes重启后也能从最后一个checkpoint继续
- **恢复指令**：自动生成可读的恢复说明

**使用流程：**
```python
# 任务开始
cp = get_checkpoint_manager(task_id="batch_001", task_name="批量处理", total_steps=5)
cp.set_steps(["打开列表", "获取第1页", "获取第2页", "获取第3页", "保存结果"])

# 步骤执行
for step_id in range(5):
    cp.start_step(step_id)
    try:
        result = execute_step(step_id)
        cp.complete_step(step_id, output=result)
    except Exception as e:
        cp.fail_step(step_id, str(e))
        cp.save()
        raise

cp.mark_completed()

# 恢复（失败后）
cp = get_checkpoint_manager.resume(task_id="batch_001")
if cp:
    next_step = cp.get_next_pending_step()
    instruction = cp.get_resume_instruction()
    print(f"从步骤 {next_step} 继续: {instruction}")
```

**Checkpoint文件：** `~/.hermes/checkpoints/{task_id}.json`

---

## 恢复策略执行顺序

每种异常类型有预设的恢复策略链，按顺序执行直到成功或耗尽：

```
1. wait:N         → 等待N秒（应对临时性问题）
2. retry          → 重试操作
3. refresh        → 刷新页面
4. check_network  → 检查网络状态
5. scroll         → 滚动页面（激活懒加载元素）
6. relocate       → 重新定位元素
7. human_confusion → 模拟人类困惑行为（画圈+犹豫）
8. escape_hatch   → 保存完整状态，通知人工
```

---

## Common Rationalizations

| 常见借口 | 真相 | 反制 |
|---------|------|------|
| "网络慢等一下就行" | 无限等待是卡死的根源 | Watchdog强制30s超时 |
| "重试3次还失败就放弃" | 重试策略需要更智能 | 检测失败模式决定策略 |
| "失败了就重新开始" | 任务状态是宝贵的 | Checkpoint保存完整状态 |
| "偶尔失败没关系" | 连续失败说明有系统问题 | 模式识别触发警报 |
| "验证码只能人工" | 滑块可OCR辅助 | CaptchaRouter路由策略 |

## Red Flags

- 任务执行超过5分钟无结果
- 连续3次相同类型的失败
- 突然跳转到意外页面
- 验证码出现但继续执行
- 登录态失效但继续操作
- 页面白屏但继续等待
- 网络错误但无限重试

---

## MCP Server失联检测与恢复（2026-05-16 新增）

### 问题描述

`mcp-chrome-stdio` 作为 Hermes 进程的子进程运行。当 Hermes 被 kill（signal 15）或意外崩溃时，Chrome MCP bridge 随 Hermes 一起终止。即使 Chrome 调试端口（9333）本身仍在监听，MCP 工具也会报 `ClosedResourceError` 或 `Failed to connect to MCP server`。

### 症状识别

```
ClosedResourceError: ClosedResourceError()
Failed to connect to MCP server
[MCP call failed] 短时间内反复出现
```

### 诊断流程

```
① 症状：MCP chrome 工具全部报错
       ↓
② 检查 Chrome 调试端口是否存活
   lsof -i :9333 | grep Chrome
       ↓
   端口存活但 MCP 不通
       → Chrome 进程正常，bridge 死了
   端口也不通
       → Chrome 整个挂了，需要重启 Chrome
```

### 分层恢复策略

**第一层：MCP bridge 自动重连**
- MCP SDK 有内置重连机制，等待 10-15 秒自动恢复

**第二层：CDP HTTP 降级（Chrome 活着但 bridge 死的 fallback）**

```python
# 检测 Chrome 端口是否活着
import urllib.request
req = urllib.request.Request("http://127.0.0.1:9333/json", method="GET")
with urllib.request.urlopen(req, timeout=5) as resp:
    tabs = json.loads(resp.read())
    print(f"Chrome OK: {len(tabs)} tabs")
```

⚠️ **CDP HTTP 端点限制**：不能截图（需要 WebSocket）、不能导航（PUT /json/new 无效），仅能枚举 tabs。

**第三层：Chrome 进程完全重启**

Chrome 调试端口也不通时：
```bash
pkill -f "Chrome.*remote-debugging-port=9333"
sleep 2
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9333 \
  --remote-allow-origins=* \
  --user-data-dir="$HOME/.hermes/chrome-debug" \
  --no-first-run --no-default-browser-check &
```

**第四层：需要导航/点击操作但 bridge 死的判断**

Chrome 端口活着 + bridge 死 + 需要操作 → 告知用户需重启 Hermes（目前 bridge 必须由 Hermes 进程拉起，无法独立存活）。

### 决策树

```
MCP chrome 工具报错
    ↓
Chrome 端口活着？(lsof -i :9333)
    ├─ NO → 重启 Chrome（第四层）
    └─ YES → bridge 死了
            ↓
        需要导航/点击操作？
            ├─ NO（只读操作）→ 用 CDP HTTP 凑合
            └─ YES → 告知用户需重启 Hermes
```

---

## Verification

验证清单：

- [x] StuckDetector在30秒无进展时触发
- [x] BlankScreenDetector检测7种白屏类型
- [x] CaptchaRouter识别6种验证码并路由
- [x] LoginDetector检测登录失效 + AutoRelogin重登
- [x] NetworkHandler分类8种网络错误 + 恢复
- [x] CheckpointManager保存/恢复完整状态
- [ ] Watchdog在BrowserWorker中实际保护操作
- [ ] 恢复后能从断点继续
- [ ] 人工接管时有完整上下文
