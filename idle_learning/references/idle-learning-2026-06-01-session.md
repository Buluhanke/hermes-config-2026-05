# idle_learning 2026-06-01 Session — 方向 A（Vision 模型调研）

## 时间
2026-06-01 01:04

## 发现摘要

### 1. Fara-7B / Fara1.5 
- GitHub microsoft/fara: **5.3k stars**, 519 forks, 50 commits
- 基于 Qwen2.5-VL-7B，**仅 vLLM 部署**（非 Ollama），无 GGUF
- Fara1.5 agent harness "coming soon"（2026-05-21 公告），模型未发布
- WebVoyager 73.5%, WebTailBench 38.4% (7B SOTA)
- **结论**：M4 24GB 无法利用（vLLM 7B 内存不够，无 GGUF/Ollama 集成）

### 2. Cider SDK（Mininglamp，明略科技）
- W8A8/W4A8 激活量化，MLX 扩展，GitHub 317 stars
- **⚠️ M4 不兼容**：条件编译，INT8 TensorOps 仅 M5+ 构建
  - M4：`is_available() = False`，`convert_model()` 是 warning no-op
- M5 Pro Qwen3-VL-2B 基准（仅供参考）：
  - FP16 Prefill: 3010 tok/s, Decode: 70 tok/s
  - W8A8 Prefill: 3242 tok/s, Decode: 104 tok/s
- Qwen3-8B W8A8：Prefill 1.46x faster, 内存降低 40%
- **Cider 是 M5+ 专属优化，M4 24GB 不适用**

### 3. LFM2.5-8B-A1B（Liquid AI，MoE）
- Ollama: `ollama pull maternion/lfm2.5`（模型页：ollama.com/maternion/lfm2.5）
- MoE: 8.3B total / **1.5B active**，文本模型（无视觉），131K 上下文
- 适合替换 qwen2.5:1.5b 做 agentic reasoning
- 有 MLX 格式可用

### 4. 24GB Backend Shootout（InsiderLLM，2026-05-22）
- ik_llama.cpp: **22s**（1.66x vs llama.cpp 37s）
- BeeLlama: **23s**（1.62x）
- Reddit r/24gb 验证：ik_llama + Qwen3.6-27B-MTP-IQ4_KS.gguf 是 24GB 最佳组合
- **Hermes 启示**：若需替换 Ollama backend 提高推理速度，ik_llama 是首选

### 5. Qwen 3.6 Q4 Quant 风险（InsiderLLM）
- Q4 量化破坏 coding agent 的工具调用和长任务稳定性
- Q4→Q6 是部分修复
- **教训**：agentic 工作负载量化不低于 Q6

### 6. Bonsai Image 4B（PrismML）
- 1-bit diffusion transformer: 0.93GB（8.3x < FLUX.2 Klein 4B）
- 88-95% FLUX 质量
- Image Generation only — Hermes vision pipeline 无交集

### 7. HN Top 10（2026-06-01）
| 排名 | 分数 | 标题 | 相关度 |
|------|------|------|--------|
| 1 | 352pts | The Website Specification | 已覆盖过 |
| 2 | 292pts | Dav2d | 视频编解码 |
| 3 | 240pts | AI subscription cancellation | 低 |
| 4 | 201pts | London's Free Roof Terraces | 低 |
| 5 | 196pts | Cloudflare Turnstile WebGL | 已覆盖过 |
| 6 | 81pts | Bonsai Image 4B | 低（image gen）|
| 7 | 57pts | Restartable Sequences | 低 |
| 8 | 25pts | Odysseus AI workspace | 低 |
| 9 | 20pts | Chibil .NET IL compiler | 低 |
| 10 | 9pts | Speed of Prototyping | 低 |

## 产线巡检快照

| 组件 | 状态 |
|------|------|
| screen_watcher | ✅ PID 3339 |
| screen_trigger_handler | ✅ PID 5884 |
| screenshot freshness | ✅ 01:03 持续更新 |
| dry-run logs | 636条，持续增长 |
| scene=other marking | ✅ [silent]（否定检测生效） |
| Ollama runner | ✅ qwen3-vl:2b loaded |
| github network | ✅ ok |
| hn network | ❌ blocked |

## 下次方向
B — 看懂内容（VLM benchmark 更新 + GUI understanding research）
