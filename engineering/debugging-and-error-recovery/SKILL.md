---
name: debugging-and-error-recovery
description: 4-phase root cause debugging — understand errors before attempting fixes. Prevents shooting in the dark.
triggers:
  - "收到了错误信息但不知道根因"
  - "同一个bug反复出现"
  - "修复后引入新的bug"
  - "错误信息无法直接对应到代码位置"
  -
version: 1.0.0 "用户报告的现象和代码对不上"
---

# Debugging and Error Recovery

## Overview

遇到错误时，**先分析，后修复**。不先理解根因就动手修，是最大的时间浪费来源。统计显示>60%的bugfix引入新bug，是因为跳过了根因分析阶段。

## When to Use

当遇到错误、异常、崩溃、或不符合预期行为时，不要立即尝试修复。先用此skill进行系统化根因分析。

## Process

### Phase 1: 理解错误（不是猜，是读）

#### 1.1 提取错误信号
- 完整错误信息（不是摘要）
- 错误类型（TypeError, IndexError, 503, 401等）
- 堆栈跟踪（stack trace）的每一行
- 发生时间、频率、触发条件

#### 1.2 定位错误位置
- 堆栈中哪一行是真正的犯错地点（非抛出地点）
- 向上追溯调用链，找到第一个不信任的调用
- 区分：错误产生者（root cause）vs 错误传播者（symptom）

#### 1.3 定义"正确行为"
- 出错前预期是什么？
- 实际发生了什么？
- 差距在哪里？

### Phase 2: 形成假设（不是蒙，是推理）

#### 2.1 列出所有可能原因
- 列出≥3个假设，按可能性排序
- 标注每个假设的置信度（高/中/低）
- 识别每个假设对应的代码位置

#### 2.2 设计验证实验
- 每个假设需要一个"如果…则…"的验证方式
- 选择验证成本最低的假设优先验证
- 准备：需要什么数据/工具/环境？

#### 2.3 检查常见陷阱
- 空指针：谁传入了null？
- 异步：callback的timing正确吗？
- 并发：race condition？
- 环境：本地/生产配置差异？
- 版本：依赖库版本匹配吗？

### Phase 3: 验证假设（不是试，是验证）

#### 3.1 执行验证
- 按置信度顺序验证假设
- 每个验证只改一个变量
- 记录每次验证的结果

#### 3.2 交叉验证
- 用日志/断点/print确认假设
- 找到能同时排除其他假设的"唯一证据"
- 确认根因后停止验证，不要继续挖掘

#### 3.3 复现验证
- 找到最小复现路径
- 在隔离环境验证根因
- 记录复现步骤

### Phase 4: 修复与验证（不是改，是确保）

#### 4.1 制定修复方案
- 修复的是根因，不是症状
- 考虑所有调用路径是否受影响
- 考虑向后兼容性
- 准备回滚方案

#### 4.2 小步验证
- 修复后立即运行最小测试
- 先单元测试，再集成测试
- 确认错误不再出现

#### 4.3 回归检查
- 确认修复未破坏其他功能
- 检查相似代码是否存在同类问题
- 更新相关文档

## Common Rationalizations

| 常见借口 | 真相 | 反制 |
|---------|------|------|
| "这个错误信息很清楚，直接改就行了" | 错误信息描述的是症状，不是根因 | 先问：是什么导致了这个状态？ |
| "上一次就是这么修的" | 同样的症状可能有完全不同的根因 | 每次都重新分析，不套用旧经验 |
| "先试试这样改" | 试出来的修复引入了新bug的概率>60% | 先形成假设，再验证，再修复 |
| "看起来是XX模块的问题" | 根因可能离错误出现地很远 | 完整追溯调用链 |
| "生产环境才能复现" | 任何bug都可以在开发环境复现 | 先创造复现条件，再修复 |
| "注释掉试试" | 注释掉的代码积累是技术债 | 只在验证时临时注释，验证完必须找到正确解法 |

## Red Flags

- 尝试修复前没有完整读错误信息
- 没有定位到根因就开始改代码
- 修复后没有运行任何测试
- 同样的错误在3个以上不同地方出现
- 修复引入了新的错误或警告
- 认为是"玄学问题"而不继续追查

## Verification

验证清单：

- [ ] 完整错误信息已记录（不是截图或摘要）
- [ ] 根因已明确定义（不是模糊的"XX模块有问题"）
- [ ] 假设已列出并按置信度排序
- [ ] 每个假设都有对应的验证结果
- [ ] 修复方案针对根因而非症状
- [ ] 修复后相关测试通过
- [ ] 修复未引入新的警告或错误
- [ ] 最小复现路径已记录

