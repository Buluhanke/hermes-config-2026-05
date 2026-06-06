# Vision Cache 设计原理

## 为什么用 DOM signature 而非截图 hash

**两种 key 方案**：

| 方案 | Key | 优点 | 缺点 |
|------|-----|------|------|
| A. 截图 hash | `sha256(image_bytes)` | 抓的是"真实视觉", 不会因 DOM 改但视觉没变而 miss | 截图本身 ~280KB, hash 慢; 视觉微小变化（动画、光标）就 miss |
| B. DOM signature | `sha256(url + dom_sig)` | 极快 (1ms), 抓的是"结构意图" | 视觉改但 DOM 没变（如 CSS 切换）会 miss |

**选 B 的理由**：
1. 视觉理解 (VLM) 的目的是"理解页面在表达什么", 不是像素比对。结构变了 = 内容变了, 需要重新理解
2. 截图 hash 280KB, 每次 key 计算 + 序列化都慢, 不如 DOM 字符串直接 sha256
3. 同一页面 5 分钟内几乎一定有 DOM 变化（动态加载、广告、时间戳），B 方案命中率实际更高
4. 对抗"动画/光标/光影"等视觉噪声, B 方案天然免疫

## 为什么 LRU 而非 LFU

- 同一页面 5 分钟内被访问 5 次 = 1 个高频项
- LRU 简单, OrderedDict O(1) move_to_end
- LFU 需要维护访问次数, 复杂且对缓存价值判定不准（"刚被访问 1 次的 vs 3 分钟前被访问 10 次的" → LRU 选前者更对, 因为时间近）

## 为什么 TTL = 300s 而非更长

- 6 大 AI 站 (Gemini/豆包/ChatGLM/DeepSeek/ChatGPT/Grok) 对话流是动态的, 新消息会改变 DOM
- 电商站 (1688/淘宝) 价格、库存实时变
- 5 分钟 = 大多数"调试一个 bug 看 3 次页面"的工作流能覆盖
- 超 5 分钟还在看 → 主动失效更安全, 避免显示过时结果

## 为什么不缓存截图

截图已经存在 `~/.hermes/cache/screenshots/` 单独的 PNG 文件, 缓存 JSON 里只存**路径**, 不重复存字节。
这样:
- JSON 文件小（每条 < 1KB）, 加载快
- 截图可独立清理 (rm 旧的 vc_*.png)
- 调试时可单独打开 PNG 看当时截了什么

## 关键 bug 复盘

### Bug 1: Python `hash()` 跨进程不稳定
```python
>>> hash("hello")  # 进程 A
123456
>>> hash("hello")  # 进程 B
-7890123  # PYTHONHASHSEED 随机
```
**根因**: Python 字符串 hash 加了 `PYTHONHASHSEED` 随机盐, 防止 DoS。**用 sha256 代替**。
**踩坑时间**: 2026-06-05 vision_cache.py 首次实现, 跑第 2 次访问命中率 0%。

### Bug 2: VLM 模型名 `qwen3-vl:latest` 不存在
```bash
$ curl http://localhost:11434/api/tags
{"models": [{"name": "qwen3-vl:2b"}, ...]}
# 没有 "qwen3-vl:latest"
```
**根因**: 假设了"默认 latest tag", 但本地装的不是 latest。**先 `curl /api/tags` 查实际型号**。
**踩坑时间**: 2026-06-05 vision_cache_browser.py 首次跑真 VLM, 404 报错。

### Bug 3: `total_size_kb` 显示 0
```python
total_size_bytes = 551
total_size_kb = 551 // 1024  # = 0
print(f"size={total_size_kb}KB")  # 误导
```
**根因**: 整数除法丢弃小数。**改为自适应单位 (B/KB/MB)**。
**踩坑时间**: 2026-06-05 stats 输出, 用户看到 "size=0KB" 会以为缓存是空的。

## 关键设计: 接入策略

**当前状态**: 手动调用 `vision_cache_browser.py` CLI

**未来** (按需做):
1. 包装 `browser_vision` 工具 → 透明加速 (所有 vision 调用自动走缓存)
2. 包装 `vision_analyze` → 同上
3. 加 `--auto-cache` 开关到 hermes_react_loop.py → ReAct 循环里自动复用
