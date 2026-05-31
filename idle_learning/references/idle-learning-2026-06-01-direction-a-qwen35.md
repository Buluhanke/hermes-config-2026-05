# 2026-06-01 方向A学习：Qwen3.5 + LocateAnything-3B + OSU-NLP Paper Scan

## ⭐ Qwen3.5 — 次世代多模态模型（Ollama 已发布）

### 注册表实测大小

从 `registry.ollama.ai/v2/library/qwen3.5/manifests/` 获取的层大小（2026-06-01 curl 实测）：

| 变体 | 模型层大小 | M4 24GB |
|--------|-----------|---------|
| qwen3.5:0.8b-q8_0 | 0.96 GB | ✅ 轻量 |
| qwen3.5:2b-q4_K_M | 1.81 GB | ✅ 等价 qwen3-vl:2b |
| qwen3.5:2b-q8_0 | 2.55 GB | ✅ 更高精度 |
| qwen3.5:4b-q4_K_M | 3.39 GB | ✅ 升级候选 |
| qwen3.5:4b-q8_0 | 4.92 GB | ⚠️ 有压 |
| qwen3.5:9b-q4_K_M | ~6.6 GB | ❌ 太大 |

### 关键优势
- **Early Fusion 训练**：多模态 token 在基座模型层面直接融合（非独立 VL 分支如 qwen3-vl）
- "outperforms Qwen3-VL models across reasoning, coding, agents, and visual understanding benchmarks"（Qwen 官方 readme）
- 架构创新：Gated Delta Networks + sparse MoE
- RL scaled across million-agent environments
- 201 languages support
- Near-100% multimodal training efficiency

### 推荐替换路径（🔄 2026-06-01 06:00 更新 — 实测决策修正）

**⚠️ 结论：不拉取 qwen3.5:2b 或 qwen3.5:4b。**

初始分析认为替换有收益（next-gen 视觉、单模型替换两模型），但**生产实测证据**否决了此建议：

| 评估维度 | 旧假设 | 产线实测 |
|---------|--------|---------|
| qwen3-vl:2b unknown 率 | 未知基线 | **0.085%** (June 1, 0% after 00:07) |
| 场景分类精度 | 存疑 | 99.2% "other" 深夜分类完全正确 |
| 小模型 GUI 基准 | 假设 qwen3.5 更强 | **未发布** — 无 2B/4B 的 ScreenSpot/OSWorld 数据 |
| 内存节约 | 2.68GB → 1.81GB | 实测 qwen3.5:2b = 2.7GB（**+0.02GB**，Ollama default quant） |

**否决原因（四项）**：
1. **0% unknown 率不可替代**：当前 qwen3-vl:2b 是经过数日生产验证的最佳状态
2. **无小模型 GUI 基准**：所有 Qwen3.5 视觉基准数据来自 397B 云模型，2B/4B 的 GUI 专项表现未知
3. **理论收益换已知风险**：所有宣称优势基于架构变化（early fusion），非实测数据
4. **唤醒条件**：等 qwen3.5 小模型放出 ScreenSpot / OSWorld 基准后再重新评估

**替代思路**（若未来需升级）：
- 内存占用接近（2.68GB → 2.7GB），essentially swap-in replacement
- 一次 `ollama pull + handler 模型名修改` 即可完成
- 不需要改 prompt 或 context config（early fusion 兼容 chat API）

### 来源
- Ollama library: ollama.com/library/qwen3.5
- Ollama registry manifests: registry.ollama.ai/v2/library/qwen3.5/manifests/4b-q4_K_M
- InsiderLLM May 2026 update: insiderllm.com/guides/best-local-llms-mac-2026

### 🏆 外部验证信号（2026-06-01 06:00 发现）
Ollama 官方 library 页面将 **Hermes Agent** 列为 Qwen3.5 的 launchable 应用之一，与 Claude Code、Codex、OpenClaw、OpenCode 并列：
```
ollama launch hermes --model qwen3.5
```
这是 Ollama 对 Hermes 生态地位的公开认可。意义：
- Hermes 与 Claude Code / Codex 同级视为 AI Agent 平台
- 间接验证 SOUL/memory/skills triad 方向
- 可用于外部沟通（如用户问"Hermes 行不行"时的佐证）

## ⭐ Qwen3.6 — M4 24GB 不可用

