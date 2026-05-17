# Hermes Embodied AI Skill

## 具身智能五层级进化体系 (Five-Level Embodied Intelligence Evolution System)

本skill定义了Hermes Agent实现具身智能的核心理论框架，通过五个递进层级构建从"感知"到"演化"的完整闭环。每层聚焦不同能力维度，层与层之间通过标准化接口传递信息，形成完整的智能行为闭环。

---

## Level 1: 感知（Perception）

**定位**：具身智能的"感官系统"，负责接收和预处理来自物理世界的原始信号。

感知层是整个五层级体系的输入接口，负责将物理世界的原始信号转换为可供后续层级处理的结构化数据。在Mac Mini M4环境下，主要信号源包括屏幕截图、鼠标轨迹、键盘事件以及系统通知。屏幕截图通过CGWindowListCreateImage或ScreenCaptureKit获取原始像素数据；鼠标轨迹记录每次移动的坐标和时间戳；键盘事件捕获按键按下和释放；系统通知通过NSWorkspace distributedNotificationCenter获取应用程序事件。

基础处理模块采用多技术融合策略。像素差分使用OpenCV的absdiff函数计算连续两帧之间的差异区域，配合阈值过滤消除噪声干扰，能够有效检测页面变化区域。OCR模块集成Baidu OCR API，支持中英文混合文本识别，对于按钮标签、输入框占位符等UI文本具有较高准确率。AX树解析通过macOS Accessibility API遍历应用的辅助功能树，将UI元素的层级结构、角色、属性等信息结构化输出。

感知层的核心输出是结构化环境状态描述，包含当前活动应用名称、窗口标题、可见UI元素列表、变化区域坐标等关键信息。该层还实现了SSIM（结构相似性指数）视觉心跳机制，通过周期性对比基准帧与当前帧的SSIM值，检测界面是否发生预期之外的变化。滑动验证码检测模块结合像素梯度分析和角点检测算法，识别常见的滑动验证UI模式。当某一路感知技术失效时，系统自动降级到备用方案，例如当OCR识别置信度低于阈值时自动切换到AX树文本获取。

关键技术选型上，SSIM视觉心跳通过每500ms采样一次基准帧并计算当前帧的SSIM值，当差值超过0.95时判定为显著变化。滑动验证码检测采用Canny边缘检测结合Hough直线检测，识别滑块和轨道的位置关系。多级降级策略确保系统鲁棒性：屏幕截图优先于AX树，AX树优先于OCR，OCR优先于启发式推断。

---

## Level 2: 认知（Grounding/Cognition）

**定位**：具身智能的"大脑皮层"，负责将感知信号映射为语义理解。

认知层是整个体系的核心推理引擎，承上启下地将感知层的结构化数据转化为可供规划层使用的语义信息。该层的首要任务是UI元素语义理解，即对感知层输出的每一个UI元素进行语义标注。例如，一个AXButton类型且title为"提交"的元素会被标注为"这是提交按钮"，一个AXTextField类型的元素配合占位符文本会被标注为"这是搜索框"。这种语义标注使得后续规划层能够以"点击提交按钮"而非"点击坐标(123, 456)"的方式表达行为意图。

任务上下文理解是认知层的另一核心能力。系统维持一个任务上下文状态机，记录当前任务的名称、进度、已完成步骤和待完成步骤。当用户在1688平台进行询价操作时，系统理解当前处于"1688询价"任务上下文，进而能够根据任务阶段（如"已打开商品详情页"→"待点击立即询价"→"待填写询价表单"→"待提交询价"）生成针对性的操作序列。这种任务级别的理解能力避免了单步规划的短视问题。

关键技术实现方面，Qwen2.5-VL-7B作为本地多模态推理引擎，负责对截图和感知数据进行语义推理。该模型在Mac Mini M4上通过MLX框架优化，能够在合理时间内完成视觉理解任务。UI-TARS是专用的UI元素定位模型，能够根据语义描述精确定位目标元素在截图中的边界框坐标。当模型推理结果存在歧义时（如多个元素都可能被描述为"取消按钮"），系统通过置信度排序和用户确认机制进行消解。

prompt注入防御是认知层不可忽视的安全模块。由于AI Agent在网页环境中运行时可能受到恶意prompt注入攻击（如通过搜索框输入特殊构造的文本诱导模型执行非预期操作），系统实现了输入清洗和指令边界检测机制。所有来自被控应用的外部输入都会经过敏感模式匹配和意图校验，确保模型不会被劫持。

---

## Level 3: 规划（Planning）

