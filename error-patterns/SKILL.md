---
name: error-patterns
description: 常见错误模式的根因分析 + 修复方案。来源：auto_skill_from_failure.py 从 agent.log 每日抽取，6类核心模式。
triggers:
  - TimeoutError
  - ConnectionError
  - JSON parse error
  - Import error
  - Permission denied
  - CDP attach failed
pitfalls:
  - 看到错误直接猜原因——应先读完整 traceback
  - 只看错误行不看不支持的方法——先确认字段存在
  - 重复同一个错误3次以上不沉淀——立即写fact_store
---

# 错误模式速查手册

## CDP attach failed (严重度4)

频率: 4次（低频但每次都阻断浏览器操作）

触发: browser_cdp 调用时 target 已消失或尚未就绪

根因:
- 页面还在导航，CDP tab 未完全加载
- WS URL 指向的 page 已关闭
- mirror Chrome (9222) 和用户主 Chrome 是独立实例

修法:
- browser_cdp_tool.py: 加 Step0 page就绪轮询（Target.getTargets 确认 target 存在才 attach）
- 落地文件: tools/browser_cdp_tool.py

## TimeoutError (严重度2)

频率: 479次（最高频，其中420次是QQBot WebSocket code=4009）

触发: QQBot WebSocket session timeout / API call 超时

根因:
- QQBot WS 每30分钟 idle 超时（code=4009）
- NVIDIA API / GLM API 响应慢
- 慢查询未设 timeout

修法:
- QQBot code=4009: adapter 有自动重连 + logger.warning 降噪为 logger.info（已落地）
- ConnectionError retry: auxiliary_client.py 已实现 _is_connection_error + 2次 exponential backoff 重试
- Command timed out: cron 脚本加 timeout 参数

## ConnectionError (严重度3)

频率: 214次

触发: NVIDIA/GLM API 连接失败

根因: API endpoint 不达 / 网络抖动 / API key 权限问题

修法（已落地）:
- auxiliary_client.py: _is_connection_error() 识别所有常见连接错误类型
- _is_transient_transport_error() + 2次 exponential backoff 重试
- 覆盖: APIConnectionError, APITimeoutError, DNS/SSL/connection refused/reset 等

## Import error / Permission denied (严重度2/3)

频率: 14次（9+5）

触发: launchd 启动的脚本 cwd=/（只读），相对路径资源加载失败

根因: launchd 启动 Python 时 cwd=/，所有相对路径失效

修法（已落地）:
- 16个 plist 全部补上 WorkingDirectory=/Users/aimac/.hermes
- 修复脚本: /tmp/fix_launchd_wd.py
- 落地: ai.hermes.*.plist 全部更新并 reload

## JSON parse error (严重度1)

频率: 13次

触发: API 返回非 JSON 或截断的响应

根因: API 超时返回空 body / partial body / HTML 错误页

修法（已落地）:
- browser_tool.py: _resolve_cdp_endpoint() 加 JSONDecodeError 特判，200状态码非JSON打 warning 不抛异常
- browser_cdp_tool.py: ws.recv() json.loads 两处加 try/except，忽略非JSON帧

## OmniRoute 安装踩坑（2026-07-10, 严重度5）
asar 打包不完整: DMG 里 app.asar 缺 ws-a972e7ffa40ff725 等 14 个包 → 重新下载 OmniRoute-x.x.x-arm64.dmg
better-sqlite3 ABI mismatch (NODE_MODULE_VERSION 137 vs 147): dist/node_modules/ 版本太旧 → rm -rf dist/node_modules/better-sqlite3 让 Node 向上找 root 的兼容版本
npm rebuild 假成功: binary 日期不变说明没真编译 → 直接删坏版本，不要依赖 rebuild
Desktop app 进程在但不监听端口: WebView 渲染失败 → 走 CLI omniroute serve
所有 API 500: storage.sqlite 空，从未完成 onboarding → omniroute setup --add-provider

## 修法通用流程

1. 确认根因：读完整 traceback，不只看错误行
2. 加容错：try/except，字段先 .get()
3. 写 fact_store 标记已修（trust=0.9）
4. 高频错误(>3次/天) → 立即生成/更新 skill
