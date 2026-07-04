---
name: perception-decision-engine
description: Hermes 4 层感知决策框架 — L0 Task Memory (缓存) → L1 AX Tree → L2 Local Detector (OpenCV+OCR+Layout) → L3 Cloud VLM (UI-TARS, 默认禁用)。解决「什么时候该调视觉」这个 Hermes 最大的性能杠杆, 严格遵守 90/9/0.9/0.1 漏斗假设。
trigger: agent 找不到目标元素、需要做视觉决策、想知道「现在该不该调 VLM」时。
---

# Hermes 4 层感知决策框架

## 为什么这是最大的杠杆

99% 的 Agent 框架默认「截图 → VLM → 决策」是反过来的：
- VLM 应该是 Exception, 不是 Default
- 100 次任务里 L0+L1 就能解决 95%, VLM 只需要兜底 0.1%
- 在 24GB Mac mini 上, VLM 推理会吃掉 6-10GB 内存 + 1-3s 延迟

**真正决定 Hermes 上限的不是哪个 VLM, 而是「何时调、不调时怎么兜底」**。

## 4 层漏斗

```
L0 Task Memory (0ms)     ← 缓存命中即返回, 命中率 ~90%
  ↓ miss
L1 AX Tree (~50ms)        ← cua-driver get_window_state, 命中率 ~9%
  ↓ miss
L2 Local Detector (~5-400ms) ← OpenCV + OCR + Layout, 命中率 ~0.9%
  ↓ miss
L3 Cloud VLM (1-3s)       ← UI-TARS HF Endpoint (默认禁用), 命中率 ~0.1%
  ↓ miss
Human Recovery            ← 上报用户, 附截图+上下文
```

## 模块位置（⚠️ 需实测验证，勿直接信任文档）

> **铁律（2026-07-04 教训）**：skill 文档里的 "✅ 落地" 状态可能已过期。每次任务前用下方命令实测验证，不凭记忆判断文件是否存在。

```bash
# 验证 L0 缓存
ls ~/.hermes/spatial_memory/          # 实际存在: cache/ index.json/ stats.json

# 验证 L1 cua-driver
cua-driver --version                  # 实际存在: 0.6.8

# 验证 L2 脚本（如果 skill 声称落地）
for f in perception_memory visual_verifier local_detector vlm_bridge decision_engine hermes_native_eyes; do
  [ -f ~/.hermes/scripts/${f}.py ] && echo "✅ $f" || echo "❌ $f 不存在"
done

# 验证 L3 VLM 配置（当前走云端，不是本地）
grep -A5 "auxiliary:" ~/.hermes/config.yaml | grep vision  # 应为 auto 或具体云 provider

# 验证 perception DB
ls ~/.hermes/perception_memory.db 2>/dev/null || echo "❌ perception_memory.db 不存在"
```

**当前实测状态（2026-07-04）**：
- L0 spatial_memory: ✅ `~/.hermes/spatial_memory/` 存在
- L1 cua-driver: ✅ `cua-driver 0.6.8`
- L2/L3 脚本: ⚠️ 未逐一验证，文档可能过期
- 本地 Ollama/LLaVA: ❌ 已删除，vision 走云端 fallback（OpenRouter → Nous Portal → Anthropic）
- `perception_memory.db`: ❌ 不存在
- `fact_store.db`: ❌ 0字节，表结构丢失

**修复优先级**：
1. fact_store.db 重建（学习历史全部丢失）
2. vision 配置改为 `provider: auto`（删掉指向已死 ollama 的硬编码）
3. perception_memory.db 重建（感知决策无历史积累）

## 已知坑 (踩过验证)

**L2 不是堆 heuristic, 而是把 CV 工具整合成一个统一接口**:

