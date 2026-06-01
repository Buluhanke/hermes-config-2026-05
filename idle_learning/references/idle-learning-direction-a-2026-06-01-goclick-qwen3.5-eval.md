# Direction A: Vision Model Evaluation — 2026-06-01

## Session Context

Cron-triggered idle_learning Direction A巡检。当前产线稳定运行中。

## Key Findings

### 1. Qwen3.5 系列确认已在 Ollama 完全可用

Ollama Library (ollama.com/library/qwen3.5) 确认全部 variant 可用：
- `qwen3.5:0.8b` → 1.0 GB (Text+Image)
- `qwen3.5:2b` → 2.7 GB (Text+Image) — 可替代 qwen3-vl:2b + qwen2.5:1.5b (当前 2.68GB 总和)
- `qwen3.5:4b` → 3.4 GB (Text+Image) — 升级候选
- Early fusion 训练策略：多模态 token 在基座模型层面直接融合

**Decision: NOT pulling.** 当前产线 0% unknown + YOLO 双分类器稳定运行，变动风险 > 潜在收益。
Qwen3.5 2B/4B 变体无 GUI 专项基准发布，升级收益不可量化。

### 2. 产线健康确认

- YOLO ScreenParser 双分类器正常部署运行 (07:25 起持续产出 [silent] 跳过)
  - `YOLO预分类: idle (1个UI元素)` → `YOLO判断空闲界面，跳过VLM分析 [silent]`
  - 93ms @ 320px CPU 推理
- qwen3-vl:2b 场景分类: June 1 00:07 后 unknown=0%
- June 1 场景分布: 99.6% "other", 0.2% "browser", 0.2% "desktop"
- Gateway hook 污染: 1928 (稳定，无增长)

### 3. GoClick 新论文发现 (arXiv:2604.23941, Apr 2026)

**Title**: GoClick: Lightweight Element Grounding Model for Autonomous GUI Interaction
**Authors**: Hongxin Li, Yuntao Chen, Zhaoxiang Zhang

**Key specs**:
- Only **230M parameters** (encoder-decoder architecture)
- Outperforms decoder-only VLMs at small scale for GUI grounding
- Progressive Data Refinement: 3.8M core set from 10.8M raw dataset
- Target: on-device execution (mobile/low-resource)

**Analysis for Hermes**:
- Grounding model (coordinate output), NOT scene classification — complementary to qwen3-vl:2b
- ~300-400MB estimated GGUF size → potentially 10-50x faster inference than qwen3-vl:2b
- Device-cloud collaboration framework: lightweight edge grounding + cloud planner
- **Status**: Pending verification (Ollama availability, GGUF format, Mac compatibility)
- **Next check**: Direction D evaluation

### 4. InsiderLLM May 2026 Guide Confirmation

Page: insiderllm.com/guides/best-local-llms-mac-2026
Updated: May 24, 2026

| RAM | Recommendation |
|-----|---------------|
| 8GB | Gemma 4 E2B or Qwen 3.5 4B |
| 16GB | Qwen 3.5 9B or Gemma 4 E4B |
| 24GB | Qwen 3.6-27B Q4 (16.8GB, "tight but doable") |
| 32-48GB | Qwen 3.6-35B-A3B MoE (3B active/token) |
| 48GB+ | Qwen 3.6-27B dense at Q6/Q8 (25.57 tok/s) |

**Key insight**: Qwen 3.6-27B at 16.8GB Q4 is too tight for M4 24GB vision work (only ~5GB left for OS + KV cache). Stick with qwen3-vl:2b + qwen2.5:1.5b.

### 5. Evaluation Methodology Refinement

**YOLO-stability-first rule** (new):
When performing Direction A model evaluation, BEFORE considering any model pull:
1. Check if YOLO ScreenParser pre-classifier is deployed (`grep "YOLO" ~/.hermes/logs/screen_trigger.log | tail -3`)
2. Check current unknown rate by date slice (not aggregate — aggregate includes historical contamination)
3. If YOLO deployed + unknown=0% (date-sliced) + stable scene classification → **skip model pull**
4. Only pull if: unknown > 5% (date-sliced) OR systematic hallucination detected OR YOLO pre-classifier shows degradation