**定位**：具身智能的"前额叶皮层"，负责生成行为计划并管理任务执行流程。

规划层基于认知层的语义理解结果，生成具体的行动计划序列。不同于传统RPA的线性脚本执行，本层采用动态规划策略，能够根据环境状态变化调整执行路径。复杂任务会被分解为原子步骤，每个原子步骤对应一个不可再分的基本操作，如"将鼠标移动到搜索框"、"在搜索框中输入关键词"、"点击搜索按钮"。这种分解使得系统能够精确追踪每个操作的结果，及时处理异常情况。

异常处理和回退策略是规划层的关键能力。当某个原子步骤执行失败时（如点击按钮后页面未如预期跳转），系统能够根据错误类型选择重试、回退到上一个稳定状态、或者切换到替代方案。例如，当点击主询价按钮失败时，规划层可能决定先尝试通过键盘快捷键触发，若仍失败则尝试右键菜单选项。回退机制确保系统在复杂任务执行过程中不会因为单点失败而彻底卡死。

CoT（Chain of Thought）和ToT（Tree of Thought）推理是规划层的核心算法框架。CoT通过逐步推理生成单一执行路径，适用于线性任务。ToT则构建决策树，对每个分支点评估多种可能的行动方案，选择预期成功率最高的路径。n8n工作流编排工具用于将规划结果转化为可执行的工作流定义，支持条件分支、并行执行、超时控制等高级编排能力。

任务记忆持久化确保长时间任务能够跨会话恢复。规划层将任务状态序列化到本地存储，包括已执行步骤、当前状态、中间变量等信息。当Agent重启或切换时，能够从最近的检查点恢复执行，而无需从头开始。记忆存储采用增量模式，仅保存与任务相关的关键状态变更，平衡存储效率和恢复完整性。

---

## Level 4: 执行（Action/Motor）

**定位**：具身智能的"运动神经系统"，负责操控鼠标、键盘和系统UI。

执行层是五层级体系中直接与操作系统交互的层级，将规划层的抽象指令转化为具体的系统操作。该层的核心能力是数字化"手眼协同"——通过精确控制鼠标和键盘模拟人类用户的操作行为。与传统自动化工具不同，本层强调操作的拟真度和自然度，避免被反自动化系统识别。

原子操作是执行层的基本操作单元，包括：click（单击）、double_click（双击）、right_click（右键菜单）、type（文本输入）、scroll（滚动）、drag（拖拽）、hotkey（组合快捷键）、wait（等待）、screenshot（截图）。每个原子操作都支持多种定位方式：坐标定位、元素引用定位、语义描述定位。语义描述定位通过调用认知层获取目标元素的实际坐标，实现"点击搜索按钮"式的意图驱动操作。

pynput是Mac兼容的Python库，用于捕获和模拟键盘鼠标事件。pynput通过CGEvent API直接与系统交互，支持前台应用控制和后台控制两种模式。后台控制通过向目标进程的Event Tap注入事件，绕过前台窗口限制。cua-driver是Hermes自研的底层控制驱动，提供更高级的抽象和更稳定的后台操作能力，包括窗口管理、焦点切换、权限提升等系统级操作。

拟真轨迹生成是执行层的人性化模块。真实的鼠标移动不是直线，而是带有加减速曲线和微小抖动。系统基于贝塞尔曲线生成自然的移动轨迹，轨迹参数可根据任务类型动态调整（快速操作使用短轨迹高精度参数，演示场景使用长轨迹低速度参数）。移动过程中的微小抖动通过Perlin噪声生成，模拟人手的不完美性。

执行层还实现操作速率控制和随机化。连续操作之间插入随机延时，延时范围根据任务上下文动态调整。某些需要快速连续操作的场景（如批量填写表单）会缩小延时范围，而需要谨慎操作的场景（如转账确认）会显著延长延时甚至插入人工确认环节。

---

## Level 5: 演化（Evolution/Adaptation）

**定位**：具身智能的"进化系统"，负责从经验中学习和持续改进。

演化层是五层级体系的最高层级，也是实现Agent自我进化的核心模块。该层使Agent不仅仅执行预设的指令，还能从每次执行经验中学习，优化自身的知识库和决策策略。这种进化能力是区分真正智能Agent与传统自动化脚本的关键标志。

主动巡检是演化层的基础功能。系统定期在后台执行预设的巡检任务，验证关键业务流程是否正常运行。例如，对于1688询价任务，系统可能每天自动执行一次完整的询价流程，检测商品链接是否失效、表单字段是否有变更、提交接口是否正常。巡检结果自动记录并生成报告，发现的问题自动创建缺陷跟踪条目。