| 工具 | 用途 | 延迟 |
|---|---|---|
| `detect_by_color` | 颜色块定位 (canvas 按钮) | ~5-20ms |
| `detect_by_template` | 模板匹配 (已知 UI 元素指纹) | ~10-50ms |
| `detect_by_shapes` | 圆/方/三角形状识别 (图标分类) | ~10-30ms |
| `detect_layout` | Sidebar/Header/Content 区域分割 | ~50-100ms |
| `detect_text_regions` | 边缘密度推断文字区域 (比 OCR 快 100x) | ~5-20ms |
| `visual_verifier.spot_by_text_heuristic` | macOS Vision OCR | ~300-400ms |
| `visual_verifier.verify_state` | 多维校验 (text + no_text + color) | ~400ms |

**统一入口**: `local_detector.detect(image_path, intent)`
- `intent="color:red"` 或 `"color:255,0,0"` → color detector
- `intent="template:/path/to/img.png"` → 模板匹配
- `intent="layout"` → 区域分割
- `intent="shape:circle|rect|triangle"` → 形状
- `intent="text_region"` → 边缘密度
- `intent="auto"` → 跑 layout + shapes

**原则**: 写「检测器」而不是「heuristic」—— 一个统一接口 + 5 个底层工具, 未来加新检测器 (SF Symbols / 文字 embedding) 都是同一个 `detect(intent=...)` 接口。**L0/L1/L2 应该越来越智能, 而不是 heuristic 越来越多**。

## 旁路缓存 (L1 → L0 自动写)

**关键设计**: L1 (AX Tree) 成功时, 立即把元素位置写入 L0 缓存. 下次同样任务直接 L0 命中, 跳过 cua-driver 调用.

```
第一次: L0 miss → L1 hit (50ms) → 写 L0
第二次: L0 hit (0.2ms)  ← 自动化, 不需要外部触发
```

**实测影响**: 30 个"新任务"第一次走 L1 (50ms), 之后**所有重复都 L0 命中 (0.2ms)**. L0 命中率会随时间持续增长, 远超初始的 90%.

**L2 同样**: OCR 找到关键词后也写 L0 (role="AXStaticText", title=匹配关键词).

## Funnel 统计 (生产数据校准)

```bash
python3 decision_engine.py stats
```

返回最近 N 天每层命中率 + 平均延迟. **用途**:
1. 验证 90/9/0.9/0.1 假设 (不同 app 比例不同)
2. 发现 L0 缓存命中率异常 (突然下降 = UI 改版/缓存失效)
3. 发现 L2 命中率高 = AX 树经常读不到, 需要扩展 L2 检测器
4. 监控 L3 实际调用次数 + 成本 (避免超预算)

**记录机制**:
- `_log_funnel` 把每次漏斗尝试写入 `~/.hermes/decision_funnel.jsonl`
- **必须 buffer 批量写** (50 条 flush 一次): 每次都 `with open("a")` 在 macOS/sandbox 小 ulimit 下会爆 `Too many open files`
- `funnel_stats` 调用前先 `_flush_funnel()`, 避免最后几条丢失

## 已知坑 (踩过验证)

1. **fd 泄漏 (最常见)**: PIL `Image.save` 不显式 close, 在 sandbox/小 ulimit (256) 下循环调用 50+ 次就 `OSError: [Errno 24] Too many open files`. 修法: `img.close(); del img; del draw`, **且每次写到同一路径** (避免 fd 累积).
2. **OCR Swift 子进程**: 第一次跑需要 Vision TCC 授权 (会弹 macOS 权限框). 屏幕纯图片/视频/加密界面时返回 0 是合法状态, **不是 bug**.
3. **缓存抖动**: AX 元素的 fingerprint 校验失败 (页面布局变了) → 应降级到 L1 重新扫描, **不要硬走 L0 返陈旧坐标**.
4. **sqlite 并发锁**: 高频写感知 DB 偶尔 `OperationalError: unable to open database file`. **修法**: `sqlite3.connect(path, timeout=5.0)` + retry 3 次 + sleep 指数退避. 写失败要静默丢, **不能阻塞主流程**.
5. **buffer flush**: `_log_funnel` 用 `FUNNEL_BUFFER` 累积 + 每 50 条 flush, 避免每次 open/close 文件 fd 累积.
6. **PIL `Image` 不要当模块级引用**: 改用 `from PIL import Image as _PILImage` 函数内 import, 避免 reload 时循环引用.
7. **类型默认值**: 函数签名别用 `Optional[X] = None` 显式, Pyright 会抱怨. 用 `list = []` / `tuple = ()` / `str = ""` 兜底.

