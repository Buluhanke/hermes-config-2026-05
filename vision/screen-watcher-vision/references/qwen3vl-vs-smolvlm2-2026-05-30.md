# Qwen3-VL vs SmolVLM2 对比测试（2026-05-30）

## 实测数据

| 指标 | smolvlm2-agentic-gui | qwen3-vl:2b |
|------|---------------------|-------------|
| 模型 | ahmadwaqar/smolvlm2-agentic-gui | qwen3-vl:2b |
| 大小 | 1.85GB (Q4_K_M) | 1.76GB |
| 响应时间 | **7.7s** | **46.6s**（900x900缩图）|
| 输入分辨率 | 原生1920x1080 ✅ | 需缩到900x900 ❌ |
| 锁屏OCR | 基本 | ✅ 识别"5月30日周六"、"登入"等中文 |
| GUI专项 | ✅ 是 | ❌ 否（通用视觉模型）|
| 适用场景 | screen_watcher实时分析 | 离线精确OCR |

## qwen3-vl:2b Ollama 已知限制

1. **原生1920x1080截图超时**：Ollama API 调用超过60s cron限制
2. **必须预处理缩图**：需要 `sips -z 900 900` 缩到900x900
3. **即使缩图仍慢**：900x900仍需46.6s，远慢于smolvlm2的7.7s
4. **速度瓶颈本质**：VLM推理本身慢，非图片尺寸问题

## 结论

- **screen_watcher 实时分析**：继续用 smolvlm2-agentic-gui（速度快，原生分辨率）
- **离线OCR场景**：可考虑 qwen3-vl:2b（需缩图预处理）
- **qwen3-vl:4b（3.3GB）**：90% ScreenSpot，若能解决速度问题可替代 smolvlm2，待实测