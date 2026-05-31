# 2026-06-01 空闲学习记录（方向B — 理解层）

## 执行时间
2026-06-01 04:30 UTC（cron 定时触发）

## 数据来源
- HN Firebase API（top 10 stories）
- OSU-NLP-Group GUI-Agents-Paper-List（raw.githubusercontent.com 直接 YAML 扫描）
- ddgs CLI（备用搜索，结果有限）

## 网络状态
- github.com: ❌ timeout
- news.ycombinator.com: ❌ timeout
- hacker-news.firebaseio.com: ✅ 200
- httpbin.org: ✅ 200
- web_search (SearXNG): ❌ 502
- ddgs: ✅ 返回结果（5条）

## 新发现论文（首次记录）

### UILoop: UI-in-the-Loop 循环式 GUI 推理
**arXiv 2604.06995, Findings of ACL 2026** — ZJU (Songze Li et al.)

核心创新：将 GUI reasoning 从单向 screen→action 改为循环式 Screen-UI elements-Action 过程。MLLM显式学习UI元件定位、语义功能、实际使用方式。

发布资源：
- **UI Comprehension-Bench**: 26K 样本
- 三项评估指标：定位准确率 / 语义功能理解 / 实际使用正确性
- SOTA UI 理解性能 + 更优 GUI 推理结果

对Hermes启发：screen_trigger_handler 可集成 UILoop 的 Verify 阶段 — 动作执行后重新分析UI状态，形成闭环。

### AutoGUI-v2: 多模态 GUI 功能理解基准
**arXiv 2604.24441, Apr 27, 2026** — UCAS/CASIA/PolyU (Hongxin Li et al.)

关键创新：VLM-人协作递归解析多平台截图，从"浅层grounding"提升到"深层功能理解"

核心数据：
- 2,753 任务，覆盖 6 个操作系统
- 三层测试：region语义 → element grounding → 动态状态预测
- Qwen3-VL 在功能 grounding 上夺冠
- Gemini-2.5-Pro-Thinking 在功能描述上领先
- **所有模型在非标准交互（uncommon actions）上表现不佳**

对Hermes启发：场景分类应升级为"功能理解" — 不止识别场景类型，还要预测"点击这里会怎样"

### Same Outcomes, Different Journeys
**arXiv 2604.07929** — Stockholm University / Spotify (Maria Movin et al.)

核心发现：首个生产级搜索系统中人类 vs GUI agent 行为对比框架
- 39 参与者 + SOTA agent，10 个多跳搜索任务
- Agent 匹配了任务成功率，但采用搜索中心低分支策略
- 人类：内容中心探索（多页面浏览、猜测性点击）
- Agent：搜索中心直线路径（高成功率但 bot 特征明显）

对Hermes启发：dry-run 日志的屏幕变化序列可量化 behavioral alignment（拟人化程度），作为 humanize_click 效果的评估指标

### 其他新记录论文
- **CocoaBench** (arXiv 2604.11201, UCSD/MBZUAI): 统一数字 agent 评估，45.1% best
- **Odysseys** (arXiv 2604.24964, CMU): 200 长时跨站工作流，human gap 大
- **MolmoWeb** (arXiv 2604.08516, AI2): 开源纯视觉 web agent，screenshot-only，SOTA on WebVoyager
- **EE-MCP** (arXiv 2604.09815, Huawei): 自进化 MCP-GUI agent，经验库推理改进
- **CORA** (arXiv 2604.09155, HKU): Conformal Risk Control for mobile GUI safety
- **UI-Perturbed** (arXiv 2604.14262): domain randomization 显示 grounding 在 spatial reasoning 上掉 27-56 分

## 产线健康巡检快照
- screen_watcher: ✅ PID 8748, since 01:27
- 截图新鲜度: ✅ 04:21, ~3.3MB, ~60s 更新
- Ollama: ✅ qwen3-vl:2b (context=4096, 2.7GB, GPU 100%)
- 场景分布 (June 1): 224 other, 2 unknown, 1 browser
- unknown 率: 0.88% (2/227) ✅
- 否定词检测: ✅ "没有需要处理的内容或异常" → [silent]
- gateway hook 污染: 1658 (历史遗留，已停止增长)
- 冷却循环: ✅ ~60s cooldown, handler 周期 ~15-20s

## 下次学习方向
C — 决策操作层（AVR路由 / 生产级权限模型 / Dry-Run=False过渡）