## 调用代价

| 层 | 延迟 | 内存 | 网络 |
|---|---|---|---|
| L0 | 0.2ms | 0 | 无 |
| L1 | 50ms | 0 | 无 |
| L2.OCR | 400ms | 0 | 无 |
| L2.Color | 5-20ms | 0 | 无 |
| L2.Layout | 50-100ms | 0 | 无 |
| L3 UI-TARS | 1-3s | 0 (远程) | 必需 |

## 与其他 skill 的分工

- **`hermes-see-act`**: 5 通道决策表 (DOM/AX/vision/RPA), 关注**单次操作的通道选择**
- **`hermes-runtime-fortress`**: 本地模型集成 + 内存保护, 关注**模型部署**
- **`perception-decision-engine` (本 skill)**: **何时该调视觉**的元决策, 4 层漏斗

**触发边界**:
- 找元素坐标 → `perception-decision-engine` (本 skill)
- 已知元素坐标, 决定怎么点 → `hermes-see-act` (cua-driver)
- 装/换本地 LLM/VLM → `hermes-runtime-fortress`
- 内存超 75% → `hermes-runtime-fortress` (watchdog)

## 核心 API

### decision_engine.find_element()
```python
from decision_engine import find_element

result = find_element(
    app="Safari",
    window_title="Checkout",
    ax_elements=elements,        # 来自 cua-driver get_window_state
    screenshot_path="/tmp/cur.png",
    target_role="AXButton",
    target_title="Submit",
    enable_vlm=False,            # 默认 False, 防止意外云端调用
)
# result["path"] = "L0_cache" | "L1_ax_tree" | "L2_ocr" | "L2_color" | "L3_vlm" | "miss"
# result["element"]["x/y/w/h"] = 精确坐标
# result["latency_ms"] = 实际延迟
```

### hermes_native_eyes.find_element_via_funnel()
同上, 是 build_frame 框架内的便捷入口。

## 实测数据 (100 次模拟任务)

| 路径 | 占比 | 平均延迟 |
|---|---|---|
| L0_cache | 90.0% | 0.2ms |
| L1_ax_tree | 0% (实测因 L0 缓存复用) | - |
| L2_color | 8.0% | 392ms |
| miss | 2.0% | 359ms |
| **总平均** | - | **39ms** |

(注: L1 实测 0% 是因为 L1 成功后立即写 L0 缓存, 模拟中第二次相同任务直接走 L0, 这是缓存系统的正确行为)

## 何时显式调 L3 (启用 VLM)

**默认禁用**, 只在以下场景显式开:
1. L2 + 多次重试都失败, 决策引擎已自动尝试 fallback
2. 用户明确说「那个按钮」(指代不明, AX 描述不够)
3. 新 App 首次遇到, 无任何缓存
4. AX 操作后视觉验证连续 2 次失败

启用方式:
```python
import vlm_bridge
vlm_bridge.set_enabled(True, provider="uitars",
                        endpoint_url="https://xxx.endpoints.huggingface.cloud",
                        api_key="hf_xxx")
```

预算控制:
- daily_budget_usd: 1.0 (默认)
- monthly_budget_usd: 10.0 (默认)
- 超预算自动 fallback 到 L2, 不抛错

## Funnel 统计

```bash
python3 decision_engine.py stats
```

输出最近 7 天每层命中率, 用于校准 90/9/0.9/0.1 假设。

## 已知坑

