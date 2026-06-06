---
name: browser-webpage-100score
description: 本地浏览器识别网页100分任务 — 反指纹100分 + CDP直连Chrome读DOM + 自愈点击输入，覆盖 9 个已登录AI站点(DeepSeek/豆包/ChatGLM/ChatGPT/Gemini 5个实测+ Poe/Claude/Perplexity/Kimi/通义千问 4个登录态待实测)的完整自动化流程
tags: []
triggers:
  - 读网页内容
  - 识别网页
  - 抓取网页数据
  - 浏览器自动化
  - 操作已登录网站
  - CDP浏览器控制
  - 反指纹检测
  - multi_ask
  - 9站交叉问
  - 9个AI站
---

# ⚠️ 登录态必须 4 维证据验证（2026-06-05 18:50 用户拍板）

**触发词**："打开网站 / AI 对话 / 检查登录 / browser_navigate" → **0 思考** 走这个 4 步验证流程, **不要假设成功**。

## 4 步验证 SOP

1. **navigate** → `browser_navigate(url)` 打开目标站
2. **snapshot** → `browser_snapshot` 看 AX 树里**登录后才有的元素** (用户名/邮箱/历史对话列表/侧栏头像)
3. **console JS 自检** → `browser_console` 执行 JS 抓 3 个维度:
   - `localStorage` 里 user/uid/token/email/profile 关键字
   - `document.cookie.length` 字符数 (其他站 209~2757 都有 user 标识, < 100 异常)
   - 是否有 "登录/Login/Sign in" 按钮 (存在 = 未登录)
4. **vision 截图** → `browser_vision` 拿 AI 读图 + 用户回看 (`~/.hermes/cache/screenshots/browser_screenshot_*.png` 留底)

## 6 维登录证据 (按权重)

| 证据 | 权重 | 检测方法 | 缺这个 = |
|---|---|---|---|
| **用户名/邮箱文本** | 强 | AX 树找含"用户"/"@gmail.com"的节点 | 大概率游客 |
| **历史对话列表** | 强 | 侧栏有"今天/昨天/7天内"分组 | 大概率新登录或空账号 |
| **localStorage user-key** | 强 | JS 抓 `/user\|uid\|token\|email/` 命名的 key | 可能是 cookie-only 登录 |
| **cookies 字符数** | 中 | `document.cookie.length` ≥ 200 | 极可能未登录 |
| **侧栏头像/账号按钮** | 中 | AX 树找非默认头像的 image | 默认头像 = 弱证据 |
| **页面级 "登录" 按钮** | 弱反证 | 不存在"登录/Sign in"按钮 = 强证据 (无) | 存在 = 强证据 (是) |

## "失败"判定 (任一触发)

- 截图默认头像/无用户标识/无历史对话 → **单列报告, 不与成功混说**
- localStorage 0 个 user-key + cookies < 100 字符 → 单列报告
- cookies 在 (200+) 但 localStorage 0 个 user-key → 标"低置信度, 待复核" (不算失败, 也不算完全成功)
- **2026-06-06 新增**: `/json` 上 0 page tab (但 Chrome 在跑) → 不是"登录丢失", 是 tab 全空, 走 bulk_open_9 治本, 不算登录失败

## 6 站实测数据 (2026-06-05 18:50 baseline)

| 站 | 登录态 | username/email | localStorage user-key | cookies | 头像 |
|---|---|---|---|---|---|
| Gemini | ✅ | K H (hanlukebu@gmail.com) | (N/A Google 账号) | (N/A) | 自定义 |
| 豆包 | ✅ | 用户320735 | (N/A) | (N/A) | 自定义 |
| DeepSeek | ✅ | 罗 | (N/A) | (N/A) | 自定义 |
| ChatGPT | ✅ | LH (缩写在头像) | ✅ user-LGyeKM5DBTtdLMSeFo4Nddva | 2757 chars | 自定义 |
| Grok | ✅ | lukebu hanlukebu@gmail.com | (N/A) | (N/A) | 自定义 |
| **智谱清言** | ⚠️ **低置信度** | 默认头像 | ❌ 无 user-key (仅 claw_guide_dialog_shown 等引导记录) | **209 chars** (其他站 209~2757 区间下限) | 默认人物剪影 |

**智谱坑点** (2026-06-05 新发现):
- 默认头像 + localStorage 无 user-key + cookies 209 chars (低于 ChatGPT/Grok 10倍)
- **可能**: cookie-only 登录, 旧号, 或未登录访客模式
- **应对**: 用户手动打开智谱清言确认右上角是否显示真实账号; 未来跑智谱对话前必先用本 SOP 复核

## 9 站实测数据 (2026-06-06 baseline, 扩到 9 站 + 元宝/文心/千问)

| 站 | 登录态 | username/email | localStorage user-key | cookies | 头像 | 备注 |
|---|---|---|---|---|---|---|
| Gemini | ✅ | K H | N/A (Google 账号) | 751 chars | 自定义 | body 实渲染 "Conversation with Gemini" |
| 豆包 | ✅ | 用户320735 | 7 | 631 | 自定义 | 历史对话列表 7+ 条 |
| ChatGLM | ✅ | GLM-5.1 | 4 | 1414 | 自定义 | 模型选择条 + "今天有什么新想法" |
| DeepSeek | ✅ | 罗 | 2 | 209 | 自定义 | 快速/专家/识图模式齐全 |
| ChatGPT | ✅ | keke (侧栏) | 8 | 2739 | 自定义 | 完整历史列表 |
| Grok | ✅ | lukebu | 3 | 1068 | 自定义 | 历史记录 6+ 条 |
| **元宝** | ❌ **未登录** | (无) | 4 | 885 | 默认 | body 明确显示 "未登录" + 登录按钮, 跳过本轮 broadcast |
| **文心一言** | ⚠️ **未跑** | (tab 走错) | - | - | - | yiyan.baidu.com 那个 tab URL 实际是 qianwen.com (被千问占), navigate_timeout, 本轮跳过 |
| 千问 | ✅ | Qwen1929 | 0 (cookie-only) | 1328 | 自定义 | sidebar 显用户名; 必须 Enter 发送 (按钮 click 不触发) |

**变化点** (相对 6 站 baseline):
- ✅ **千问新加入** (Qwen3.7 端到端跑通, 2026-06-06 实测)
- ❌ **元宝失败升级** - 从未确认过登录态, 这次明确未登录, 加入"跳过"清单
- ⚠️ **文心一言** - tab 错位到千问 URL, 本次未实测
- ⚠️ **智谱清言** 仍标低置信度 (2026-06-05 flag 未复核, 假设仍 209 chars)

