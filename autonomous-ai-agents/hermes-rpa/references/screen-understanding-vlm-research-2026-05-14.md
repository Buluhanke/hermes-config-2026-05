# Screen Understanding VLM — 2024-2025 开源方案调研

> 来源：2026-05-14 VLM调研任务
> 用途：hermes-rpa perception层升级参考

---

## 一、屏幕理解 + 点击定位（Click Grounding）方案

### 1. OmniParser（微软，2024.10）⭐ 最推荐

| 维度 | 详情 |
|-----|-----|
| **架构** | Florence-2/BLIP-2 做 region detection + captioning → LLM(GPT-4V/Claude) 理解屏幕+坐标 |
| **关键模块** | Region Detection（可交互区域）+ Captioning（语义描述）+ Grounding（坐标映射） |
| **开源** | ✅ 完全开源（MIT） |
| **本地运行** | ✅ Florence-2-base(~0.7B)，显存~4GB |
| **优点** | 无需accessibility tree，纯视觉，任意应用/浏览器可用；与LLM解耦即插即用；对动态UI(canvas/游戏)也有效 |
| **缺点** | 小模型复杂界面描述精度有限；每帧~2-5s推理；高度重叠UI处理不佳 |
| **GitHub** | github.com/microsoft/OmniParser |

### 2. SeeClick（2024.07）

| 维度 | 详情 |
|-----|-----|
| **架构** | 端到端视觉GUI grounding，基于Qwen-VL微调，输入截图输出点击坐标（直接回归，非bbox） |
| **关键创新** | Fuyu-8B架构，patch序列直接生成坐标token；ScreenSpot benchmark SOTA |
| **开源** | ✅ 完全开源 |
| **本地运行** | ✅ 8B需~16GB显存(量化后~8GB)；轻量版可用 |
| **优点** | 端到端无需中间件；坐标预测精度高；推理快于OmniParser级联方案 |
| **缺点** | 高分辨率屏幕(4K/5K)支持不佳；纯坐标输出缺少语义上下文；文字密集场景OCR不如专门引擎 |
| **GitHub** | github.com/nju-weblearning/SeeClick |

### 3. UI-TARS（字节跳动，2025.01）

| 维度 | 详情 |
|-----|-----|
| **架构** | 基于Qwen2-VL微调，Visual Grounding + Reflection + Action闭环；多步任务自验证 |
| **关键创新** | Captioning-based grounding + 操作后截图自我验证 + 历史状态维护 |
| **开源** | ✅ 完全开源 |
| **本地运行** | ✅ 7B/8B，量化后~6GB显存 |
| **优点** | ScreenSpot+GUIE双榜领先；有reflection机制减少错误积累；支持多轮交互 |
| **缺点** | 模型较大推理延迟高；对非Web应用需额外适配 |
| **GitHub** | github.com/bytedance/UI-TARS |

### 4. CogAgent（智谱/清华，2024.01）

| 维度 | 详情 |
|-----|-----|
| **架构** | CogVLM视觉GUI Agent；dual-encoder（低分辨率全局+高分辨率细节）；输出动作序列 |
| **关键创新** | High-res cross-attention(1120×1120)；Agent-9K数据集；系统状态回溯 |
| **开源** | ✅ 完全开源（Apache 2.0） |
| **本地运行** | ❌ 18B需~40GB显存(FP16)，量化后~12GB，门槛高 |
| **优点** | 高分辨率处理；grounding精度高；Web+桌面+手机都支持 |
| **缺点** | 模型太大本地难跑；推理慢(每步~3-8s)；动态内容理解有限 |
| **GitHub** | github.com/THUDM/CogAgent |

### 5. Qwen2-VL / Qwen2.5-VL（阿里，2024-2025）⭐ 本地VLM首选

| 维度 | 详情 |
|-----|-----|
| **架构** | 通用VLM，GUI理解能力强；支持任意分辨率(动态分辨率)；M-RoPE处理高分辨率图像 |
| **规格** | 2B/7B/72B三个版本 |
| **开源** | ✅ 完全开源（Apache 2.0） |
| **本地运行** | ✅ 2B量化后~2GB，7B量化后~6GB，72B需~40GB |
| **优点** | 多尺寸灵活选择；中英文都支持（对中国UI友好）；OCR能力强；内置视觉encoder |
| **缺点** | 非专门GUI Agent设计，需额外微调；grounding精度不如专用模型 |
| **GitHub** | github.com/QwenLM/Qwen2-VL |

### 6. smolvlm2-agentic-gui（已安装在Ollama）

| 维度 | 详情 |
|-----|-----|
| **架构** | smolvlm2微调版，专为GUI自动化设计，直接输出 `click(x=0.519, y=0.238)` 归一化坐标 |
| **规格** | 2.0GB，已在Ollama运行（`ahmadwaqar/smolvlm2-agentic-gui:latest`） |
| **本地运行** | ✅ 纯本地 |
| **优点** | 体积小推理快；直接输出坐标无需解析；已实测可用 |
| **缺点** | 微调专用模型，通用性不如Qwen2-VL；简单任务可用，复杂界面可能误判 |
| **安装** | `ollama pull ahmadwaqar/smolvlm2-agentic-gui` |