| 变体 | 大小 | 结论 |
|--------|------|------|
| qwen3.6:27b-q4_K_M | ~16.8 GB | ❌ 仅剩 ~5GB 给系统和上下文 |
| qwen3.6:35b-a3b-q4_K_M | ~20 GB | ❌ 太大 |
| InsiderLLM 金句 | "On 24GB: Qwen 3.6-27B dense at Q4, tight but doable" | 适合编码不适合 vision 常驻 |

Qwen3.6 只适合纯推理工作，不适合 screen_watcher 场景（需要常驻视觉模型 + 文本模型）

## ⭐ LocateAnything-3B（NVIDIA）

- **HuggingFace**: `nvidia/LocateAnything-3B` — 580 likes (May 26-28 发布)
- **Ollama**: ❌ 不可用（nvidia-license，无 GGUF 发布）
- **架构**: Qwen2.5-3B-Instruct (2.5B LLM) + MoonViT-SO-400M (视觉编码器) ≈ 3.4B
- **并行 Box Decoding (PBD)**: 单步平行框解码替代逐 token 序列，2.5x throughput
- **训练数据**: 12M 图像, 138M+ queries, 785M 边界框
- **部署**: 仅 vLLM serve / SGLang / Transformers（不能用 Ollama）
- **对 Hermes**: 直接集成成本高（额外 vLLM 服务进程），Qwen3.5:4b 更优

## ⭐ OSU-NLP Paper List 扫描结果

来源: raw.githubusercontent.com/OSU-NLP-Group/GUI-Agents-Paper-List/main/papers.yaml

### 新发现的 Desktop + 框架论文（此前未记录）

| 论文 | arxiv | 要点 | Hermes 关联 |
|------|-------|------|-------------|
| VLAA-GUI | 2604.21375 | 77.5% OSWorld, Stop-Recover-Search | handler Verify 阶段 |
| UI-Voyager | 2603.24533 | 4B 81.0% AndroidWorld, 自失败进化 | dry-run → self-correction |
| AdaZoom-GUI | 2603.17441 | 指令重写+自适应缩放 grounding | handler second-pass |
| GPA | 2604.01676 | 训练无关，10x faster than Gemini 3 Pro | 纯视觉动作模板 |
| ClawGUI | 2604.11784 | 全栈框架，PRM+GiGPO，ClawGUI-2B | Verify 阶段的 PRM |
| ZoomUI | 2603.14448 | training-free 渐进式 grounding | other 场景细粒度分析 |
| HyMEM | 2603.10291 | 图结构记忆，7B/8B 匹配闭源 | memory 架构 |
| Visual Confused Deputy | 2603.14707 | 双通道 Guardrail | handler 否定检测升级 |
| CUAAudit | 2603.10577 | VLM-as-judge 审计 | handler 自我验证 |
| OS-Themis | 2603.19191 | 里程碑分解奖励模型 | DRY_RUN=False 验证机制 |

## ⭐ 产线健康快照（2026-06-01 07:00）
**注意：此快照为 07:00 轮次的数据。2026-06-01 06:00 轮次最新数据见下方 \`06:00 更新\` 分节。**

| 组件 | 状态 | 详情 |
|------|------|------|
| screen_watcher | ✅ | PID 8748, 1:27 AM 启动 |
| Ollama | ✅ | qwen3-vl:2b + qwen2.5:1.5b, runner 2.78GB |
| 截图新鲜度 | ✅ | current.png 04:56, 3.3MB |
| 场景分类 | ✅ | 99.2% "other"（深夜 idling） |
| unknown 率 | ✅ | 0.8%（仅 2 条，00:07 后 0%） |
| 否定检测 | ✅ | [silent] 正确标记 |
| AUTO-EXEC-DRY | ✅ | 853 条 |
| Gateway 污染 | ✅ | 1707，修复后停止增长 |
| 网络 | ✅ | github OK, hn blocked |
| Handler lock | ✅ | 无 |

### 🆕 2026-06-01 06:00 轮次更新

| 组件 | 更新值 |
|------|--------|
| AUTO-EXEC-DRY | 905（+52 自 07:00 快照） |
| Gateway 污染 | 1788（+81，缓慢增长，非功能性问题） |
| June 1 05:00-06:00 scene | 48 "other", 1 "desktop", 0 unknown ✅ |
| Ollama ps | qwen3-vl:2b loaded (2.7GB, 100% GPU, ctx 4096) |
| 网络 | github OK, hn blocked（不变） |
| Qwen3.5 决策 | ⛔ 不拉取（见上方更新） |

**配置修改**：无。产线 100% 稳定。