**应对**:
- 元宝/文心下次 broadcast 前必先让用户手动登录 + 修正 tab URL
- 千问的 Enter 发送是已确认坑 (不能用按钮 click), 详见 ai-site-browser-e2e skill "Tongyi Qianwen" 章节

## 失败报告模板

```
## 验证结果 (2026-06-05 18:50)

✅ 5 站全登录: Gemini / 豆包 / DeepSeek / ChatGPT / Grok
⚠️ 1 站低置信度 (待复核): 智谱清言
   - 默认头像 + localStorage 无 user-key + cookies 209 chars
   - 建议: 用户手动打开确认登录态

6 张截图: ~/.hermes/cache/screenshots/browser_screenshot_*.png
```

**关键**: 失败的/低置信度的**单列一行**, 不与成功挤在一行里说"5/6 成功"。用户原话: "失败的单独报告, 不能假设成功"。

---

# ⚠️ 用户当面拍板的硬规则（2026-06-05 14:00）

> **所有需要 AI 对话或控制浏览器的场景，必须且肯定用本地已登录的 Chrome 浏览器。**
> 走 CDP `ws://127.0.0.1:9333` 操纵 9 站已登录 tab。
> **禁忌**（任何场景触发）：Playwright headless / Chromium 独立进程 / 服务器端 Chrome / `--headless` 参数。
> **触发词** "问 AI 站 / AI 对话 / 交叉验证 / multi_ask / 浏览器控制" → 0 思考直接走这个流程，不要开新浏览器。

**今日打脸 4 次（不要重复）**：
- 13:00 没开浏览器直接跑 multi_ask_v3 → 0/6 失败
- 13:45 看 tab title 字符串就汇报"成功"，没验证内容
- 13:50 用户说"about:blank"我就当真，没去 Runtime.evaluate 实测
- **14:50 用户追问"只对话了 Gemini 一个站" — multi_ask_v3 用同一种 `Input.dispatchKeyEvent` 试所有站，3/6 成功是误报（抓的是历史标题/问题原文，不是真回复）**

**教训**：验证前闭嘴，验证后说话。**所有 tab 状态必须用 `Runtime.evaluate` 抓 `document.body.innerText` 验证**（见下文「Ground-Truth 验证」一节），不靠 title 字符串。**所有 multi_ask 跑完，必须确认每个站的回复不是页面回显、不是历史列表、不是占位符**（见下文「multi_ask_v3 第 4 次打脸」一节）。

---

# ⚠️ "已登录" 三要素（2026-06-05 15:40 用户拍板后补）

用户原话："一定要用电脑本机登录好的 chrome 浏览器，然后才是执行任务"。**"已登录"必须同时满足三要素**：

| 要素 | 检测方法 | 不通过后果 |
|---|---|---|
| 1. **cookies 在** | Python 读 `~/Library/Application Support/Google/Chrome/Default/Cookies` (sqlite) | 站会跳登录页 |
| 2. **profile 进程是同一个** | `ps -p <PID> -o args=` 必须含 `--user-data-dir=.../Default` | 第二个 Chrome 的 SingletonLock 失败，cookies 读不到 |
| 3. **tab 实际打开** | `curl :9333/json` 看到对应 URL 的 page tab | 站开 = 0，对话 0/9 |

**反模式**（2026-06-05 15:40 真翻车）：
- ❌ "AI 站登录态丢失" → 误判。**cookies 一直在**（Default/Cookies 229KB 没被清），丢的是 **tab 页面**
- ❌ "Chrome 起了但 cookies 不见了" → 实际是**启了 2 个 Chrome 抢同一个 profile**，第二个读不到 SingletonLock
- ❌ "pkill -9 Chrome 应该没事" → pkill -9 **把带登录态的 Chrome 也杀了**，cookies 持久化但 tab 没了

**根因诊断清单**（登录态相关问题必跑）：
```bash
# 1. 看 system profile 里的 cookies 是否真在
python3 -c "
import sqlite3, os
db = os.path.expanduser('~/Library/Application Support/Google/Chrome/Default/Cookies')
conn = sqlite3.connect(f'file:{db}?mode=ro', uri=True)
for r in conn.execute('SELECT host_key, name FROM cookies ORDER BY host_key'):
    print(r)
"
# 2. 看 9333 上是哪个 PID 在跑 (是不是 system profile 启的)
lsof -nP -iTCP:9333 -sTCP:LISTEN
# 3. 看是不是有 2+ 个 debug Chrome 抢 profile
pgrep -fl "Google Chrome.*--remote-debugging-port"
```

**如果 2/3 不对**：跑 `bash scripts/chrome_keepalive.sh`（见下文）一次性修复。

---

# ⚠️ macOS 14+ DevTools 端口限制（2026-06-05 15:00 拍板）

`--remote-debugging-port=9222/9333` 启动 Chrome 在 macOS 14+ 上**有时不监听端口**（CDP HTTP `/json/version` 返回 000，进程在跑但 `lsof -i` 空）。

**根因**：macOS 14+ 在用 system profile 启动时，DevTools 端口需要额外的 system 授权（默认拒绝）。

**已知 Workaround**（按优先级）：

1. **隔离 profile + 显式 --proxy-server**（最稳，已验证 14:00 工作过）：
   ```bash
   "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
       --remote-debugging-port=9333 \
       --user-data-dir=/Users/aimac/.hermes/chrome-debug \
       --disable-extensions --no-first-run --no-default-browser-check \
       --proxy-server="http://127.0.0.1:7897" \
       --proxy-bypass-list="127.0.0.1,localhost,*.local"
   ```
   端口在 PID 起来后 5-8 秒监听。

2. **system profile 启动**（要登录态，但 9222 端口不监听概率高）：失败时**回退 1**。

3. **重启 Mac / 退出 Chrome 后重开**：最干净，但用户不一定愿意做。

**检测端口是否起来**：
```bash
sleep 5
lsof -i :9333 2>/dev/null | head -2
curl -s --connect-timeout 3 http://localhost:9333/json/version | python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('Browser','')[:30])"
```
→ 空 = 没起来，再等 5 秒或回退 1。