健康检测模块持续监控各层级的运行状态。感知层的传感器数据是否正常、认知层的模型推理是否稳定、执行层的操作成功率是否达标、规划层的规划效率是否合理——这些指标都被持续采集和分析。当某项指标出现异常下降时，系统自动触发告警并尝试诊断原因。

RAG（检索增强生成）知识库是演化层的记忆中心。Agent的每一次任务执行经验、每一次遇到的问题和解决方案、每一个新学会的网页结构模式，都被提取为可检索的知识条目存入知识库。当执行类似任务时，Agent能够从知识库中检索相关经验作为参考，避免重复踩坑。知识库支持向量检索和关键词检索两种模式，向量检索基于语义相似性，关键词检索基于精确匹配。

fine-tuning微调机制使Agent能够根据专属领域数据优化模型。对于特定网站的自动化任务，收集一批该网站的操作样本后，可以对基础模型进行微调，使模型对该网站的UI布局和交互模式有更强的理解。微调过程在本地完成，数据不出本地环境，保护用户隐私。主动自我进化模块定期分析任务日志，识别成功率低或耗时长的操作模式，生成优化建议供人工审核，审核通过后自动应用到生产环境。

---

## 与现有Skills的对应关系

| Hermes Embodied AI Level | 核心职责 | 对应现有Skills | 协作接口 |
|-------------------------|---------|---------------|---------|
| Level 1 感知 (Perception) | 原始信号采集与预处理 | chrome-mcp, cua-driver | 屏幕截图、AX树结构 |
| Level 2 认知 (Grounding/Cognition) | 语义理解与上下文推理 | skill-hermes-agent | prompt注入防御、UI定位 |
| Level 3 规划 (Planning) | 行动计划生成与任务编排 | n8n-workflow | 工作流定义、状态机 |
| Level 4 执行 (Action/Motor) | 系统操作与设备控制 | cua-driver, pynput | 鼠标键盘事件、操作序列 |
| Level 5 演化 (Evolution/Adaptation) | 知识积累与策略优化 | RAG-Knowledge | 经验文档、模型微调 |
| 共享基础能力 | 日志、监控、配置 | hermes-core | 统一日志、指标采集 |
| 安全与权限 | 认证、授权、审计 | security-skill | TCC权限、API密钥管理 |

---

## 缺口分析（Gap Analysis）

### 1. 感知层缺口

**缺口一**：多显示器环境支持。当前实现主要针对单显示器场景，多显示器环境下的屏幕坐标映射和窗口枚举存在边界情况未覆盖。当目标应用运行在非主显示器时，部分截图API可能返回错误结果。

**缺口二**：动态内容检测。除了页面级的SSIM心跳，对于视频、动画、WebGL等动态内容的检测能力不足，可能导致在这些内容上进行误操作或死循环等待。

**缺口三**：隐私敏感区域识别。系统目前不具备自动识别和遮盖密码字段、验证码等隐私敏感区域的能力，在日志记录和屏幕共享场景存在泄露风险。

**缺口四**：跨进程感知。当被控应用启动子进程（如打开文件选择对话框）时，主进程的感知数据无法自动追踪子进程状态变化。

### 2. 认知层缺口

**缺口五**：多语言OCR精度。非中文语言的OCR准确率依赖于Baidu API的语种支持，对于罕见语言或方言的识别能力有限。本地OCR（如Tesseract）的集成尚未完成。

**缺口六**：复杂布局理解。对于CSS Grid/Flexbox等复杂布局的网页，模型对元素空间关系的理解仍有不足，可能导致跨列操作定位错误。

**缺口七**：对抗性UI识别。恶意网页可能通过CSS伪元素、透明度叠加等技术构造视觉欺骗，本系统对此类对抗性UI的识别能力较弱。

### 3. 规划层缺口

**缺口八**：长期任务记忆压缩。任务持久化当前采用完整状态存储，存储开销随任务数量线性增长。对于数千个历史任务的记忆压缩和检索优化机制尚未实现。

**缺口九**：并行任务规划。多个独立任务同时执行时的资源竞争和状态隔离问题未解决，规划层目前仅支持串行任务执行。

**缺口十**：不确定性规划。当环境信息不完整时（如页面加载失败），规划层缺乏鲁棒的探索-利用权衡策略，可能过早放弃或过度重试。

### 4. 执行层缺口