---

## Appendix A: 常见错误模式库

按领域分类的高频错误模式，帮助快速识别根因。

### A.1 JavaScript/TypeScript

| 错误模式 | 典型表现 | 根因 | 验证方法 |
|---------|---------|------|---------|
| **空引用链** | `Cannot read property 'x' of null` | 调用链中某个节点为null | 逐层console.log或断点，定位第一个null |
| **异步地狱** | 结果顺序错乱、undefined | Promise/await使用错误 | 检查await位置是否在正确的async函数内 |
| **闭包陷阱** | 循环中绑定旧值 | for循环变量在闭包中未捕获 | 使用let而非var，或使用forEach |
| **类型体操失败** | `Type 'X' is not assignable to type 'Y'` | 接口定义不一致 | 对照接口定义，检查实际传递的字段 |
| **内存泄漏** | 内存持续增长 | 事件监听器未清理、定时器未清除 | Chrome DevTools Memory面板录制 |
| **循环依赖** | `Module not found` 或栈溢出 | A imports B, B imports A | 检查import语句，构建工具警告通常会提示 |

### A.2 Python

| 错误模式 | 典型表现 | 根因 | 验证方法 |
|---------|---------|------|---------|
| **可变默认参数** | 函数输出随调用累积 | 默认参数使用list/dict | 使用None作为默认值，显式创建 |
| **Python2/3编码** | `UnicodeEncodeError` | 字符串/字节混淆 | 检查字符串类型（str vs bytes） |
| **GIL瓶颈** | 多线程性能不增反降 | 全局解释器锁 | 使用multiprocessing替代threading |
| **模块缓存** | 修改模块后行为不变 | import缓存未失效 | 重启Python进程或使用importlib.reload |
| **迭代器耗尽** | StopIteration或无输出 | 迭代器已被消费 | 检查是否重复使用同一迭代器 |
| **super()位置错误** | `TypeError: super() ... arguments` | 多继承时调用顺序错误 | 确保super()在子类方法首行调用 |

### A.3 API/网络

| 错误模式 | 典型表现 | 根因 | 验证方法 |
|---------|---------|------|---------|
| **幂等性忽略** | 重试后状态异常 | GET/POST语义混淆 | 确认HTTP方法与操作语义匹配 |
| **响应截断** | JSON parse失败但请求成功 | 分页/流式响应未完整处理 | 检查响应头Content-Length vs 实际长度 |
| **重定向丢失body** | POST变GET，body丢失 | 跟随重定向时method变化 | 30x响应检查，明确禁用自动重定向 |
| **连接池耗尽** | 请求排队、超时 | 连接未释放、超设上限 | 检查连接关闭（close()）或使用with语句 |
| **DNS缓存毒化** | 切换环境后仍连旧服务器 | 客户端DNS缓存 | 重启客户端或清除缓存 |

### A.4 数据库

| 错误模式 | 典型表现 | 根因 | 验证方法 |
|---------|---------|------|---------|
| **N+1查询** | 查询数量=1+N*关联数 | 循环中查询关联 | 检查ORM日志或使用selectinload |
| **连接泄漏** | 连接数持续上升 | 异常路径未释放连接 | finally块确保close() |
| **事务未提交** | 数据不保存 | 异常导致回滚 | 检查commit()是否在finally中 |
| **锁等待超时** | 长时间卡住后报错 | 长事务持有锁 | 缩小事务范围，减少锁粒度 |
| **索引失效** | 查询突然变慢 | LIKE前缀%、函数索引列 | EXPLAIN分析执行计划 |

---

## Appendix B: LLM API 错误速查表

### B.1 OpenAI 兼容 API 错误码

