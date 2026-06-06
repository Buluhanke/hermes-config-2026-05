# 本地 VLM 模型状态（2026-06-05 实测）

## 已装模型

```bash
$ curl -s http://localhost:11434/api/tags | python3 -c "import json,sys; print([m['name'] for m in json.loads(sys.stdin.read())['models']])"
['moondream:latest', 'qwen2.5:1.5b', 'qwen3-vl:2b']
```

| 模型 | 大小 | 视觉 | 中文 | 实测耗时 | 推荐场景 |
|------|------|------|------|----------|----------|
| **qwen3-vl:2b** | ~2GB | ✅ | ✅ 原生 | 16.6s (首次), 3.7s (二次) | 中文界面理解 |
| moondream:latest | ~1GB | ✅ | ⚠️ 英文为主 | ~1s | 英文简单图 |
| qwen2.5:1.5b | ~1GB | ❌ 纯文本 | ✅ | ~0.3s | 文本生成 |

**注意**: `qwen3-vl:latest` 这个 tag **不存在**, 别用。要用 `qwen3-vl:2b`。

## 实测耗时（2026-06-05 browserleaks.com/javascript 截图）

| 任务 | 首次 (模型冷启动) | 二次 (模型已加载) |
|------|------------------|------------------|
| 简单识别 (URL/Title) | 16.6s | 3.7s |
| 复杂理解 (页有几个测试项) | 60s+ timeout | 未测 |

**首次慢的根因**: Ollama 第一次调用要把模型从磁盘加载到内存 + MPS 编译。

## 远程 VLM（备选）

| 服务 | 视觉 | 中文 | 备注 |
|------|------|------|------|
| Gemini API | ✅ | ✅ | 需要 key, 跨境不稳 |
| Claude API | ✅ | ✅ | 需要 key, 付费 |
| ChatGPT API | ✅ | ✅ | 需要 key, 付费 |

**当前默认**: 本地 qwen3-vl:2b, 不上云 (省 token + 隐私)

## 已知问题

### 1. 复杂任务超时
qwen3-vl:2b 对"页面有几个测试项"这种需要数数的问题会超过 60s, 默认 timeout 失败。
**对策**: cache hit 后用之前的结果, 不重复调。

### 2. 中文 prompt 有时输出英文
qwen3-vl:2b 中文 prompt 偶尔输出英文回答。
**对策**: prompt 加 "请用中文回答" 后缀, 或缓存后人工校对。

### 3. 截图尺寸影响
`Page.captureScreenshot` 默认 1280×720 (viewport)。长截图 `captureBeyondViewport: true` 会更大, 推理更慢。
**对策**: 默认 viewport 截图, 不开 captureBeyondViewport。

## 切换模型方法

```python
# vision_cache_browser.py 里改一行
payload = {"model": "qwen3-vl:2b", ...}  # 改这个
```

## 升级路径

| 升级 | 何时 | 怎么升 |
|------|------|--------|
| 换 qwen3-vl:7b | 2b 不够用时 | `ollama pull qwen3-vl:7b`, 改 `vision_cache_browser.py` 模型名 |
| 远程兜底 | 本地全挂时 | 加 `call_vlm_remote()` 函数, 走 Gemini API |
| 多模型路由 | 不同问题用不同模型 | 在 `get_or_compute` 里按 prompt 长度/类型路由 |