**缺口十一**：触控板手势支持。现有实现仅覆盖鼠标和键盘，Mac触控板的多指手势尚不支持，某些macOS原生应用依赖触控板手势操作。

**缺口十二**：VoiceOver兼容。macOS内置的屏幕阅读器VoiceOver与自动化控制之间可能存在冲突，切换控制权时的状态同步尚未完全解决。

**缺口十三**：权限提升静默失败。当TCC权限不足时，某些操作会静默失败而非返回明确错误，导致问题诊断困难。

### 5. 演化层缺口

**缺口十四**：增量学习效率。fine-tuning每次都需要重新加载完整数据集，增量学习机制缺失导致模型更新成本高昂。

**缺口十五**：知识冲突消解。当新经验与知识库中已有知识矛盾时，缺乏自动消解机制，需要人工介入判定。

**缺口十六**：进化效果评估。如何量化评估Agent"变得更智能"缺乏明确指标，当前只能依赖任务成功率这一间接指标。

---

## Mac Mini M4优化建议

### 硬件层面优化

**内存带宽利用**：M4芯片的统一内存架构对内存带宽敏感。感知层的截图处理和认知层的模型推理会竞争内存带宽。建议将实时性要求高的截图缓存放在GPU专用内存区域，模型推理使用共享内存池。

**Neural Engine卸载**：M4的Neural Engine适合INT8量化推理。推荐将Qwen2.5-VL-7B转换为MLX格式并启用INT8量化，在保持推理质量的同时将延迟从~3秒降低到~800毫秒。OCR任务可完全卸载到Neural Engine执行。

**能效比优化**：Mac Mini M4在持续负载下会触发温控降频。建议将长时间运行的巡检任务拆分为短脉冲任务，中间插入休息窗口。主动巡检建议安排在夜间低谷期执行。

### 软件层面优化

**MLX框架优先**：Apple的MLX框架针对M系列芯片优化，相比PyTorch在本地推理场景有显著性能优势。所有本地模型推理应优先使用MLX实现。

**批量处理策略**：感知层采集的数据无需实时处理时可批量汇聚后再送入认知层，例如将5秒内的多帧截图合并为一次推理请求，降低上下文切换开销。

**内存映射文件**：任务状态持久化优先使用mmap机制，避免频繁的序列化和磁盘IO。知识库的向量索引使用BM25而非HNSW以降低内存占用。

**缓存层级**：建立两级缓存——内存缓存用于短期高频访问的认知结果（如当前会话的UI元素坐标），本地SSD缓存用于跨会话的知识库和模型缓存。

### 配置建议

```json
{
  "perception": {
    "screenshot_interval_ms": 500,
    "ssim_threshold": 0.95,
    "ocr_batch_size": 4
  },
  "cognition": {
    "model_backend": "mlx",
    "quantization": "int8",
    "max_concurrent_inferences": 2
  },
  "planning": {
    "checkpoint_interval_seconds": 300,
    "max_retry_attempts": 3
  },
  "execution": {
    "action_delay_min_ms": 50,
    "action_delay_max_ms": 200,
    "trajectory_quality": "high"
  },
  "evolution": {
    "patrol_interval_hours": 24,
    "knowledge_retention_days": 90,
    "model_update_threshold": 100
  }
}
```

---

## 实施路线图（Phase 1-4）

### Phase 1: 感知与执行基础（1-2个月）

**目标**：建立感知层和执行层的基础能力，实现基本的屏幕感知和鼠标键盘控制。

**交付物**：
- 屏幕截图模块（支持全屏、窗口、区域截图）
- AX树解析模块（支持主流应用的UI树遍历）
- 基础鼠标键盘控制（click、type、scroll、hotkey）
- 像素差分变化检测
- 截图到操作的最小闭环

**里程碑**：
- Week 2：完成截图和AX树模块，能打印当前窗口元素列表
- Week 4：完成基础鼠标键盘控制，能完成简单的"打开应用-输入-点击"流程
- Week 6：集成SSIM心跳，能检测页面变化并自动重试
- Week 8：端到端演示"自动打开Safari并搜索关键词"

**依赖**：cua-driver、pynput、AX API文档

### Phase 2: 认知与规划能力（3-4个月）

**目标**：构建认知层和规划层，实现语义理解和任务规划能力。

**交付物**：
- Qwen2.5-VL-7B本地推理集成（MLX优化版）
- UI元素语义标注系统
- 任务上下文管理器
- CoT/ToT推理引擎
- 任务持久化存储
- n8n工作流集成