**完整兜底（端口死 3 次）**：
- 不要再挣扎换端口/换 proxy，**停下来问用户** "Chrome 端口不监听, 要不要重启 Mac / 退出 Chrome / 我用 9333 隔离 profile 重试"
- **不要写负面约束到 memory**（"Chrome 不可用"），因为环境一变就失效

---

# ⚠️ 多 Chrome 抢 user-data-dir — SingletonLock 冲突（2026-06-05 15:40 真翻车）

**症状**：
- 启了 Chrome 但登录态"消失"
- 第二个 Chrome 启后立即挂掉 / `lsof -i:9333` 空
- 多 AI 站 tab 全部跳登录页

**根因**：Chrome 用 `SingletonLock` / `SingletonSocket` / `SingletonCookie` 三个文件**强制单实例访问同一个 user-data-dir**。第二个 Chrome 启动时读不到 lock，行为：
- 读不到现有 cookies → **新 tab 都是未登录态**
- 写到 Default/Cookies 时锁失败 → **可能损坏 cookies 库**

**检测命令**（一键诊断）：
```bash
# 找出所有启了 debug port 的 Chrome 进程
pgrep -fl "Google Chrome.*--remote-debugging-port" | grep -v "Helper\|crashpad"
# 对比 9333 端口实际 PID
lsof -nP -iTCP:9333 -sTCP:LISTEN
# 如果两者列表不一样 → 抢 profile 冲突
```

**自动修复**：跑 `bash ~/.hermes/skills/browser-automation/browser-webpage-100score/scripts/chrome_keepalive.sh`（已附在本 skill 的 `scripts/` 下）。脚本会：
1. 找 9333 上 LISTEN 的 PID（保留它）
2. 找其他启了 `--remote-debugging-port` 但不在 9333 上的 PID → SIGTERM → SIGKILL
3. 如果 9333 没人监听 → 启动新 Chrome（用 system Default profile，**保留登录态**）

**launchd 部署**（每 5 分钟巡检）：
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>ai.hermes.chrome-keepalive</string>
    <key>ProgramArguments</key>
    <array><string>/bin/bash</string>
    <string>/Users/aimac/.hermes/skills/browser-automation/browser-webpage-100score/scripts/chrome_keepalive.sh</string></array>
    <key>StartInterval</key><integer>300</integer>
    <key>RunAtLoad</key><true/>
    <key>StandardOutPath</key><string>/Users/aimac/.hermes/logs/chrome_keepalive.log</string>
    <key>StandardErrorPath</key><string>/Users/aimac/.hermes/logs/chrome_keepalive_err.log</string>
</dict>
</plist>
```

**预防（写代码/启 Chrome 前）**：
- ❌ **永远不要并发启 2 个带 `--remote-debugging-port` 的 Chrome**
- ✅ 启前先 `pkill -9 -f "Google Chrome"`，**等 2 秒**再启新的
- ✅ 用保活脚本统一管理（不要手动 `open -na Google\ Chrome` 多开）
- ✅ launchd plist 调度时 `KeepAlive=false`，**保活只靠保活脚本**，避免多个调度器抢

**用户日常 Chrome vs Debug Chrome 的关系**（2026-06-05 实测结论）：
- **两个进程可以共享 system Default profile**（用户日常 + debug Chrome），但**只能 1 个带 `--remote-debugging-port`**
- debug Chrome 启时 `pkill` 会把日常 Chrome 也杀掉（因为都带 "Google Chrome" 字符串）→ **改用 `pkill -f "remote-debugging-port"` 更精准**
- cookies 在 system Default 里**全局共享**，所以日常 Chrome 登录后 debug Chrome 直接看到登录态

**根因 2 候选（pkill -9 误杀）**：
- `pkill -9 -f "Google Chrome"` 会**把所有带 Chrome 字符串的进程杀掉**（包括带登录态的）
- **正确**：`pkill -f "remote-debugging-port=9333"` 精准杀 debug Chrome
- 杀完再启 system profile 的 debug Chrome → tab 全空但 cookies 都在 → 重新打开 9 站 tab 就好

# ⚠️ execute_code 大块 Python 干 CDP 会被 BLOCKED（2026-06-05 15:15 拍板）

`execute_code` 写大块 Python 直接驱动 CDP / `Target.createTarget` / `Page.navigate` 等批量操作 → **会被用户 BLOCKED 拒授权**。

**正确做法**：用 `browser_navigate` / `browser_cdp` / `browser_click` 等**显式工具**逐站操作，**不要一坨 Python 走 execute_code**。

**例外**：execute_code **可以**用于纯本地数据处理（不调 CDP / 浏览器），例如 `python3 -c "import json; ..."` 解析 errors.log。

# ⚠️ Chrome 启动参数（不写 4 站会被 uBlock 挡死）

`chrome-debug-launcher.py` 默认带 uBlock Origin。`chatglm.cn` / `chatgpt.com` / `grok.com` / `deepseek.com` 中至少 4 站会被 uBlock 直接 ERR_BLOCKED_BY_CLIENT。

**启动 Chrome 必须加 `--disable-extensions`**：
```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    --remote-debugging-port=9333 \
    --user-data-dir=/Users/aimac/.hermes/chrome-debug \
    --disable-extensions \
    --no-first-run --no-default-browser-check
```

如果用户坚持要 uBlock，**单站白名单** + 9 站单独自启都行，但默认走 `--disable-extensions` 是最快的。

---

# Ground-Truth 验证（防止"看 title 报成功"的假阳性）

```python
import json, urllib.request, asyncio, websockets

# 拿 9 站 page WS
tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9333/json").read())
ws_map = {t['url']: t['webSocketDebuggerUrl'] for t in tabs if t.get('type') == 'page'}

async def check_real_content(name, ws_url):
    """实地读 document.body.innerText 前 200 字符, 证明页面真的渲染了"""
    async with websockets.connect(ws_url, max_size=5*1024*1024) as ws:
        await ws.send(json.dumps({
            "id": 1, "method": "Runtime.evaluate",
            "params": {
                "expression": "document.body ? document.body.innerText.slice(0,200) : 'NO_BODY'",
                "returnByValue": True
            }
        }))
        r = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
        return name, r.get('result',{}).get('result',{}).get('value','')

# 跑全部 9 站
for name, ws in ws_map.items():
    n, text = await check_real_content(name, ws)
    if 'NO_BODY' in text or len(text) < 10:
        print(f"❌ {n}: 真空白/没渲染")
    else:
        print(f"✅ {n}: 渲染了 ({len(text)} 字符)")
