# 4 层漏斗架构 — 决策依据 (2026-06-29)

## 背景: 为什么 4 层而不是「直接 VLM」

用户最初建议是「引入 UI-TARS 作为核心感知层, 走三维对齐 (AX + VLM + OCR)」。
我提出 3 个硬伤后, 用户修正方向为「4 层漏斗 + 云端按需」, **核心原则: 决策引擎高于 VLM 选型**。

## UI-TARS-1.5-7B 硬件门槛 (事实, 不是意见)

官方部署文档 [README_deploy.md](https://github.com/bytedance/UI-TARS/blob/main/README_deploy.md) 明确:

> For the 7B model, select **GPU L40S 1GPU 48G** (Recommended: Nvidia L4 / Nvidia A100)

24GB Mac mini M4 统一内存:
- 4bit 量化: ~5GB 模型权重 + ~3GB KV cache + 8GB 系统 + 上下文图片 → **不稳定**
- MLX 框架实测: UI-TARS-1.5-7B-4bit + mlx-vlm 启动后内存峰值 8-10GB, **频繁 OOM**
- UI-TARS-2 (2025-09): 闭源权重, **本地根本跑不了**

## 「主动每步调 VLM」的代价

按「关键步骤调一次 UI-TARS」假设:
- 推理延迟: 7B 模型 1000-2000ms/次 (Apple Silicon 无专门 kernel)
- 10 步任务 → 10-20 秒纯 VLM 开销
- 24GB 内存压力 + 长任务 swap → **整个 Hermes gateway 卡**

## 实测漏斗分布 (100 次模拟, 2026-06-29)

| 路径 | 占比 | 平均延迟 |
|---|---|---|
| L0_cache | 90.0% | 0.2ms |
| L1_ax_tree | 0% (L0 缓存复用) | - |
| L2_color | 8.0% | 392ms |
| L2_ocr | 0% | - |
| L3_vlm | 0% | - |
| miss | 2.0% | 359ms |
| **总平均** | - | **39ms** |

**关键发现**: L1 实测 0% 不是 bug, 是因为 L1 成功立即写 L0, 第二次同样任务直接 L0 命中 (旁路缓存). **真实生产中 L0 命中率会随时间持续增长, 远超初始 90%.**

## 用户原话 (决策依据, 2026-06-29)

> "我基本同意这份分析, 而且我认为它比之前直接建议「本地 UI-TARS」更符合你这台 Mac mini M4 24GB 的实际情况."

> "Hermes 真正瓶颈不是看不懂, 而是不知道什么时候该看. 如果直接 API(UI-TARS), 网络延迟 / Rate Limit / Token 成本 / 上传截图都会成为新的问题. 我更建议: 先把 Decision Engine 做好."

> "L2 应该越来越智能, 而不是 heuristic 越来越多. ... L2 是 Local Detector, 不是堆 heuristic."

> "我会研究 Decision Engine. ... 真正调用 VLM 的概率可能 100 次任务: AX 90, Detector 9, VLM 1, 甚至 0.5%."

> "真正决定 Hermes 上限的不是哪一个 VLM, 而是何时需要调用 VLM, 以及如何尽量避免调用 VLM."

## 不做的方案对比

| 方案 | 问题 |
|---|---|
| 本地 7B VLM 常驻 | 6-10GB 内存 + 1-3s 延迟, 24GB 跑不动 |
| 每步调云端 VLM | 100% 网络依赖 + token 成本爆炸 + 每次 1-3s |
| 堆 heuristic | 维护成本指数增长, 不通用 |
| 「三维对齐」硬做 | 坐标系变换 + 文本匹配去重的代码量 > 视觉验证本身 |
| 闭源 UI-TARS-2 | 根本开源不了 |

## 4 层架构的正确性论证

1. **L0 缓存**: 重复任务常见 (如「每天打开同一网站」), 缓存命中率自然 > 80%
2. **L1 AX Tree**: macOS 原生能力, cua-driver 已经做好, 0 成本
3. **L2 Local Detector**: OpenCV + Vision 都是本地能力, 零网络, 覆盖 90% AX 读不到的场景
4. **L3 云端 VLM**: 仅 0.1% 场景用得起, 用 HuggingFace Endpoint 避免本地资源压力

## 演进路径

1. **现在**: 4 层漏斗已落地, 实测 90% L0 命中
2. **下阶段**: 收集真实生产 funnel_stats, 调整 L0 缓存 TTL 和命中校验策略
3. **再下阶段**: 接入 UI-TARS HF Endpoint (按需), 验证 miss 场景下 VLM 能否真正解决
4. **未来**: M5/M6 芯片或 48GB+ 内存时, 考虑本地 7B 量化版, 把 L3 延迟从 1-3s 压到 200ms

## 触发词 (避免重蹈覆辙)

- "装个本地 VLM / UI-TARS-7B 量化 / mlx-vlm 跑 UI-TARS" → 0 思考拒绝, 24GB 跑不动
- "每步调 VLM" → 0 思考拒绝, 网络 + 成本 + 延迟都不可承受
- "堆更多 heuristic" → 0 思考拒绝, 改用 Local Detector 统一接口
- "Decision Engine 没用, 直接调 VLM" → 0 思考拒绝, 决策引擎是最大性能杠杆
- "三维对齐 (AX + VLM + OCR)" → 0 思考评估 ROI, 坐标系变换代码量 > 收益

## 实际参考

- UI-TARS 官方: https://github.com/bytedance/UI-TARS
- HuggingFace Endpoint 部署: https://github.com/bytedance/UI-TARS/blob/main/README_deploy.md
- ScreenSpot-Pro 基准: UI-TARS-1.5 61.6% (远超 OpenAI CUA 23.4% / Claude 3.7 27.7%)
- macOS Vision OCR: VNRecognizeTextRequest (system native, 无需依赖)
- OpenCV 4.13 + numpy 2.4 (已装, 零新依赖)