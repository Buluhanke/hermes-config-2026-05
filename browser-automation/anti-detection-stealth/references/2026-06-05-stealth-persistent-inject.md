# 2026-06-05 Stealth 持久注入实战 transcript

## 背景
完成了 P0 ⑥ 防御维度（智谱/豆包 共识推荐 stealth 注入）。本 session 之前 anti-detection-stealth skill 已经有 11 招反指纹 + 3 注入方式，但**所有方式都是"单次临时"**（`Runtime.evaluate` 直接传 IIFE）— 没有"持久跨所有 tab 跨导航" 的能力。

## 新能力: Page.addScriptToEvaluateOnNewDocument 持久注入
- 之前 anti-detection-stealth 提到过这个 CDP 方法（在"方式 2"），但**没有给完整可运行模板**
- 这次写了 `scripts/stealth_inject.py` + `scripts/stealth.js`，**完整实现**：
  1. `Page.addScriptToEvaluateOnNewDocument({source: 完整 IIFE, worldName: 'MAIN'})` → 每个新 doc 自动跑
  2. `Runtime.evaluate({expression: 完整 IIFE, runImmediately: true})` → 当前页立即生效
  3. 配合 launchd 30 分钟周期 plist 跑一遍 → 真"治本"持续 stealth

## 踩到的 2 个新坑（**没在原 skill 里**）

### 坑 1: Chrome 148+ 默认 push event 帧，ws.recv() 拿不到 command response
**症状**: 注入 stealth 时 `cd.send('Page.addScriptToEvaluateOnNewDocument', ...)` 然后 `cd.recv()` 拿到的不是 `{"id": 2, "result": {...}}` 而是 `{"method": "Runtime.executionContextCreated", "params": {...}}` —— `result['result']['value']` 直接 `KeyError: 'result'`。

**根因**: Chrome 148+ CDP 协议在 socket 上**主动 push event**（`Runtime.executionContextCreated` / `Page.frameNavigated` / `Target.targetInfoChanged` 等），客户端 `ws.recv()` 拿到的**第一个**消息是 event 而不是给对应 id 的 command response。

**修法**: 用一个循环，直到拿到 `id` 字段匹配**自己发的 id** 的消息：
```python
def sendrecv(self, method, params=None):
    self.msg_id += 1
    my_id = self.msg_id
    self.ws.send(json.dumps({'id': my_id, 'method': method, 'params': params or {}}))
    while True:
        msg = json.loads(self.ws.recv())
        if 'id' in msg and msg['id'] == my_id:
            return msg
```

**经验**:
- 之前 `cdp-browser-automation` skill 里的 `Runtime.evaluate` 调用也是单次 `recv()`，**没踩这个坑是因为有时序**（CDP 总是先发 command response 再发 event），**并发**才会撞
- 2026-06-05 这个 stealth 注入脚本是**多 tab 顺序**调用，**但 addScript 后** Chrome 立即 push `Runtime.executionContextCreated` 把 command response 推到第二帧

### 坑 2: dry-run 路径重复 print `✅`
**症状**: `python3 stealth_inject.py --dry-run` 跑出 `[DRY-RUN] would inject URL` **后面又跟** `✅ URL`。
**根因**: main 循环里 `if inject_stealth(... dry_run=True): print('✅')` —— dry-run 时 `inject_stealth` 已 print `[DRY-RUN]` 并返 True，main 仍 print `✅`。
**修法**: 把 main 循环拆成 dry-run / 真跑两路径，dry-run 时不调 main 的 print。

## 实测 10/10 满
跑 `python3 stealth_inject.py --verify` 验 bot.sannysoft tab：
- `[10/10 1/1/1/1/1/1/1/1/1/1] https://bot.sannysoft.com/`
- 10 项检查：webdriver=false / plugins>=3 / plugins_names>=3 / languages>=2 / chrome.runtime=object / stealth_injected=true / webgl_vendor='Google Inc. (Apple)' / webgl_renderer startswith 'ANGLE' / permissions=ok / cdc_keys=0

## launchd 30 分钟保活
`ai.hermes.stealth-watchdog.plist` (StartCalendarInterval Minute=0,30) — 启动时 + 每 30 分钟跑一次 `stealth_inject.py`，所有 tab 重新注入。
- 验证 launchd `last exit code = 0` ✅
- 治本：tab 关闭/新建/刷新都自动有 stealth

## 关联
- 这次的 RAG (P0 ⑤)、watchdog bug 修复 (P0 ⑨)、VLM 路由 (P1 ①) 都是**独立新能力**，但 stealth 是**有现成 skill (anti-detection-stealth) 的拓展**——按偏好 1 应 patch 该 skill
- 已 patch 那个 skill 加上 `Page.addScriptToEvaluateOnNewDocument` 完整模板 + 2 个新坑的详细记录