```

**判断标准**：
- 返回 `NO_BODY` 或空 → 页面没渲染（DOM 树为空）
- 长度 < 10 → 大概率登录页或 redirect 中
- 长度 > 50 且含中文/英文 → 真的 OK

---

# ⚠️ multi_ask_v3 第 4 次打脸 — 输入方式必须按站适配

**用户追问**（14:50）："https://www.doubao.com/chat 和 https://chatglm.cn/main/alltoolsdetail?lang=zh + https://chat.deepseek.com/ + https://chatgpt.com/ + https://grok.com/ + https://yuanbao.tencent.com/chat/naQivTmsDa + https://yiyan.baidu.com/ + https://www.qianwen.com/z 这些你都没有对话？只对话了一个 https://gemini.google.com/app/ed4eec4891dca095，这样哪里来的正确反馈"

**根因**：multi_ask_v3 用**同一种 `Input.dispatchKeyEvent` 试所有站**，没按站适配输入方式：
- DeepSeek = 必须逐字（`ta.value=` 无效）
- 豆包 / ChatGLM = `ta.value=` + `dispatchEvent`
- Gemini = AppleScript Cmd+V（zone.js 拦截）
- ChatGPT = `Input.insertText` on ProseMirror
- Grok = SKILL 已警告"换 Gemini/豆包"
- 元宝 / 文心 / 千问 = **未实测，不保证能用**

**multi_ask_v3 的"成功"假象**：抓页面历史对话标题 / 已存在的列表 / 问题原文，**根本没等到 AI 真回复**就返回 "✅ success"。

## 修正清单（下次跑前必做）

| 站 | multi_ask_v3 用的方式 | 实际应该 | 修法 |
|---|---|---|---|
| Gemini | `Input.dispatchKeyEvent` | AppleScript Cmd+V + Return | 单独加 `gemini_ask()` 函数 |
| DeepSeek | `Input.dispatchKeyEvent` | **逐字 `dispatchKeyEvent`**（keyDown.text="") | 当前实现是逐字但 keyDown.text 可能非空导致双倍字符 |
| 豆包 | `Input.dispatchKeyEvent` | `ta.value=` + Event | 用 `Runtime.evaluate` 直接设值 |
| ChatGLM | `Input.dispatchKeyEvent` | `ta.value=` + Event | 同上 |
| ChatGPT | `Input.dispatchKeyEvent` | `Input.insertText` on ProseMirror contenteditable | 走 `Input.insertText` |
| Grok | `Input.dispatchKeyEvent` | **换 Gemini/豆包**（SKILL 已警告） | 在 multi_ask_v3 跳过 Grok |
| 元宝 / 文心 / 千问 | `Input.dispatchKeyEvent` | 未知 | **标记"未实测，不保证能用"** |

## 假阳性判断（必加）

```python
def is_real_response(text, user_question):
    # 假阳性 1: 长度 < 50 → 极可能是占位符或加载中
    if len(text) < 50: return False
    # 假阳性 2: 末尾 = user_question 重复 → 是页面回显
    if user_question[:50] in text: return False
    # 假阳性 3: 含 "thinking" / "正在输入" / "..." 末尾占位 → 还在流式
    if any(s in text[-30:] for s in ['思考中', '正在输入', '...', 'thinking']): return False
    return True
```

**用户对 multi_ask_v3 的态度**：到 2026-06-05 14:50 为止，**multi_ask_v3 还没有一次成功的多站 cross-validate 输出**。**下次跑 multi_ask_v3 前必须先按上面修法改造**，否则不要跑。

---

# 本地浏览器识别网页 100 分任务

## 核心定位

用本地 Chrome（已登录9个AI站）做网页识别和自动化操作，100分 = 反指纹100分 + 读网页0分纸 + 自愈闭环全通。

**不依赖 OCR，不依赖截图，用 DOM 直接读内容。**

## 架构图

```
Hermes Agent
    │
    ▼
browser_cdp ──→ ws://127.0.0.1:9333 (debug Chrome)
    │                  │
    │              [已登录态]
    │                  │
    │    ┌─────────────┼─────────────┐
    │    ▼             ▼             ▼
    │ anti_detect.js  DOM读  自愈驱动
    │ (100分)        (innerText)  (click/type)
    │                  │
    └──────────────────┘
            │
            ▼
    结构化数据 → Hermes 记忆/处理
```

## 第一步：验证反指纹 100 分

### ⚠️ Chrome 重启 / 新 tab 后必须重新注入
- `addScriptToEvaluateOnNewDocument` 只对新打开的 tab 生效，Chrome 重启后丢
- 当前 tab 注入只在 session 内有效，session 断开就失效
- **每次跑任务前**先跑 `python3 ~/.hermes/scripts/anti_detect_inject.py --port 9333`

### 快速验证命令
```bash
# 检查 Chrome 是否在跑 + 端口
curl -s http://127.0.0.1:9333/json/version | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('webSocketDebuggerUrl','no debug port'))"

# 单次注入 + 验证（不需要重启Chrome）
python3 ~/.hermes/scripts/anti_detect_inject.py --port 9333 --verify
```

### 验证通过的标准（12项全绿）
```
✅ navigator.webdriver         → undefined（非false，false本身是指纹）
✅ navigator.plugins.length    → 3-5（不是0）
✅ navigator.languages         → ['zh-CN','zh','en-US','en']
✅ navigator.hardwareConcurrency → 8（非1）
✅ navigator.deviceMemory       → 8（非1）
✅ navigator.platform          → MacIntel
✅ window.chrome.runtime       → object（非undefined）
✅ Canvas noise               → getImageData含Math.random
✅ WebGL vendor              → Google Inc. / Intel
✅ Permissions.query          → notifications返回default
✅ __puppeteer_/__nightmare  → deleted
✅ PDF plugins               → 至少3个，含Native Client
```

### 如果分数不够
```bash
# 重新注入
python3 ~/.hermes/scripts/anti_detect_inject.py --port 9333

# 重启Chrome + extension持久化（最彻底）
bash ~/.hermes/scripts/launch_hermes_chrome.sh --kill && sleep 2 && bash ~/.hermes/scripts/launch_hermes_chrome.sh
```

## 第二步：CDP 直连浏览器（端口嗅探）

**禁止硬编码端口**，必须先嗅探：
```python
CDP_PORTS = [9333, 9444, 9222]

