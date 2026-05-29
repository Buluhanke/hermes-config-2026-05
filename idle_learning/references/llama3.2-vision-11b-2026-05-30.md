# llama3.2-vision:11b 评估 (2026-05-30)

## benchmark 数据来源
- InsiderLLM (insiderllm.com/guides/vision-models-locally/)
- Codersera Blogs (Qwen3-VL vs llama3.2-vision 对比)

## 核心结论
- **ScreenSpot: ~79%**（Qwen3-VL 8B 达 94%，差距 ~15pp）
- Meta 出品，~8GB，Mac M4 24GB 可运行
- 社区支持强，但 benchmark 几乎所有任务输给 Qwen2.5-VL 7B
- 通用视觉理解强（captioning/image reasoning），非 GUI 专用

## 本地模型状态 (2026-05-30 实测)
```
Total models: 4
  - qwen2.5:1.5b (0.92 GB)
  - qwen3-vl:2b (1.76 GB)
  - nomic-embed-text:latest (0.26 GB)
  - ahmadwaqar/smolvlm2-agentic-gui:latest (1.85 GB)
```
llama3.2-vision:11b 未安装。

## 决策：不安装
理由：
1. benchmark 输给现有 qwen3-vl:2b（通用视觉）约 15pp ScreenSpot
2. GUI 场景不如 smolvlm2-agentic-gui（61.71%，专用）
3. 如需升级，优先级：qwen3-vl:4b > GGUF导入 Holo1.5-3B > llama3.2-vision:11b

## 下次学习方向
执行层 — screen_watcher 完整链路验证（screen_watcher 进程状态 + dry-run 日志）