---

## 二、电脑控制 Agent（Computer Use Agent）架构

### Anthropic CUA（Claude Computer Use，2024.10）
- ❌ 闭源（API）；基于Claude 3.5 Sonnet/Vision API
- 闭环：`截图 → 分析 → 动作 → 观察结果 → 截图`
- 参考价值：动作空间设计（mouse_move/left_click/key/type/scroll/screenshot/wait）+ 安全护栏

### Microsoft UFO / PCAgent
- UFO：双Agent架构（HostAgent+AppAgent）+ Windows UIA（UI Automation）
- PC-Agent：单Agent + PyAutoGUI + GPT-4V截图
- 参考价值：UFO的双Agent分工思路；PC-Agent的简单架构

### AppAgent（腾讯，2024.01）
- 手机端为主，桌面适配不完善
- 核心思想：自主探索生成操作文档，基于文档执行任务
- 参考价值：自主探索机制（exploration→execution两阶段）

### OS-Copilot / FRIDAY
- 通用OS Agent；FRIDAY核心模型；Linux桌面（可扩展macOS/Windows）
- 参考价值：自我改进机制；系统级控制能力

### OpenAdapt
- 记录人类操作→生成自动化脚本→LLM驱动的GUI Agent
- 参考价值：人机协同设计；从演示中学习流程重建

---

## 三、记忆系统对比

| 方案 | 开源 | 本地 | 记忆类型 | 特点 |
|------|------|------|---------|------|
| **Mem0** | ✅ MIT | ✅ | 对话历史+实体提取+图谱 | 自动提取用户偏好/事实，多session聚合 |
| **Letta(MemGPT)** | ✅ Apache 2.0 | ✅ | 分层记忆(Main/Working/Archival) | 自我编辑记忆，Virtual Context Management |
| **Zep** | ✅ Apache 2.0 | ✅ | 长期对话+实体+摘要 | 生产级，多session聚合 |
| **Memary** | ✅ MIT | ✅ | 知识图谱+实体记忆 | 图结构，可解释性强 |
| **claude-mem** | ✅ MIT | ❌(需Anthropic API) | 对话历史+事实提取 | 仅Claude Code可用 |

**结论**：Mem0（用户事实提取）+ Letta（分层记忆管理）是Hermes最佳参考。

---

## 四、工作流自动化对比

| 方案 | 本地运行 | 核心能力 |
|------|---------|---------|
| **n8n** | ✅ 自托管 | 400+集成，webhook/定时/事件触发，AI Agent节点 |
| **LangGraph** | ✅ | 状态机控制流，Human-in-the-loop，最灵活 |
| **Temporal** | ✅ | 分布式工作流引擎，企业级可靠性 |
| **Dify** | ✅ | 可视化Agent+RAG管道，中文生态好 |

**结论**：n8n自托管 + LangGraph Agent 是最佳组合。

---

## 五、Hermes架构差距矩阵

| 维度 | 现状 | 目标 | 差距 |
|------|------|------|------|
| 感知范围 | 仅Chrome浏览器 | 任意桌面应用+浏览器 | 🔴 大 |
| 视觉理解 | 百度OCR（云端，需上传） | 本地VLM（OmniParser/Qwen2-VL） | 🟡 中 |
| 记忆系统 | 无跨session记忆 | Mem0+Letta混合 | 🔴 大 |
| 主动触发 | 纯指令驱动 | 时间/事件/状态触发 | 🔴 大 |
| 工作流 | 单步工具调用 | n8n事件驱动 | 🟡 中 |
| 工具优化 | 基础function calling | 动态路由+reflection+缓存 | 🟡 中 |

---

## 六、升级路线图（建议优先级）

### Phase 1（快速见效）
```
Hermes + OmniParser（本地）
→ 保留Chrome CDP做精确grounding
→ OmniParser做fallback和桌面应用扩展
→ 替换百度OCR为OmniParser captioning
```

### Phase 2（能力增强）
```
Hermes + SeeClick + OmniParser + Qwen2-VL
→ SeeClick：快速grounding（轻量任务）
→ OmniParser：密集描述+grounding（复杂任务）
→ Qwen2-VL：本地OCR+屏幕理解
→ Reflection机制（UI-TARS启发）
```

### Phase 3（完全自洽）
```
端到端GUI Agent
→ 统一视觉感知模块
→ 本地VLM推理（Hermes 3 + Qwen2-VL）
→ 跨平台桌面控制
→ 自我改进机制
```

---

## 七、关键Benchmark参考

| Benchmark | 描述 | 领先方案 |
|-----------|------|---------|
| ScreenSpot | 截图grounding坐标预测 | SeeClick > CogAgent > OmniParser |
| GUIE | 多步GUI任务执行 | UI-TARS > CogAgent > UFO |
| OSWorld | 桌面OS任务 | FRIDAY > UFO > PC-Agent |
| MiniWob++ | Web交互任务 | UI-TARS > SeeClick > CogAgent |