def detect_cdp_port():
    import urllib.request, json
    for port in CDP_PORTS:
        try:
            tabs = json.loads(
                urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=3).read()
            )
            if tabs:
                return f"ws://127.0.0.1:{port}", port
        except Exception:
            continue
    return None

result = detect_cdp_port()
if not result:
    raise RuntimeError("Chrome debug port 未找到，请启动 Chrome --remote-debugging-port=9333")
ws_url, port = result
```

## 第三步：连接目标标签页

```python
import urllib.request, json, websocket

def find_target_tab(keyword: str):
    """找包含keyword的标签页"""
    tabs = json.loads(
        urllib.request.urlopen("http://127.0.0.1:9333/json", timeout=5).read()
    )
    for t in tabs:
        if keyword.lower() in t.get("url","").lower() and t.get("type") == "page":
            return t["id"], t["webSocketDebuggerUrl"]
    return None, None

tab_id, ws_url = find_target_tab("doubao.com")  # 例：找豆包
if not ws_url:
    raise RuntimeError(f"未找到包含 '{keyword}' 的标签页")
```

## 第四步：读取网页内容（DOM优先，零OCR）

### 通用读法 innerText
```javascript
// Runtime.evaluate 注入到页面
expression = """
(function(){
    var texts = [];
    var walker = document.createTreeWalker(
        document.body, NodeFilter.SHOW_TEXT, null, false
    );
    var node;
    while(node = walker.nextNode()) {
        var t = node.textContent.trim();
        if(t.length > 0) texts.push(t);
    }
    return JSON.stringify({
        innerText: document.body.innerText.substring(0, 50000),
        links: Array.from(document.querySelectorAll('a')).map(a=>({text:a.innerText, href:a.href})),
        images: Array.from(document.querySelectorAll('img')).map(i=>({alt:i.alt, src:i.src})),
        title: document.title,
        url: location.href
    });
})()
"""
```

### 精准读法（知道结构时）
```javascript
expression = """
(function(){
    var items = [];
    document.querySelectorAll('.item,.productItem,.list-item').forEach(el=>{
        items.push({
            title: el.querySelector('h2,h3,.title')?.innerText||'',
            price: el.querySelector('.price,[class*="price"]')?.innerText||'',
            link: el.querySelector('a')?.href||'',
            shop: el.querySelector('.shop')?.innerText||''
        });
    });
    return JSON.stringify(items);
})()
"""
```

### React SPA 流式稳定检测（读 AI 真回复）
```javascript
// 等待流式输出完成，再读完整内容
expression = """
(function(){
    return new Promise(resolve=>{
        var lastLen = 0;
        var stable = 0;
        var timer = setInterval(()=>{
            var t = document.body.innerText.length;
            if(t === lastLen) {
                stable++;
                if(stable >= 4) {
                    clearInterval(timer);
                    resolve(JSON.stringify({body: document.body.innerText}));
                }
            } else {
                stable = 0;
                lastLen = t;
            }
        }, 500);
        setTimeout(()=>{
            clearInterval(timer);
            resolve(JSON.stringify({body: document.body.innerText}));
        }, 60000);
    });
})()
"""
```

### ⚠️ 豆包 Shadow DOM 特殊处理
豆包的消息区（`div.chat-message`）用 Shadow DOM 包裹，`innerText` 只能读到外层框架文字，AI 回复内容完全摸不到。

**症状**：`innerText` 正常返回但 AI 回复为空，`document.querySelector` 找 `.chat-message` 返回空数组。

**解法**：用 vision 截图兜底
```python
browser_vision(question="请完整读取页面上AI的回复内容")
```

**判断标准**：
```javascript
(function(){
    var msgEl = document.querySelector('[class*="message-bubble"], [class*="chat-message"]');
    if(!msgEl) return 'no message element found';
    var shadowRoot = msgEl.shadowRoot || msgEl.querySelector('*')?.shadowRoot;
    return shadowRoot ? 'SHADOW_DOM_detected' : 'normal_DOM';
})()
```
→ 返回 `SHADOW_DOM_detected` → 立即换 vision 截图

### Grok Next.js流式占位符（已知坑）
textarea 高度 16px，`__reactProps` 无 onChange，cross-origin iframe 触达不到。
**解法：换 Gemini 或豆包**，不在 Grok 上浪费时间。

## 第五步：自愈点击和输入（三级降级）

使用 `self_healing_driver.py`：
```python
import sys
sys.path.insert(0, '/Users/aimac/.hermes/scripts')
from self_healing_driver import SelfHealingDriver

driver = SelfHealingDriver(cdp_url="ws://127.0.0.1:9333")

driver.click("#submit-btn")     # Tier1: CDP querySelector
driver.click("登录")            # Tier2: AX label
driver.click((640, 400))       # Tier3: 截图+VLM找目标

driver.type_text("#search", "Mac mini M4 配置")

