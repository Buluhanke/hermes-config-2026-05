# LocateAnything-3B（Nvidia，2026-05 发布）

## 基本信息
- **模型**：`nvidia/LocateAnything-3B`
- **来源**：Nvidia LABs, arxiv 2605.27365v1
- **发布**：4天前（2026-05 末）
- **平台**：HuggingFace（https://huggingface.co/nvidia/LocateAnything-3B）

## 核心能力
- Fast and High-Quality Vision-Language Grounding
- 精确目标定位（object localization）
- 密集检测（dense detection）
- 基于点的定位（point-based）

## GUI Grounding 基准
- 在 GUI grounding 任务上表现优异
- 论文 Table 3 展示 ScreenSpot-Pro 结果
- 来源文章：`pub.towardsai.net/nvidia-drops-a-model-locateanything-e0c50de7326d`

## 与 Hermes 关系
- ⚠️ github.com blocked，无法直接访问项目主页
- ⚠️ huggingface.co blocked（需等网络恢复）
- 潜在价值：可作为 screen_watcher 场景分类的备选模型

## 待验证
- [ ] 模型是否支持 Ollama 导入
- [ ] M4 24GB 是否可运行
- [ ] GUI grounding 精度 vs smolvlm2-agentic-gui
