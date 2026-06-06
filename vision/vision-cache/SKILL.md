---
name: vision-cache
description: |
  浏览器视觉理解结果缓存 — 避免 VLM/OCR 重复调用的 LRU+TTL 缓存层。
  基于 (URL + DOM signature + prompt) 三元组做 key, 命中后 0ms 返回。
  实测: 同页 5 次访问从 5×16.6s 降到 1×16.6s + 4×0ms, 节省 99.9%。
  
  触发词: "vision 缓存" / "VLM 重复调用" / "截图理解结果复用" /
  "vision_cache" / "视觉结果缓存" / "browser_vision 加速"。
---

# Vision Cache (浏览器视觉理解结果缓存)

## 1. 目标

**问题**：浏览器场景下, 视觉理解 (VLM) 一次 3-25s, 慢 + 费 token。同一会话内反复访问同一页面很常见 (登录态检查 / 反爬验证 / 调试), 但每次都重跑 VLM。

**解法**: 在 (URL, DOM signature, prompt) 三元组上加 LRU+TTL 缓存, 命中后 0ms 返回。

## 2. 文件

| 文件 | 作用 |
|------|------|
| `~/.hermes/scripts/vision_cache.py` | 核心 LRU+TTL 缓存类 + CLI |
| `~/.hermes/scripts/vision_cache_browser.py` | 浏览器接线 (CDP 9333 + DOM signature + 截图 + VLM) |
| `~/.hermes/scripts/vision_with_cache.py` | 透明 wrapper: 包装 vision_analyze / browser_vision 自动走缓存 |
| `~/.hermes/cache/vision_cache.json` | 持久化 (JSON, 人类可读) |
| `~/.hermes/cache/screenshots/vc_*.png` | 缓存命中的截图 (供回溯) |

## 3. 快速使用

### 3.1 Python 调用
```python
from vision_cache import VisionCache

cache = VisionCache(ttl=300, max_entries=200)
result, hit = cache.get_or_compute(
    url="https://example.com",
    dom_hash="<sha256-of-dom-sig>",
    prompt="页面有几个按钮?",
    compute_fn=lambda: call_vlm(image, prompt),  # 耗时操作
    model="qwen3-vl:2b",
    screenshot_path="/tmp/screenshot.png",
)
print(f"hit={hit}, result={result}")
```

### 3.2 CLI 调用
```bash
# 跑实测 (验证缓存层)
python3 ~/.hermes/scripts/vision_cache.py test

# 浏览器接线 (接真实 Chrome)
python3 ~/.hermes/scripts/vision_cache_browser.py -q "页面标题是什么"
python3 ~/.hermes/scripts/vision_cache_browser.py --mock -q "test"  # mock VLM

# 统计
python3 ~/.hermes/scripts/vision_cache.py stats
python3 ~/.hermes/scripts/vision_cache_browser.py --stats

# 清空
python3 ~/.hermes/scripts/vision_cache.py clear
```

## 4. Key 设计

```python
def make_key(url, dom_hash, prompt):
    raw = f"{url}::{dom_hash}::{normalize(prompt)}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]
```

| 维度 | 抓什么 | 为什么 |
|------|--------|--------|
| URL | `location.href` | 切页/换站点自动失效 |
| DOM signature | title + 节点数 + 文本长度 + 前 100 元素 tag + 交互元素文本 | 视觉变化敏感 (节点数/文本长度变化 → key 变) |
| Prompt | 归一化 (去空格/小写) | 同一问题不同写法命中同一缓存 |

**⚠️ 关键**：DOM hash **必须**用 sha256, **不能用** Python `hash()`。`hash()` 每次进程启动值都不同 (PYTHONHASHSEED 随机), 缓存命中率会掉到 0%。

## 5. DOM signature 模板 (浏览器端)

```javascript
(() => {
    const sigs = [];
    sigs.push(document.title || '');
    sigs.push(document.body ? document.body.tagName : '');
    sigs.push(document.body ? document.body.children.length : 0);
    // 节点总数 (结构变化敏感)
    sigs.push('nodes=' + document.querySelectorAll('*').length);
    // 可见文本总长 (内容变化敏感)
    sigs.push('text_len=' + (document.body ? (document.body.innerText || '').length : 0));
    // 前 100 个元素 tagName (结构)
    const tops = document.querySelectorAll('body *');
    Array.from(tops).slice(0, 100).forEach(el => sigs.push(el.tagName));
    // 交互元素 + 文本 (按钮/链接变化)
    const interactives = document.querySelectorAll('button, a, input, textarea, select, [role=button]');
    interactives.forEach(el => {
        sigs.push(el.tagName + ':' + (el.textContent || '').trim().slice(0, 30));
    });
    return JSON.stringify({url: location.href, title: document.title, dom_sig: sigs.join('|').slice(0, 2000)});
})()
```