tree = driver.snapshot()
```

### 三级降级逻辑

| Tier | 方法 | 适用场景 | 失败原因 |
|------|------|---------|---------|
| 1 CDP | `Runtime.evaluate` + `querySelector` | 标准HTML按钮/输入框 | 元素不存在/disabled |
| 2 AX | `cua-driver` get_window_state + element_index | React Shadow DOM/浮动菜单 | 元素不在AX树 |
| 3 Coord | 截图 + VLM定位 + click(x,y) | 非常规元素/Canvas | 元素越界/不存在 |

## 第六步：9 个已登录站点输入方案（按站适配！）

### 5 个已实测（2026-06-03）
| 站点 | 输入方式 | 发送方式 | 状态 |
|------|---------|---------|------|
| **DeepSeek** | `Input.dispatchKeyEvent` 逐字 ✅ | Enter keyDown ✅ | ✅ |
| **豆包** | `ta.value=` + `Event` ✅ | 发送按钮 click ✅ | ✅ |
| **ChatGLM** | `ta.value=` + `Event` ✅ | Enter keyDown ✅ | ✅ |
| **ChatGPT** | `Input.insertText` on ProseMirror DOM ✅ | 按钮 click ✅ | ✅ |
| **Gemini** | AppleScript Cmd+V（绕过zone.js）✅ | Return ✅ | ✅ |

### 4 个登录态已确认（2026-06-04 批量验证），输入方案待实测
| 站点 | 已知信息 | 默认推断 | 待测 |
|------|---------|---------|------|
| **Poe** | 多模型聚合站（K H 账号） | React SPA，try `Input.insertText` | ⏳ |
| **Claude** | Anthropic 官方站（keke 账号） | ProseMirror 类 ChatGPT，try `Input.insertText` | ⏳ |
| **Perplexity** | 搜索式问答（K H 账号） | textarea 标准输入，try `ta.value=` | ⏳ |
| **Kimi** | 月之暗面（登月者6283 账号） | 长文本优化，React 输入框 | ⏳ |
| **通义千问** | 阿里 Qwen1929 账号 | ProseMirror/React | ⏳ |
| **Grok** | xAI（lukebu 账号） | ⚠️ Next.js流式占位符复杂 | ⚠️ 换Gemini/豆包 |

### DeepSeek 逐字输入（必须）
```python
async def deepseek_type(ws, text):
    for ch in text:
        await ws.send(json.dumps({
            "id": next_id(), "method": "Input.dispatchKeyEvent",
            "params": {
                "type": "keyDown", "key": ch, "text": "",  # text必须空！
                "keyCode": ord(ch.upper()), "windowsVirtualKeyCode": ord(ch.upper())
            }
        }))
        await asyncio.sleep(random.gauss(0.05, 0.015))
        await ws.send(json.dumps({
            "id": next_id(), "method": "Input.dispatchKeyEvent",
            "params": {"type": "char", "text": ch}
        }))
        await ws.send(json.dumps({
            "id": next_id(), "method": "Input.dispatchKeyEvent",
            "params": {"type": "keyUp", "key": ch}
        }))
        await asyncio.sleep(random.gauss(0.06, 0.02))
```

### 豆包/ChatGLM 快速输入（ta.value=）
```python
await ws.send(json.dumps({
    "id": next_id(), "method": "Runtime.evaluate",
    "params": {
        "expression": """
        (function(){
            var ta = document.querySelector('textarea');
            if(!ta) return 'no textarea';
            ta.value = '要输入的文本';
            ta.dispatchEvent(new Event('input', {bubbles:true}));
            ta.dispatchEvent(new Event('change', {bubbles:true}));
            return 'ok';
        })()
        """,
        "returnByValue": True
    }
}))
# 发送用Enter
await enter_key(ws)
```

## 第七步：智能滚屏（逼出懒加载内容）

```python
async def smart_scroll_to_bottom(ws, timeout=60):
    """自动找virtual-list容器，滚到底再回顶，强制渲染"""
    start = time.time()
    last_h = 0
    stable = 0
    
    while time.time() - start < timeout:
        r = await ws.send(json.dumps({
            "id": next_id(), "method": "Runtime.evaluate",
            "params": {
                "expression": """
                (function(){
                    var maxH=0, target=null;
                    document.querySelectorAll('div,main,section,article').forEach(d=>{
                        if(d.scrollHeight>d.clientHeight+10 && d.clientHeight>200){
                            if(d.scrollHeight>maxH){maxH=d.scrollHeight;target=d;}
                        }
                    });
                    if(target) return {sel:target.className.substring(0,50), h:target.scrollHeight};
                    return {sel:'window', h:document.documentElement.scrollHeight};
                })()
                """,
                "returnByValue": True
            }
        }))
        h = r.get("result",{}).get("value",{}).get("h", 0)
        
        if h == last_h or h == 0:
            stable += 1
            if stable >= 2: break
        else:
            stable = 0
            last_h = h
        
        await ws.send(json.dumps({
            "id": next_id(), "method": "Runtime.evaluate",
            "params": {
                "expression": f"(document.querySelector('[class*=virtual-list]')||window).scrollTop={h}",
                "userGesture": True
            }
        }))
        await asyncio.sleep(2.0)
    
    await ws.send(json.dumps({
        "id": next_id(), "method": "Runtime.evaluate",
        "params": {"expression": "(document.querySelector('[class*=virtual-list]')||{}).scrollTop=0;window.scrollTo(0,0)"}
    }))
```

## 完整任务模板

```
【任务】识别 / 读取 / 操作 网页

① 验证反指纹：python3 ~/.hermes/scripts/anti_detect_inject.py --port 9333 --verify
   → 12项全绿才继续

② ⚠️ 用 Runtime.evaluate 抽 1-2 个 tab 实地验证 body.innerText（防止"看 title 报成功"）
   → 长度 > 50 且含中文/英文 才算真渲染

③ 连接Chrome：detect_cdp_port() → ws://127.0.0.1:9333

④ 找目标tab：find_target_tab("关键词") → tab_id + ws_url

⑤ 注入反指纹（如需要）：
   browser_cdp(method="Runtime.evaluate",
     expression="...anti_detect_mini.js IIFE...",
     target_id=tab_id)

⑥ 读取内容：Runtime.evaluate → innerText / 精准CSS选择器
   → 结构化JSON

⑦ 操作（如需输入）— 按站适配：
   - DeepSeek：逐字 Input.dispatchKeyEvent
   - 豆包/ChatGLM：ta.value= + dispatchEvent
   - ChatGPT：Input.insertText on ProseMirror
   - Gemini：AppleScript Cmd+V
   - Grok：换 Gemini/豆包
   - 元宝/文心/千问：未实测，不保证

⑧ 滚屏：smart_scroll_to_bottom（如有虚拟列表）

⑨ 自愈兜底：SelfHealingDriver.click() 三级降级

⑩ 验证结果：is_real_response() 排除假阳性（详见"multi_ask_v3 第 4 次打脸"）
```

## 验证 100 分标准

```bash
# 一键跑全部验证
python3 /tmp/verify_all_3.py

