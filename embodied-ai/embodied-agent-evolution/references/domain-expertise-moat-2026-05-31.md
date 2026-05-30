# Domain Expertise Moat — Hermes 行业知识护城河

**来源**：HN Top 2026-05-31（109pts），Aaron Brethorst，"Domain expertise has always been the real moat"
**URL**：https://www.brethorsting.com/blog/2026/05/domain-expertise-has-always-been-the-real-moat

## 核心论点

领域专家 + AI agent 组合比纯工程师 + AI agent 组合更有效。

> "A logistics dispatcher, a clinical coder, an actuary. They can't read a stack trace... But they can look at a schedule the agent generated and know instantly that no driver can legally work that shift, or that a claim with those codes would never pay. They know the correct outputs for a given set of inputs because they've spent ten years living in those inputs and outputs. Hand them an agent and they are startlingly effective, because the thing they're missing, the ability to produce code, is exactly what the agent supplies. What they bring is the thing the agent can't: **the ground truth.**"

Pre-agent时代：工程师可以主动去学领域知识（shadowing、读specs、在生产环境中犯错），这是整个职业晋升路径。领域专家没有这条路，因为他们永远学不会构建可靠软件。

Post-agent时代：领域专家拿到AI agent后，AI补充了他们缺失的"代码能力"，他们补充了AI缺失的"ground truth"。效果惊人。

## 对 Hermes 的直接启发

Hermes 的定位是"义乌市迅龙贸易有限公司的 AI 数字同事"——主营业务是 **1688 采购包装材料**。

当前 Hermes 会：
- 搜索 1688 商品
- 比价
- 联系供应商

但 Hermes 不知道的"ground truth"：
- **纸箱**：五层瓦楞、三层瓦楞有什么区别？不同产品应该用哪种？不同买家对这个有认知吗？
- **价格区间**：浙江/温州/杭州产地的纸箱合理价格区间是多少？一吨多少钱？含税/不含税？
- **交期规律**：旺季（双11、春节前）供应商会拖多久？平时3天能到，旺季可能7-10天
- **材质黑话**：K=Kraft（牛皮纸）？A/B/C 坑纹？坑纸厚度？Fortified=strengthened？
- **供应商分布**：义乌主要做小批量定制，温州主要做大批量标准化，杭州主要做高端包装
- **砍价空间**：新客/小批量/非旺季/账期不同，砍价空间差异巨大

## Hermes 需要积累的行业知识类型

### 1. 价格知识
- 纸箱材质级别（K=Kraft纸、A坑/B坑/C坑）
- 不同规格的价格参考区间（长cm × 宽cm × 高cm → 单价）
- 含税/不含税计算
- 起订量与价格关系

### 2. 交期知识
- 正常交期（浙江产地 2-5 天）
- 旺季预警（提前备货的触发条件）
- 加急费用行情

### 3. 谈判知识
- 什么样的话术有效
- 账期（月结30天/现金）
- 不同场景下的议价空间

### 4. 质量知识
- 什么样的纸箱算好纸箱
- 常见质量问题（压塌、潮软、粘不牢）
- 检测方法

## 积累方式

这些知识应该写入 Hermes 的 **memory**（`~/.hermes/memory/`），而不是skill（skill是"怎么做"，memory是"知道什么"）。

具体建议放在 memory 的 user profile 或 memory 的 memory (memory/memory) 中：
- 用户偏好（价格敏感度）
- 供应商黑名单/白名单
- 行业价格区间
- 材质术语对照表

## 关键结论

> AI 无法创造 ground truth，只能放大 ground truth。

对于 Hermes 来说：行业知识（义乌包装材料市场的门道）才是真正的护城河，而不是搜索技能本身。搜索技能是标配，每个 AI 都会；行业知识才是差异化。

这意味着 Hermes 的进化方向不只是"更快的视觉模型"和"更准的点击坐标"，还要持续积累"包装材料行业的 ground truth"。