| HTTP状态码 | 错误类型 | 含义 | 立即处理 |
|-----------|---------|------|---------|
| 400 | `invalid_request_error` | 请求格式错误（缺字段、字段类型错误） | 检查请求体JSON结构 |
| 400 | `invalid_api_key` | API Key格式错误或已被撤销 | 重新生成Key |
| 401 | `authentication_error` | 认证失败（Key无效/过期） | 确认Key有效期内 |
| 403 | `permission_error` | 无权限（配额超限/地区限制） | 检查账户状态和配额 |
| 404 | `not_found_error` | 资源不存在（模型、文件） | 确认模型名称和资源ID |
| 408 | `timeout` | 请求超时 | 增加timeout或切至流式 |
| 409 | `conflict_error` | 资源冲突（如创建同名助手） | 使用已有资源或换名称 |
| 413 | `content_too_large` | 输入超过上下文窗口 | 缩短输入或启用 truncation |
| 422 | `unprocessable_entity` | 请求有效但无法处理（格式错误） | 检查字段约束 |
| 429 | `rate_limit_error` | 请求频率超限 | 等待后指数退避重试 |
| 429 | `tokens_per_minute_exceeded` | TPM超限 | 减少max_tokens或启用孙歇 |
| 429 | `context_window_exceeded` | 超出上下文窗口 | 启用truncation或拆分请求 |
| 403 | `insufficient_user_quota` | **模型提供商额度耗尽** | **立即切换到备用免费模型（如 deepseek/deepseek-v4-flash）；所有渠道同时掉线是典型症状，检查 gateway.error.log 是否有 403 quota 错误** |
| 500 | `server_error` | OpenAI服务端内部错误 | 等待后重试，不自行修复 |
| 503 | `service_unavailable` | 服务不可用（维护/过载） | 等待后重试，监控状态页 |

### B.2 重试策略

```
指数退避重试模板：
try:
    response = api.call()
except RateLimitError:
    for attempt in range(5):
        wait = 2 ** attempt + random.uniform(0, 1)
        time.sleep(wait)
        response = api.call()
except ServerError:
    # 5xx 只重试 3 次
    for attempt in range(3):
        wait = 2 ** attempt
        time.sleep(wait)
        response = api.call()
```

### B.3 本地模型（Ollama / LM Studio）常见错误

| 错误 | 含义 | 处理 |
|------|------|------|
| `connection refused` | Ollama服务未启动 | `ollama serve` 或检查端口 |
| `model not found` | 模型未拉取 | `ollama pull <model>` |
| `context length exceeded` | 上下文超限 | 减少输入或使用更长上下文的模型 |
| `GPU out of memory` | VRAM不足 | 减少并行请求、降低batch size |
| `slot is permanently unavailable` | 模型实例崩溃 | 重启Ollama服务 |

### B.4 费用控制

| 策略 | 操作 |
|------|------|
| 设置硬上限 | API Dashboard → Usage → Spending Limits |
| 监控实时用量 | 每次请求记录token消耗，累计报警 |
| 缓存复用 | 相同语义请求优先用缓存（`cache_control`） |
| 模型降级 | 非关键任务切换至更小模型 |

---

## Appendix C: 浏览器自动化错误分类

### C.1 Element 操作错误

| 错误类型 | 症状 | 根因 | 解决方案 |
|---------|------|------|---------|
| ElementNotFound | 定位符找不到元素 | 元素未渲染/定位符错误/跨帧 | 增加显式等待、用wait.until()、检查frame |
| StaleElementReference | 元素曾有效但已失效 | DOM重新渲染导致元素失效 | 重新查询元素，或在DOM变化后重新定位 |
| ElementIntercepted | 元素被遮挡无法点击 | 其他元素叠加（弹窗、广告） | 先关闭干扰元素再操作 |
| ElementReadOnly | 无法输入到只读字段 | readonly属性或disabled状态 | 确认字段是否可编辑 |
| ClickTargetAborted | 点击被中断 | 页面导航导致操作失效 | 等待页面稳定后再操作 |

### C.2 页面状态错误

| 错误类型 | 症状 | 根因 | 解决方案 |
|---------|------|------|---------|
| PageNotLoaded | 操作时页面未加载完成 | 异步渲染/网络慢 | wait for document.readyState === 'complete' |
| NavigationTimeout | 导航超时 | 重定向死循环/服务器无响应 | 增加timeout、检查网络请求 |
| FrameNotFound | 切换frame失败 | frame已删除或未加载 | 等待frame出现再切换 |
| CookieBlocked | Cookie操作失败 | 浏览器隐私设置阻止 | 检查浏览器隐私配置 |
| SSLHandshakeError | HTTPS连接失败 | 证书无效/自签名证书 | 在测试环境允许无效证书 |

### C.3 资源加载错误