# 期望输出
✅ plugins.length = 3+
✅ navigator.webdriver = undefined
✅ navigator.plugins 含 Native Client
✅ 自愈驱动 Tier1/Tier2/Tier3 9条 attempts 全通
✅ 轨迹录制 start/stop 正常
总分: 100 / 100
```

## Cross-reference

This skill is the **verification + injection wrapper** (反指纹100分 + 4个缺口跑分) for browser-driven AI tasks. For site-specific input/reading tactics across the 9-station roster (豆包 Shadow DOM pitfall, DeepSeek char-by-char, ChatGLM React dispatcher, Gemini zone.js), see umbrella `browser-automation/ai-site-browser-e2e`. Use this skill to get the browser to 100/100, then defer to `ai-site-browser-e2e` for per-site escalation tables.

## 关键文件

| 文件 | 用途 |
|------|------|
| `~/.hermes/scripts/anti_detect_inject.py` | 批量给所有tab注入反指纹 |
| `~/.hermes/scripts/self_healing_driver.py` | 三级降级自愈驱动 |
| `~/.hermes/anti_detect_mini.js` | 压缩版2.3KB，适合单次注入 |
| `~/.hermes/scripts/launch_hermes_chrome.sh` | 启动Chrome + extension |
| `references/9-tab-verification-failures-2026-06-05.md` | 今日 3 次打脸原始案例（必读） |
| `references/bulk-open-9-ai-stations.md` | 9 站批量打开流程 |
| `references/2026-06-05-chrome-multi-owner-root-cause.md` | **5 个程序争 Chrome 真根因** + 治本 3 步 + 验证命令（"登录态平白无故丢"事件复现配方）|
| `references/6-station-login-baseline-2026-06-05.md` | **6 AI 站 4 维证据登录态 baseline** (2026-06-05 18:50 拍板) + 智谱"低置信度"坑点 + 复现配方 |
| `references/multi-ask-cross-validate-20260605.md` | **多 AI 站交叉验证 + 9 维度自评框架**（跑 N 站问同一问题 → 共识表 + 否决违反硬规则的 + 自评打分，2026-06-05 3 站实测模板）|
| `scripts/verify_9_tabs.py` | 9 站 tab 实地验证脚本（黄金流程步骤 5） |
| `scripts/chrome_keepalive.sh` | Chrome 9333 单实例保活（每 5 分钟巡检，杀重复进程保 system profile 不丢 cookies） |
| `/tmp/verify_all_3.py` | 100分验证脚本（临时）|

## 必加载: 这是 multi_ask / 9 站交叉问 / browser_navigate 的入口

**任何要"问 AI 站 / 跑 multi_ask / 浏览器控制 / cross-validate 9 站"的场景, 0 思考先加载本 skill**. 本 SKILL 第一步"反指纹 12 项 + 9 站 navigate + 验证" 是 **anti_fingerprint + multi_ask_v3 工作流**的强制前置. 跳过这一步 = 0/6 失败 (见 meta/verification-before-reporting/references/2026-06-05-multi-ask-session.md).

## 9 站扩展 / 固化纪律（2026-06-05 拍板）

**凡是写"已登录 N 站"的清单，N 必须等于 fact_store / session_search 里实际登录过的站数**，不是实测过的站数。

| 角色 | 数量 | 处理方式 |
|------|------|---------|
| 实测过输入方案 | 5 | ✅ 详细写"输入方式/发送方式"列 |
| 仅登录态 | 4 | 写明"默认推断 / 待测"，不假装已实测 |
| 已登录但极复杂 | 1 (Grok) | 写"⚠️ 换用 Gemini/豆包"降级方案 |

**反模式**：只列实测过的站，假装"已登录 N 站"= "已掌握 N 站"。

**扩展新站时的固化模板**：
1. 在 `references/<station>-input-strategy.md` 单独写一份"实测报告"
2. 跑通 1-2 个真实问题截图验证
3. 测出"输入/发送/读取"三件套
4. 把 ①②③ 压成一行进本 skill 的"已实测"表
5. 从"待测"表移到"已实测"表，**保留账号信息一行**

**触发词**："固化/写进 skill/列已登录站" → 0 思考先列全部 9 站 + 标注实测/待测，不挑拣。

## 已知坑速查

| 坑 | 症状 | 解法 |
|----|------|------|
| DeepSeek逐字双倍字符 | 输入"你好"变成"你你好" | keyDown.text="" 必须空 |
| 豆包Keychain加密cookie | cookies的value为空 | 在debug Chrome里重新登录一次 |
| 豆包消息区Shadow DOM | innerText/querySelector全返回空 | browser_vision截图+VLM读取 |
| Gemini zone.js拦截 | Input.dispatchKeyEvent无效 | AppleScript Cmd+V绕过 |
| Grok Next.js流式占位符 | textarea 16px高，无__reactProps | 换Gemini或豆包 |
| 虚拟列表懒加载 | 滚屏后内容才渲染 | smart_scroll_to_bottom |
| Shadow DOM穿透 | btn.click()无效 | JS内部focus() + Enter |
| JSON.stringify Boolean丢失 | `JSON.stringify({w:navigator.webdriver})` | `String(navigator.webdriver)` |
| CDP参数类型 | 报"Invalid parameter" | modifiers/clickCount必须int不是str |
| Chrome重启/新tab反指纹掉分 | 100→97，plugins消失 | 跑任务前必跑 `anti_detect_inject.py --port 9333` |
| multi_ask_v3 假阳性"成功" | 报告"3/6 成功"但只真对话 1 站 | 必加 `is_real_response()` 校验 + 按站适配输入方式 |
| "已登录"误判为"丢登录态" | 看到 9 站 tab 空就报告"登录丢了" | 跑"已登录三要素"诊断：cookies 文件 + 9333 PID 的 user-data-dir + tab 列表 |
| 多 Chrome 抢同一 user-data-dir | SingletonLock 失败，第二 Chrome 读不到 cookies | `pgrep -fl "Google Chrome.*--remote-debugging-port"` 看重复进程；`bash scripts/chrome_keepalive.sh` 自动修 |
| `pkill -9 -f "Google Chrome"` 误杀 | 带登录态的 Chrome 也被杀，cookies 持久化但 tab 全空 | 改用 `pkill -f "remote-debugging-port=9333"` 精准杀 debug Chrome |
| 5 个程序都管 Chrome，profile 不统一 | "登录态平白无故丢" 真根因：`ai.hermes.chrome.plist` + `com.aimac.hermes-chrome-debug.plist` + `chrome-on-demand.sh` 用 `~/.hermes/chrome-debug` 隔离 profile；`chrome_keepalive.sh` 用 `.../Chrome/Default` system profile；`self_evolution.sh` 每小时 `pkill -f "chrome.*9333"` | 治本：2 个旧 plist rename `.disabled`，`chrome-on-demand.sh` 改用 system Default，`self_evolution.sh` 委托给 keepalive 而非自启。验证：`pgrep -fl "Google Chrome.*--user-data-dir"` 只剩 1 个 path |
| 用户拍板"治本不治标" / "平白无故丢" | 听到这个 trigger 别再加 5 个兜底脚本，去 audit 整个 surface 找根因 | 步骤：① 列所有管组件的程序 ② 找出用错 config 的 ③ disable/合并 ④ 验证用户原问题消失 |
| 智谱清言"低置信度"登录态 (2026-06-05) | 默认头像 + localStorage 无 user-key + cookies 209 chars (其他站 209~2757) | 跑对话前必先用"4 维证据验证 SOP"复核; 标记"待复核"不算成功也不算失败 |
| 浏览器"已登录"必须 4 维证据 (2026-06-05 18:50) | 单看 title / 单看 AX 树 / 单看 vision 都可能误报"成功" | 走 4 步: navigate → snapshot → console JS (localStorage+cookies) → vision; 失败/低置信度单列报告, 不混入成功 |

## 治本 3 件套 SOP（2026-06-05 15:40 实测落地，从 5 个程序争 Chrome → 1 个保活）

**用户原话**："平白无故丢失登录记录数据，这不解决永远在维修的路上"

**原则**：不要叠加第 6 个保活脚本，**先 audit 整个 surface** — 有几个程序在管这个资源？它们各自用的什么 config？哪个跟用户原问题相关？

### Step 1: 列所有管组件的程序（**5 个程序管 Chrome 的反面教材**）

```bash
# 1) 找所有引用 Chrome 9333 的 plist
find /Users/aimac/Library/LaunchAgents -name "*.plist" 2>/dev/null | xargs grep -l "remote-debugging\|9333\|chrome" 2>/dev/null
# 2) 找所有启停 Chrome 的脚本
grep -rl "Google Chrome" ~/.hermes/scripts/ 2>/dev/null
# 3) 看 launchd 实际加载的 Chrome 相关服务
launchctl list | grep -i chrome
```

**今天实测的 5 个程序**（登录态"丢"事件时的状态）：
| # | 程序 | profile | 行为 | 后果 |
|---|---|---|---|---|
| 1 | `ai.hermes.chrome.plist` (5/9 旧) | 没指定 → 走 system Default | launchd 启 | 跟 on-demand 抢 user-data-dir |
| 2 | `com.aimac.hermes-chrome-debug.plist` (6/1 旧) | `~/.hermes/chrome-debug` 隔离 | launchd 启 | 跟 system 隔离，cookies 不共享 |
| 3 | `chrome-on-demand.sh` | `~/.hermes/chrome-debug` 隔离 | 手动 start | 跟 2 同 profile |
| 4 | `self_evolution.sh` line 78 | N/A | **每小时 `pkill -f "chrome.*9333"` 强杀** | 杀光带登录态的 Chrome |
| 5 | `chrome_keepalive.sh` (新增) | system Default | 5 分钟巡检 | **唯一保活** |

### Step 2: 找出用错 config 的

**冲突点**：
- 程序 1+5 都用 system Default → 抢 profile
- 程序 2+3 都用 `chrome-debug` 隔离 → 跟 system 隔离 = cookies 不共享
- 程序 4 杀 system Chrome → cookies 持久化但 tab 全空 = "登录态丢"假象

### Step 3: disable / 合并（按这个顺序）

```bash
# A) 旧 plist 改名 .disabled (不删, 保留回滚)
cd ~/Library/LaunchAgents/
launchctl unload ai.hermes.chrome.plist
mv ai.hermes.chrome.plist ai.hermes.chrome.plist.disabled
launchctl unload com.aimac.hermes-chrome-debug.plist
mv com.aimac.hermes-chrome-debug.plist com.aimac.hermes-chrome-debug.plist.disabled