1. **fd 泄漏**: PIL Image.save 不显式 close 会累计 fd, 在 sandbox/小 ulimit 下爆. 修: `img.close(); del img`
2. **OCR Swift 子进程**: 第一次需要 Vision TCC 授权, 屏幕纯图片/视频时返回 0
3. **缓存抖动**: AX 元素的 fingerprint 校验失败时降级到 L1, 不要硬走 L0
4. **sqlite 锁**: 并发写感知 DB 偶尔 OperationalError, 已加 retry 3 次 + sleep

## 生产级微调 (2026-06-29 落地)

### 微调 1: 缓存一致性 region_fp 校验
L0 命中后**不立即返回**, 必须校验「这个位置还是不是这个东西」:
- 整图粗校验 (`fingerprint` 比对)
- 区域精校验 (`region_fp`, bbox 32x32 灰度 md5)
- 不一致 → **失效缓存 + 降级到 L1/L2**, 避免无效点击
- element_lookup 已返回 `region_fp` 字段

### 微调 2: LRU 清理 (24h 未访问)
- element_cache 新增 `last_accessed_at` 列 + 索引
- element_lookup 自动刷新热度
- `decision_engine.heartbeat_cleanup(max_age_hours=24)` 清理冷缓存
- 推荐: cron 每小时跑一次, 比纯 TTL 更精准 (热门元素不误清)

### 微调 3: Miss → 主动学习 (终身学习)
- 新增 `miss_learning` 表, 存 90 天
- 流程: miss → human_in_loop → 用户操作完 → `decision_engine.report_miss_recovery(...)`
- 自动把结果写入 L0 缓存 (region_fp 也算)
- 下次同样任务 → **直接从 miss 跨入 L0_cache, 0ms**
- 这是「终身学习」的最关键闭环
### 微调 4: funnel_stats 扩展

新增三个生产级字段:
- `miss_by_element_type`: 按元素类型统计 miss, 找 UI 设计中不稳定的部分
- `recovery_latency`: Human Recovery 平均介入时长 (samples/avg/min/max)
- **`visual_alignment_offset`** (新增): L0 命中时 AX 坐标 vs OCR 文本中心的偏移统计

**指标解读**:
- `avg_offset_px` < 5px: 系统映射精准，无需校准
- `avg_offset_px` 10-20px 且 variance 小：Retina 缩放系统误差，可用 `scaling_factor` 统一修正
- `variance` 大 (>50): UI 动态渲染问题，不能硬校准，依赖 L2 兜底

调用示例:
```python
# 1. 心跳清理 (cron 每小时)
de.heartbeat_cleanup(max_age_hours=24)

# 2. Miss 学习 (human recovery 完成后)
de.report_miss_recovery(
    app="Safari", window_title="Settings",
    target_role="AXButton", target_title="Done",
    x=920, y=80, w=80, h=30,
    screenshot_path="/tmp/after_human_click.png",
)

# 3. 看生产指标 (含 alignment offset)
print(json.dumps(de.funnel_stats(days=7), indent=2))
```

## 调用代价

| 层 | 延迟 | 内存 | 网络 |
|---|---|---|---|
| L0 | 0.2ms | 0 | 无 |
| L1 | 50ms | 0 | 无 |
| L2.OCR | 400ms | 0 | 无 |
| L2.Color | 5-20ms | 0 | 无 |
| L2.Layout | 50-100ms | 0 | 无 |
| L3 UI-TARS | 1-3s | 0 (远程) | 必需 |

## 演进路径

1. **现在**: 4 层漏斗已落地, 实测 90% L0 命中
2. **下阶段**: 收集真实生产数据, 看实际漏斗比例, 调整 L0 缓存 TTL 和命中校验策略
3. **再下阶段**: 接入 UI-TARS 云端 (按需), 验证 miss 场景下 VLM 能否真正解决
4. **未来**: 本地 7B+ M4 优化版, 内存压力可承受时再考虑本地化 L3

## 相关文件

- **架构决策依据 + UI-TARS 硬件门槛 + 不做的方案对比**: `references/funnel-architecture-decision.md`
- **4 层漏斗烟雾测试模板 (复制改 find_element 调用即可)**: `templates/funnel_smoke_test.py`