| 错误类型 | 症状 | 根因 | 解决方案 |
|---------|------|------|---------|
| ResourceNotFound | 静态资源404 | 资源路径错误或构建问题 | 检查资源URL |
| ImageLoadFailed | 图片显示占位符 | 图片链接失效 | 检查图片URL有效性 |
| FontLoadFailed | 字体显示为宋体/等线 | 字体CDN不可用/跨域限制 | 配置字体CORS或fallback |
| ScriptLoadError | JS功能不工作（无报错） | JS文件加载失败 | 检查网络请求、配置fallback |
| CSSNotApplied | 样式错乱/无样式 | CSS加载阻塞/路径错误 | 检查CSS link标签 |

### C.4 权限与安全错误

| 错误类型 | 症状 | 根因 | 解决方案 |
|---------|------|------|---------|
| PermissionDenied | 无法读取剪贴板/摄像头等 | 权限未授予 | 用户授权或降级到不需要权限的方案 |
| CORSBlocked | 网络请求失败 | 跨域限制 | 配置CORS白名单或使用代理 |
| CSPViolation | 操作被浏览器拦截 | 内容安全策略阻止 | 调整CSP配置或改变实现方式 |
| SandboxBlocked | iframe内容无法访问 | X-Frame-Options禁止 | 使用服务端渲染替代iframe嵌入 |

### C.5 反自动化检测

| 错误类型 | 症状 | 根因 | 解决方案 |
|---------|------|------|---------|
| HumanVerificationRequired | 出现验证码/CAPTCHA | 行为被识别为机器人 | 减慢操作节奏、使用真实UA、IP轮换 |
| SessionExpired | 登录后立即要求重新登录 | 检测到自动化工具 | 使用真实浏览器profile |
| BlockedIP | 访问被拒绝 | IP被标记/频率限制 | 等待或使用代理IP |

---

## Appendix D: 工具超时处理策略

### D.1 超时分类与应对

| 超时类型 | 典型场景 | 根因 | 策略 |
|---------|---------|------|------|
| **网络超时** | HTTP请求未在预期时间内返回 | 网络抖动/服务器过载 | 指数退避重试1-3次 |
| **连接超时** | TCP握手未完成 | DNS故障/防火墙阻击 | 检查网络路径，确认端口可达 |
| **读取超时** | 数据传输中断 | 大文件传输慢/连接不稳定 | 增加timeout或分片传输 |
| **数据库超时** | 查询长时间无响应 | 慢查询/锁等待/连接池耗尽 | 优化查询或扩大连接池 |
| **浏览器超时** | 页面操作超时 | 元素加载慢/JS执行阻塞 | 使用显式等待而非固定sleep |
| **进程超时** | 子进程长时间未返回 | 进程死锁/死循环 | 设置进程最大运行时间，强制终止 |

### D.2 分层超时设计

```
推荐的超时配置模式：

HTTP 请求层：
  connect_timeout:  5s   （连接建立）
  read_timeout:    30s   （读取响应）
  total_timeout:   60s   （整体限制）

浏览器自动化层：
  page_load_timeout:  30s  （页面加载）
  script_timeout:     20s  （JS执行）
  implicit_wait:      5s   （元素隐式查找）

数据库层：
  query_timeout:   10s   （单次查询）
  connection_timeout: 5s  （获取连接）
  idle_timeout:    300s  （空闲连接回收）

重试策略：
  max_retries: 3
  backoff_base: 2s
  backoff_max: 60s
  jitter: ±0.5s
```

### D.3 渐进式超时

```
不要：对所有操作使用相同的固定超时。

应该：使用渐进式超时，让系统有时间自我恢复。

示例（Playwright）：
await page.goto(url, {
    timeout: 30000,          // 初始导航 30s
    waitUntil: 'domcontentloaded'  // 先等DOM，再等资源
})

// 元素操作使用更短超时
await page.locator('#button').click({ timeout: 5000 })  // 5s

// 配合显式等待
await page.locator('#result').waitFor({ state: 'visible', timeout: 10000 })
```

### D.4 超时后的恢复流程

```
当操作超时时：

1. 记录超时上下文
   - 超时发生在哪个操作
   - 当前页面状态（URL、关键元素）
   - 已消耗的时间

2. 判断是否可以重试
   - 幂等操作（GET、DELETE）→ 可以重试
   - 非幂等操作（POST、PUT）→ 检查是否已执行

3. 重试前恢复现场
   - 刷新页面重新进入流程
   - 清理已填充的表单状态

4. 降级处理
   - 多次超时后切换备用方案
   - 降级到手动处理流程
   - 发送告警等待人工介入
```

---

## Appendix E: 错误日志自动聚合

### E.1 日志聚合架构

