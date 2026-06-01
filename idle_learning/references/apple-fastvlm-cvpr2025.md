# Apple FastVLM — CVPR 2025

**标题**: FastVLM: Efficient Vision Encoding for Vision Language Models
**来源**: Apple Machine Learning Research (machinelearning.apple.com/research/fast-vision-language-models)
**发表**: CVPR 2025 (July 23, 2025), updated September 22, 2025

## 核心创新

- **FastViTHD**: 混合架构视觉编码器（卷积 + transformer 多阶段），专为高分辨率图像设计
- 减少视觉 token 数量同时保持高质量，无需复杂的 token pruning/merging
- 简单 MLP 投影层连接视觉编码器和 LLM

## 模型规模

| 规模 | 说明 |
|------|------|
| 0.5B | 小模型，适合极端轻量场景 |
| 1.5B | 主流配置，与 LLM 平衡 |
| 7B | 高精度场景 |

## 关键性能对比

- 比 LLaVA-OneVision (0.5B) **快 85x**
- 比 SmolVLM (~0.5B) **快 5.2x**
- 比 Cambrian-1 (7B) **快 21x**
- FastViT 比 ViT-L/14 快 **20x**、小 **8x**

## 可用性

- HuggingFace 已发布 MLX 和 CoreML 格式 checkpoint
- iOS/macOS 演示 App 基于 MLX
- 浏览器 demo（transformers.js + WebGPU）
- **非 Ollama 格式** — 需 MLX-Python 或 CoreML 运行

## 产线评估

- ✅ 苹果官方、CVPR 顶会、Apple Silicon 原生优化
- ❌ 非 Ollama 兼容，需额外推理框架
- ❌ 未针对 scene classification 任务训练/测试
- **当前结论**: 记录备查，不拉取。若未来产线迁移到 MLX 推理层可重新评估。

## 页面结构备忘（JS 提取）

Apple ML Research 页面结构特殊，`document.querySelector('main')` 返回 null。
正确提取方式：
```javascript
Array.from(document.querySelectorAll('p, h2, h3, h4, li'))
  .map(el => el.innerText)
  .filter(t => t.trim())
  .join('\n')
```