# B) 改 on-demand 用 system Default
# patch ~/.hermes/scripts/chrome-on-demand.sh:
#   --user-data-dir="/Users/aimac/.hermes/chrome-debug"
#   → --user-data-dir="$HOME/Library/Application Support/Google/Chrome/Default"

# C) 改 self_evolution 不要 pkill, 委托 keepalive
# patch ~/.hermes/scripts/self_evolution.sh line 78:
#   pkill -f "chrome.*9333" + open ...
#   → do_run bash $HERMES_HOME/scripts/chrome_keepalive.sh
#   (最后兜底: osascript 通知用户, 不强杀)
```

### Step 4: 验证用户原问题消失（按 14:00 硬规则实地验证）

```bash
# 1) launchd Chrome 服务数 5 → 1/2
launchctl list | grep -i chrome
# 期望: 只有 ai.hermes.chrome-keepalive (+ chrome-devtools-mcp)

# 2) system Default profile cookies 还在
python3 -c "
import sqlite3, os
db = os.path.expanduser('~/Library/Application Support/Google/Chrome/Default/Cookies')
conn = sqlite3.connect(f'file:{db}?mode=ro', uri=True)
print('cookies:', conn.execute('SELECT COUNT(*) FROM cookies').fetchone()[0])
"
# 期望: 400+ (含 AI 站 84 条)

# 3) 9333 在 system profile 的 PID 上
lsof -nP -iTCP:9333 -sTCP:LISTEN
# 对比 Chrome 进程 args
ps -p <PID> -o args= | grep -c "Chrome/Default"
# 期望: 1 (system profile)

# 4) 4 站 (Claude/豆包/Grok/智谱) 实际访问, 不重登
for site in claude.ai doubao.com grok.com chatglm.cn; do
    curl -sI --max-time 5 "https://$site" | head -1
done
# 期望: 全部 2xx/3xx, 不跳 login
```

### 治本 vs 治标 判断矩阵

| 用户原话 | 信号 | 反模式（治标）| 正确（治本）|
|---|---|---|---|
| "平白无故丢" / "维修的路上" | 不要再加保活 | 再加第 6 个保活脚本 | audit 整个 surface, 找根因 |
| "对账表" | 删错了用户会骂 | 列 11+12 行大表 | 1-2 行对账 + 1 句确认 |
| "有问题默认修" | 修 bug 不要问 | 抛 3 选 1 让用户选 | 直接修 + 跑验证 + 汇报 |

### 治本不删主体 原则

| 类别 | 处理 |
|---|---|
| 不可逆（删文件/卸载/格式化）| 必须授权 |
| 治本 disable | rename `.disabled` 不删, 留回滚路径 |
| 修代码 bug | 默认修, 不问 |
| 改生产 config | 授权 |

**反面教材**：今天我第一版方案是"再加 2 个保活脚本"。如果走那条路，2 个月后会有 7 个保活脚本，登录态该丢还丢。**治本只有一条路：audit 整个 surface**。
