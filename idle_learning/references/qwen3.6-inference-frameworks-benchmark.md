# Qwen3.6 推理框架基准测试（2026-05-30 学习）

来源：[Qwen 3.6 27B on 24GB VRAM: Benchmarking llama.cpp, ik_llama.cpp, BeeLlama, vLLM](https://dasroot.net/posts/2026/05/qwen-3-6-27b-24gb-vram-benchmarking-llama-cpp-ik-llama-cpp-beellama-vllm/)，2026-05-21

测试环境：A100 80GB（12GB allocated），Intel Xeon E5-2698 v4 (20c/40t)，Ubuntu 22.04 LTS，框架版本：llama.cpp v0.8.2 / ik_llama.cpp v0.7.1 / BeeLlama v1.1.0 / vLLM v0.5.4

## 吞吐量横评（Qwen3.6-35B-A3B MoE，~3B 活跃参数）

| 框架 | 吞吐量 | 核心优化点 |
|------|--------|-----------|
| llama.cpp | **80 tok/s** | 基线，简单兼容性好 |
| ik_llama.cpp | **110 tok/s** | 内存管理优化，减少碎片提升缓存利用率 |
| BeeLlama | **145 tok/s** | 多线程并行处理，适合多 GPU/多核场景 |
| vLLM | **190 tok/s** | MTP（Multi-Token Prediction）投机解码 |

> vLLM 最高，vLLM + MTP 投机解码比 llama.cpp 基线快 **2.4x**。

## Qwen3.6-35B-A3B MoE 在 24GB 显卡（RTX 4090，Q4 量化）

社区报告约 **120 tok/s**（RTX 4090）。

## 关键洞察：Memory Bandwidth 是瓶颈

低 batch decode 算术强度极低（FP16 约 1 FLOP/byte），推理瓶颈是 **memory bandwidth**，不是 FLOPS。

## Hermes 执行层影响

- smolvlm2 响应 5-11s 是 memory bandwidth 限制的正常表现
- 50,000 tokens 生成：100 tok/s ≈ 8 分钟，3,000 tok/s ≈ 17 秒
- auto_execute 大量 reasoning token 生成时，decode 速度直接决定响应延迟
- "智能 × 迭代速度"：生产力边界从"只拼智能"转向"智能 × 迭代速度"

## Ollama 的位置

Ollama 封装了 llama.cpp，当前不支持 MTP 投机解码。如需 vLLM 级别的 MTP 加速，需直接部署 vLLM 或等待 Ollama 支持。

## 相关链接

- [Kog AI 推理引擎](https://cloudnews.tech/kog-ai-drives-a-revolution-in-inference-with-amd-mi300x-up-to-3-5-times-faster-than-current-engines/)：3,000 tok/s per request（8×AMD MI300X），瓶颈分析同义
- [Kog AI 官网](https://www.kog.ai/)