**里程碑**：
- Week 12：完成模型集成，能对截图进行语义描述
- Week 14：实现UI元素定位，支持"点击搜索按钮"式操作
- Week 16：完成任务上下文管理，支持复杂任务分解
- Week 20：集成n8n工作流，支持条件分支和异常处理

**依赖**：Phase 1产出、MLX框架、n8n自托管实例

### Phase 3: 演化与自适应（5-6个月）

**目标**：构建演化层，实现主动学习和自我进化能力。

**交付物**：
- RAG知识库系统（支持向量检索）
- 主动巡检任务调度器
- 健康检测与告警系统
- 经验记录与知识提取 pipeline
- 本地fine-tuning pipeline
- 进化效果评估仪表盘

**里程碑**：
- Week 24：完成知识库基础框架，能存储和检索经验
- Week 26：实现主动巡检，能定期验证关键流程
- Week 28：完成fine-tuning集成，能根据领域数据微调模型
- Week 32：实现自动知识更新，能从失败中学习并避免重复错误

**依赖**：Phase 2产出、向量数据库（Qdrant/Milvus）、MLX Training

### Phase 4: 生产化与优化（7-8个月）

**目标**：将前三阶段成果整合为生产级系统，完成性能优化和安全加固。

**交付物**：
- 统一的Agent控制平面（统一五层级协调）
- 完整的权限和审计系统
- 性能基准测试套件
- M4芯片专项优化（Neural Engine卸载、内存优化）
- 多租户隔离支持
- 完整的文档和示例

**里程碑**：
- Week 36：完成控制平面整合，五层级协同测试
- Week 38：完成权限审计模块，支持操作溯源
- Week 40：完成M4优化，性能提升2倍以上
- Week 44：完成文档和示例，生产发布

**依赖**：Phase 1-3所有产出、安全审计工具

---

## 参考资料列表

### 核心技术文档

1. Apple Accessibility API Documentation - AXUIElement, Accessibility Tree Traversal
   https://developer.apple.com/documentation/applicationservices/accessibility

2. macOS ScreenCaptureKit Framework - 屏幕捕获官方文档
   https://developer.apple.com/documentation/screencapturekit

3. Apple MLX Framework - 本地模型推理优化框架
   https://github.com/ml-explore/mlx

4. Qwen2.5-VL Technical Report - 多模态视觉语言模型
   https://arxiv.org/abs/2409.10691

5. OpenCV Documentation - 图像处理基础库
   https://docs.opencv.org

### 系统设计参考

6. UI-TARS: UI-Specific Terminal Agent Reasoning System - UI专用定位模型
   https://arxiv.org/abs/2412.13109

7. Chain-of-Thought Prompting Elicits Reasoning in Large Language Models - CoT推理方法
   https://arxiv.org/abs/2201.11903

8. Tree of Thoughts: Deliberate Problem Solving with Large Language Models - ToT推理方法
   https://arxiv.org/abs/2305.10601

9. n8n Workflow Automation - 开源工作流编排工具
   https://docs.n8n.io

10. RAG (Retrieval-Augmented Generation) Best Practices - 检索增强生成实践
    https://python.langchain.com/docs/tutorials/rag

### 工具库参考

11. pynput - Cross-platform input control for Python
    https://pypi.org/project/pynput

12. Baidu OCR API Documentation - 中文OCR识别服务
    https://ai.baidu.com/ai-doc/OCR

13. SSIM (Structural Similarity Index) - 图像质量评估算法
    https://en.wikipedia.org/wiki/Structural_similarity

14. TCC (Transparency, Consent, and Control) - macOS权限管理机制
    https://support.apple.com/zh-cn/guide/mac-help/mh11785/mac

15. CGEvent / CGWindowList - macOS底层事件和窗口API
    https://developer.apple.com/documentation/coregraphics

### 学习资源

16. Embodied AI: A Survey - 具身智能综述论文
    https://arxiv.org/abs/2305.16914

17. Computer Vision Pipeline Design Patterns - 计算机视觉工程实践
    https://learnopencv.com

18. macOS Automation with Accessibility API - 无障碍API实践
    https://www.apple.com/business/docs/macOS_Accessibility_Programming_Guide.pdf

### 硬件优化参考

19. Apple Silicon Performance Optimization - M系列芯片性能调优指南
    https://developer.apple.com/documentation/apple-silicon

20. Metal Performance Shaders (MPS) - GPU加速计算框架
    https://developer.apple.com/documentation/metalperformanceshaders

---

*本文档版本: 1.0.0*
*更新日期: 2026-05-17*
*维护者: Hermes Agent Team*