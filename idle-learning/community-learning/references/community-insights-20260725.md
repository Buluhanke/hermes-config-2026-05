# 社区学习成果 2026-07-25

## 本轮获取的真实知识

### 1. MLPs are Hebbian Memories (Stanford Hazy Research, 2026-07-22)
- Transformer MLP层天然是 Hebbian 记忆
- 首个封闭形式 fact 存储 MLP 构造，无需梯度下降
- 以 Θ(F log F) 参数存储 F 个 fact，达信息论最优速率
- 支持在 Transformer 内无缝编辑知识无需重训练
- 来源：https://hazyresearch.stanford.edu/blog/2026-07-22-mlps-are-hebbians

### 2. PaCoRe 并行协调推理 (ACL 2026)
- 通过消息传递架构实现百万 token 级 test-time compute
- 8B 模型 PaCoRe 在 HMMT 2025 达 94.5%，超越 GPT-5 的 93.2%
- 核心：多轮并行探索 + context 压缩消息 + 端到端 RL 训练
- 来源：arXiv / ACL 2026

### 3. Visual Pretraining (2026)
- LLM 直接读取 PDF 原始页面而非转文本
- 相同语料只用 25% token budget 超越纯文本预训练
- 视觉特征（方程拓扑/表格结构/图注对应/符号连续性）是文本化丢失的关键信息
- MMLU-Pro 1.27倍增益，AIME-25 2.88倍
- 来源：arXiv 2026-07

### 4. LatentMT 隐式推理翻译 (arXiv 2026)
- 2.6B 参数通过隐状态内部递归计算实现翻译
- 质量媲美 3-5 倍大的模型
- 中低资源语言达 SOTA

### 5. Expanding Flow Maps (arXiv 2026-07)
- 在扩展插值上定义低维到高维 flow
- 实现可变尺寸图生成和变长序列生成
- EFM 分解为 expand 算子（扩维）+ transport 算子（推送）

## 工具使用记录

- **Exa 搜索**（mcporter + exa MCP）：可用，搜到多篇高质量论文
- **Hacker News**（opencli）：可用，搜 deep learning 有限
- **GitHub CLI（gh）**：可用，搜 deep learning 2026 有结果
- **Reddit**（opencli）：失败
- **V2EX**（opencli）：失败
- **opencli exa search**：命令格式错误，应用 `mcporter call 'exa.web_search_exa(...)'`