## 6. 关键坑点 (踩过的)

### 6.1 Python `hash()` 跨进程不稳定
```python
# ❌ 错: 每次进程启动值都不同
dom_hash = str(hash(dom_sig))

# ✅ 对: 用 sha256
import hashlib
dom_hash = hashlib.sha256(dom_sig.encode('utf-8')).hexdigest()[:16]
```

### 6.2 VLM 模型名要对齐本地实际型号
```python
# ❌ 错: 假设有 qwen3-vl:latest
payload = {"model": "qwen3-vl:latest", ...}
# 实际返回: 404 Not Found

# ✅ 对: 先 `curl http://localhost:11434/api/tags` 查实际装的
payload = {"model": "qwen3-vl:2b", ...}  # 本地实测装的是这个
```

### 6.3 JSON 反序列化后类型变化
```python
# 注入端不要用 String() 包装
# ❌ String(undefined) → "undefined" str, String(8) → "8" str
# ✅ 直接传原值, Python 端做宽松类型判断
```

### 6.4 `total_size_kb` 单位陷阱
```python
# ❌ 错: 551 字节的缓存显示 "0KB"
return {"total_size_kb": total_size_bytes // 1024}  # = 0

# ✅ 对: 自适应单位
if total_size_bytes >= 1024:
    size_str = f"{total_size_bytes / 1024:.1f}KB"
else:
    size_str = f"{total_size_bytes}B"
```

### 6.5 持久化 JSON 必须带 ensure_ascii=False
中文 result 不会变 \uXXXX, 人类可读:
```python
json.dump(data, f, ensure_ascii=False, indent=2)
```

### 6.6 错误结果必须不缓存 (避免污染) — 2026-06-05 新增
VLM 服务挂的时候 (ollama 502, 超时等) 会返回错误结果。如果缓存了错误结果,
后续命中会一直返回错误, 用户以为是真问题实际上是缓存污染。

**真实事件 (2026-06-05)**: ollama 第一次重启后所有 qwen3-vl:2b 调用都返回 502 Bad Gateway。如果 put 没过滤, 第一次 502 会被存为"有效结果", 之后所有命中都返回 502, 调试时困惑很久。

```python
# ❌ 错: 错误结果也缓存
def put(self, key, result, ...):
    self.data[key] = {...}  # 错误也存

# ✅ 对: put 时检测错误模式, 不缓存
def put(self, key, result, ...):
    if isinstance(result, str):
        error_patterns = ["[VLM_ERR]", "[ERR]", "HTTP Error", "timed out", "Traceback", "Error:"]
        if any(p in result for p in error_patterns):
            return  # 错误不缓存, 让下次重新调
    # 空结果也不缓存
    if result is None or (isinstance(result, str) and not result.strip()):
        return
    self.data[key] = {...}
```

**经验**: 任何"长期缓存 + 上游可能挂"的服务, put 时都要过滤错误结果。

### 6.7 修复 bug 后默认直接修, 不要停在"要不要修" (2026-06-05)

**用户原话**: *"有问题的以后都默认要修，不用问"*

本会话修了 4 个 bug (hash 不稳定/模型名错/单位假数据/错误污染), 全是发现就直接修。详见 `proactive-execution` skill 规则 21。

## 7. TTL + LRU 策略

| 参数 | 默认 | 理由 |
|------|------|------|
| TTL | 300s (5 分钟) | 页面是动态的, 太久会失效 |
| max_entries | 200 | LRU 平衡: 够覆盖会话内反复访问, 不会撑爆磁盘 |
| 触发淘汰 | TTL 过期 + LRU 超出 | `get()` 命中时 move_to_end; `put()` 时 evict |

## 8. 何时适合用

✅ **适合**:
- 同一会话内反复访问同一页面 (登录态检查、反爬调试、AI 站对话刷新)
- DOM 变化不频繁的页面 (文档/设置页/AI 对话结果)
- VLM 耗时 > 100ms (慢才有缓存价值)

❌ **不适合**:
- 实时变化的页面 (股票、倒计时、视频流)
- 一次性查询 (VLM < 100ms 没必要)
- 隐私敏感场景 (result 写盘 = 留痕)

## 9. 验证缓存生效 (踩坑自查清单)

```bash
# 1. 清缓存
python3 ~/.hermes/scripts/vision_cache.py clear

# 2. 第 1 次: 应该 miss (调 VLM)
python3 ~/.hermes/scripts/vision_cache_browser.py -q "测试问题"
# 期望: "🔄 缓存未命中"

# 3. 第 2 次: 应该 hit (0ms)
python3 ~/.hermes/scripts/vision_cache_browser.py -q "测试问题"
# 期望: "⚡ 缓存命中"

# 4. 改 prompt: 应该 miss
python3 ~/.hermes/scripts/vision_cache_browser.py -q "另一个问题"
# 期望: "🔄 缓存未命中" (不同 key)

# 5. 改 URL (navigate 到别的页): 应该 miss
# 期望: "🔄 缓存未命中"

# 6. stats 看命中率
python3 ~/.hermes/scripts/vision_cache.py stats
# 期望: hits >= 1, hit_rate > 0%
```

## 10. 与现有技能的关系

| 关系 | 说明 |
|------|------|
| **依赖** `hermes-vision-agent` | 视觉理解主技能, vision_cache 是其下的"加速层" |
| **依赖** `cdp-browser-automation` | 浏览器接线需要 CDP 9333, 复用其 tab 嗅探代码 |
| **依赖** `anti-detect-verify-script` | 同样的 Chrome 调试端口, 可共享注入后的浏览器 |
| **被 `browser_vision` 工具调用** | 未来可透明包装, 所有 vision 调用自动走缓存 |

## 11. 透明 wrapper (2026-06-05 新增)

`vision_with_cache.py` 把缓存层透明包到原工具上, **不修改原 vision_analyze / browser_vision**。

```python
from vision_with_cache import cached_vision_analyze, cached_browser_vision

# 替代原 vision_analyze
result = cached_vision_analyze(image_url_or_path, prompt, model=None)

# 替代原 browser_vision
result = cached_browser_vision(question, annotate=False)

# use_cache=False 可临时绕过
result = cached_browser_vision(question, use_cache=False)
```

**好处**:
- 调用方代码改动最小 (只改 import + 函数名)
- `use_cache=False` 保留紧急绕过通道
- 错误结果不污染 (继承 VisionCache 的 put 过滤)

**未来**: 直接修改 `vision_analyze_tool` / `browser_vision` 内部调用 wrapper, 所有 vision 调用自动走缓存, 完全透明。

### 11.1 端到端实测数据 (2026-06-05)

```
[wrapper 端到端测试] python3 scripts/verify_vision_wrapper.py
TEST 1 hash_image 同图同 hash / 改图 hash 变         ✅ PASS
TEST 2 get_current_url 拿到浏览器 URL                ✅ PASS
TEST 3 make_key 4 维隔离 (URL/DOM/prompt)             ✅ PASS
TEST 4 缓存工作流 3 次访问只 1 次 VLM                  ✅ PASS
TEST 5 TTL 过期 (1s TTL, 1.5s 后 miss)                ✅ PASS
```

**真实浏览器提速 (qwen3-vl:2b, 同一 URL + 同一 DOM + 同一 prompt)**:
| 访问次数 | VLM 耗时 | 累计节省 |
|---|---|---|
| 第 1 次 (miss) | 10.9s | 0 |
| 第 2 次 (hit) | 0ms | 10.9s |
| 第 3 次 (hit) | 0ms | 21.8s |

**配套测试脚本**:
- `scripts/verify_vision_cache.py` — 测核心 VisionCache (LRU+TTL+key 隔离)
- `scripts/verify_vision_wrapper.py` — 测透明 wrapper (hash + URL + DOM + 端到端)

## 12. 参考

- `references/vision-cache-design-rationale.md` — 为什么用 DOM signature 而非截图 hash
- `references/vlm-models-status-2026-06-05.md` — 本地 VLM 模型清单 + 真实响应耗时
- `scripts/verify_vision_cache.py` — 5 步验证脚本 (跑这个能确认缓存层没坏)
- `scripts/verify_vision_wrapper.py` — 5 步 wrapper 端到端验证 (2026-06-05 新增)