```
原始日志流
    │
    ▼
[结构化日志层]  ← JSON格式，强制包含以下字段
    - timestamp    ISO8601 时间戳
    - level       DEBUG/INFO/WARN/ERROR/CRITICAL
    - service     服务名
    - trace_id    调用链ID
    - message     消息模板（不含变量）
    - metadata    键值对（error_code, user_id, duration_ms...）
    - error       错误详情对象（type, message, stack_trace）
    │
    ▼
[聚合工具层]
    - grep/ripgrep     即时搜索
    - loguru           Python结构化日志
    - pino             Node.js结构化日志
    - Loki + Grafana   时序聚合
    - ELK Stack        全文搜索 + 可视化
    │
    ▼
[聚合视图]
    - 按 error_type 聚合：同类错误出现次数
    - 按 trace_id 聚合：一请求内所有日志
    - 按 time 聚合：错误频率随时间变化
    - 按 service 聚合：多服务依赖链追踪
```

### E.2 标准日志格式（JSON）

```json
{
  "timestamp": "2026-05-17T16:00:00.000Z",
  "level": "ERROR",
  "service": "hermes-agent",
  "trace_id": "8f14e45f-ceea-46d5-9189-4e7c3d4e5f6a",
  "span_id": "a1b2c3d4",
  "message": "LLM API request failed",
  "metadata": {
    "provider": "openai",
    "model": "gpt-4o",
    "duration_ms": 30000,
    "retry_count": 3
  },
  "error": {
    "type": "RateLimitError",
    "code": 429,
    "message": "tokens_per_minute_exceeded",
    "stack_trace": "..." 
  }
}
```

### E.3 快速聚合命令集

| 场景 | 命令 |
|------|------|
| 按错误类型聚合计数 | `grep '"level": "ERROR"' app.log \| jq -r '.error.type' \| sort \| uniq -c \| sort -rn` |
| 最近N条错误 | `grep '"level": "ERROR"' app.log \| tail -100` |
| 特定trace_id所有日志 | `grep '"trace_id": "8f14e45f"' app.log \| jq -s 'sort_by(.timestamp)'` |
| 错误频率随时间变化 | `grep '"level": "ERROR"' app.log \| jq -r '.timestamp[0:16]' \| sort \| uniq -c` |
| 高频错误top10 | `grep '"level": "ERROR"' app.log \| jq -r '.message' \| sort \| uniq -c \| sort -rn \| head -10` |
| 特定用户所有错误 | `grep '"user_id": "u123"' app.log \| grep '"level": "ERROR"'` |
| 错误堆栈提取 | `grep '"level": "ERROR"' app.log \| jq -r '.error.stack_trace' 2>/dev/null` |
| 某时间段内错误 | `grep '"timestamp": "2026-05-17T1[4-5]' app.log \| grep '"level": "ERROR"'` |

### E.4 自动告警规则

```
基于错误日志聚合的告警配置（Prometheus Alertmanager / Grafana 风格）：

groups:
- name: hermes-errors
  rules:
  - alert: HighErrorRate
    expr: |
      sum(rate(log_messages{level="ERROR"}[5m]))
      / sum(rate(log_messages[5m])) > 0.05
    for: 5m
    annotations:
      summary: "错误率超过5%"

  - alert: CriticalErrorBurst
    expr: |
      sum(increase(log_messages{level="ERROR"}[1m])) > 50
    for: 1m
    annotations:
      summary: "1分钟内50+错误"

  - alert: SameErrorRepeated
    expr: |
      topk(5, count by (error_type, message) (log_messages{level="ERROR"}))
    annotations:
      summary: "高频相同错误，可能存在未修复bug"

  - alert: LatencySpike
    expr: |
      histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 5
    annotations:
      summary: "P99延迟超过5秒"
```

### E.5 根因聚合工作流

```
当收到大量错误告警时，用以下步骤聚合：

Step 1: 提取所有错误指纹
  按 error.type + message（前50字符）聚合
  → 识别是单一根因还是多个独立问题

Step 2: 按 trace_id 分组
  同一 trace_id 的错误属于同一请求上下文
  → 定位具体是哪个请求链路出错

Step 3: 按时间窗口切片
  错误集中在哪个时间段？
  → 判断是否与部署、配置变更相关

Step 4: 关联上下文
  错误发生前的最后一条INFO/WARN是什么？
  → 找到触发错误的前置事件

Step 5: 合并同因错误
  同一个根因可能触发多种表象错误
  → 找到根因后，标记所有相关错误为已解决
```
