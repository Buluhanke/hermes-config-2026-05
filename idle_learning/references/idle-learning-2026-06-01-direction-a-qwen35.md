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

### 推荐替换路径
- **P1 推荐**: `ollama pull qwen3.5:2b-q4_K_M` (1.81GB) → 直接替换 qwen3-vl:2b (1.76GB)
  - 几乎相同内存占用，next-gen 视觉能力
  - 还可替换 qwen2.5:1.5b（Qwen3.5 是通用多模态，scene classification + 文本推理可单模型完成）
  - 总内存: 2.68GB → 1.81GB，节省 0.87GB
- **P2 推荐**: `ollama pull qwen3.5:4b-q4_K_M` (3.39GB) → 更强但多占 1.63GB
- 当前内存状态: 仅 11% 占用 (qwen3-vl:2b 1.76GB + qwen2.5:1.5b 0.92GB = 2.68GB / 24GB)
- 空间充裕，升级后 ~14%，完全可接受

### 来源
- Ollama library: ollama.com/library/qwen3.5
- Ollama registry manifests: registry.ollama.ai/v2/library/qwen3.5/manifests/4b-q4_K_M
- InsiderLLM May 2026 update: insiderllm.com/guides/best-local-llms-mac-2026

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
