# InsiderLLM M4 Mac 2026 Guide（2026-05-31 实测）

来源：insiderllm.com/guides/best-local-llms-mac-2026/（2026-05 更新）

## M4 24GB（Hermes Mac mini）关键结论

**官方推荐**："The 14B tier and the low edge of the Qwen 3.6-27B zone"

### Qwen 3.6 系列（2026-04-02 发布，Apache 2.0）
- **Qwen 3.6-27B dense**（~17GB Q4_K_M）—"tight but doable"，vision **内建于基座**（首个无独立VL分支的Qwen），262K 上下文
- **Qwen 3.6-35B-A3B MoE**（~22GB）— 3B active/token，Mac 32GB+ 推荐，token 速度接近 3B 模型
- ⚠️ Ollama 是否支持 Qwen 3.6 **待验证**（github.blocked）

### Gemma 4 系列（2026-04-02 发布）
- **Gemma 4 26B-A4B**（MoE，4B active，256K 上下文）— 32-48GB Mac 推荐
- **Gemma 4 E2B/E4B** — 8-16GB Mac 推荐，边缘设备优化

### Memory Bandwidth 对推理速度的影响
| Chip | Bandwidth | Relative Speed |
|------|-----------|----------------|
| M4 base | ~150 GB/s | 1x |
| M4 Pro | ~273 GB/s | 2-2.5x |
| M4 Max | ~400+ GB/s | 3-5x |

**结论**：M4 24GB = M4 Pro 核芯，~273 GB/s。推理瓶颈是 memory bandwidth，不是 FLOPS。

## Vision 模型选择参考

**当前 Hermes 现状**：
- smolvlm2-agentic-gui（61.71%，1.85GB）— 已消失 3 次，疑似 Ollama 自动清理
- qwen3-vl:2b（已装但 60s+ 超时）— 不适合实时 screen_watcher
- qwen3-vl:8b — 估计 15s，可能可用，但未测试

**待验证候选**：
1. Qwen 3.6-27B dense — vision 内建于基座，M4 24GB "tight but doable"
2. Holo1.5-3B（91.7%，~3GB）— Ollama pull 失败，需 GGUF 导入
3. Gemma 4 视觉变体 — 多模态版本在 Ollama 可用

## 已知 Ollama Bug
- qwen35moe mmproj bug（#14575）— Qwen 3.5 MoE + 独立 vision projector 报错
