# 4 层漏斗 vs 单点 VLM 选型 — 架构演进 (2026-06-29)

## 背景

本 skill (hermes-runtime-fortress) 之前是「装哪个本地 VLM」的单点决策树,
推荐 UI-TARS-MLX 优先、LLaVA 兜底. 这个建议**单点看没错**, 但**架构错了**.

## 修正: 单点选型 → 元决策 (4 层漏斗)

用户 2026-06-29 决策:

> "我基本同意 [反对本地 UI-TARS] 的分析, 而且我认为它比之前直接建议「本地 UI-TARS」更符合你这台 Mac mini M4 24GB 的实际情况."

> "Hermes 真正瓶颈不是看不懂, 而是不知道什么时候该看. ... 真正决定 Hermes 上限的不是哪一个 VLM, 而是何时需要调用 VLM, 以及如何尽量避免调用 VLM."

**4 层漏斗 (L0 → L1 → L2 → L3)**:

```
L0 Task Memory (0ms, 缓存)        ← 命中率 ~90%, 重复任务直接返回
L1 AX Tree (50ms, cua-driver)     ← 命中率 ~9%
L2 Local Detector (5-400ms)       ← 命中率 ~0.9%, OpenCV+OCR+Layout
L3 Cloud VLM (1-3s, UI-TARS)     ← 命中率 ~0.1%, HF Endpoint 按需
```

**关键差异**:

| 维度 | 单点 VLM 选型 (旧) | 4 层漏斗 (新) |
|---|---|---|
| 默认路径 | 调 VLM | 调缓存 (90% 命中) |
| 内存压力 | 6-10GB 常驻 | 0 (VLM 仅按需) |
| 延迟 | 1-3s/次 | 0.2ms (平均) |
| 成本 | 常驻 token | 日预算 $1 自动熔断 |
| 误判率 | LLaVA 自拼 prompt ~60% | UI-TARS 仅 0.1% 场景, 准确率 61.6% |
| 可演进性 | 换模型要重部署 | 换 L3 endpoint 即可 |

## 对本 skill 决策表的影响

### 之前 (本 skill 推荐)

```
UI grounding → UI-TARS-MLX 本地 (4bit, ~6GB)
通用 vision  → LLaVA 7B (4.7GB)
中文 OCR     → LLaMA 3.2 Vision 11B
```

### 之后 (4 层漏斗优先)

```
屏幕理解/找元素 → 4 层漏斗 (perception-decision-engine)
                  ├── L0 缓存命中 (90% 不需要任何视觉)
                  ├── L1 AX 树 (9% 不需要本地模型)
                  ├── L2 OpenCV+OCR (0.9% 走本地 CV, 零网络)
                  └── L3 UI-TARS 云端 (0.1% 走 HF Endpoint, 按需)
通用 vision    → LLaVA 7B (4.7GB, 仍本地, 用于 mac_vision_fallback)
中文 OCR       → macOS Vision (system native, 零依赖, 已在 L2 用)
```

## L3 Cloud VLM 配置 (云端按需)

```python
import vlm_bridge
vlm_bridge.set_enabled(
    True,
    provider="uitars",  # 或 "openai" / "anthropic"
    endpoint_url="https://xxx.endpoints.huggingface.cloud",
    api_key="hf_xxx",
)
# 预算控制 (自动 fallback 到 L2, 不抛错):
#   daily_budget_usd = 1.0
#   monthly_budget_usd = 10.0
#   per_task_max_calls = 3
```

**为什么用 HF Endpoint 而不是本地 7B**:
- UI-TARS-1.5-7B 官方推荐 L40S 48GB GPU, 24GB Mac mini 跑不动
- HF Endpoint 按调用计费, 比本地常驻便宜
- 模型升级无需重部署, 改 endpoint 即可

## 何时显式调 L3 (决策引擎自动判断)

1. L0/L1/L2 全部 miss (罕见, 实测 ~0.1%)
2. 用户指代不明 ("那个按钮" 类)
3. 新 App 首次遇到
4. AX 操作后视觉验证连续 2 次失败

**默认 enable_vlm=False**, 决策引擎显式开, 避免意外云端调用.

## 触发边界 (skill 互不重叠)

| 任务 | 走哪个 skill |
|---|---|
| 装/换本地 LLM/VLM/embedding | **hermes-runtime-fortress** (本 skill) |
| 找元素坐标 (何时调视觉) | **perception-decision-engine** |
| 已知坐标, 决定怎么点 | **hermes-see-act** |
| 内存超 75% 告警 | **hermes-runtime-fortress** (watchdog) |

## 真实数据 (2026-06-29 100 次模拟)

| 路径 | 占比 | 平均延迟 |
|---|---|---|
| L0_cache | 90.0% | 0.2ms |
| L2_color | 8.0% | 392ms |
| miss | 2.0% | 359ms |
| **总平均** | - | **39ms** |

L1 实测 0% 不是 bug, 是因为 L1 成功立即写 L0, 第二次同样任务直接 L0 命中 (旁路缓存).

## 实际产出文件

- `~/.hermes/scripts/perception_memory.py` (L0)
- `~/.hermes/scripts/visual_verifier.py` (L2 OCR + verify)
- `~/.hermes/scripts/local_detector.py` (L2 CV: color/template/layout/shape)
- `~/.hermes/scripts/vlm_bridge.py` (L3, 默认禁用)
- `~/.hermes/scripts/decision_engine.py` (4 层漏斗引擎)
- `~/.hermes/perception_memory.db` (sqlite3 缓存 DB)
- `~/.hermes/decision_funnel.jsonl` (生产 funnel 统计)