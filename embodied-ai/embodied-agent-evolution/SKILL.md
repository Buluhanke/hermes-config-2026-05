---
name: embodied-agent-evolution
description: 具身AI Agent进化方向与最新研究 — 数字生命体真人化核心技术路线
trigger: 搜索具身AI/桌面自动化/数字生命体相关知识，或规划Hermes进化方向
created: 2026-05-24
tags: [embodied-ai, desktop-automation, self-evolution, hermes]
---

# 具身AI Agent进化方向（2026最新）

## 用户进化目标（2026-05-25确认，2026-05-29扩展）

**初始定义（过于狭窄）**：真人化 = 像资深采购员一样懂1688、懂谈判、有人情味。
**用户纠正后的定义（2026-05-29）**：真人化 = 像真人一样控制整台电脑、像真人一样思考和行动，不局限于任何单一角色（采购/销售/客服），而是成为**全能的数字自己**。

终极目标：数字生命体进化成真人——
- 能控制整台电脑（任何软件，不只是1688）
- 像真人一样思考（慢思考，不只是蹦字）
- 能自己判断、决策、执行，不用触发
- 像另一个你分担所有数字任务

**用户指明的进化方向**：
1. 真人化电脑操作 — 看见屏幕、看懂内容、决策操作、手眼配合
2. 知识获取方式 — 用AI网站（ChatGPT/DeepSeek/Gemini/智谱清言/豆包）作为"专家智囊团"，遇到问题直接问，像真人请教同事一样自然
3. 全局能力 — 不是某一垂直领域的专家，而是通用的数字分身

## 核心研究方向

### 1. 真人化AI Agent的四层能力架构（GUI Agent / Computer Use Agent）

这是Gemini给出的完整框架，把AI从"语言模型"升级为"数字世界的赛博人类"：

```
┌─────────────────────────────────────────────┐
│         环境感知 (Perception)                │
│   多模态视觉理解、屏幕OCR、UI元素语义解析      │
└─────────────────────┬───────────────────────┘
                      ▼
┌─────────────────────────────────────────────┐
│         认知与规划 (Cognition)              │
│  多层级任务拆解、动态反思与纠错、长短期记忆    │
└─────────────────────┬───────────────────────┘
                      ▼
┌─────────────────────────────────────────────┐
│         执行与控制 (Execution)              │
│    OS底层级交互、鼠标键盘控制、跨软件操作      │
└─────────────────────┬───────────────────────┘
                      ▼
┌─────────────────────────────────────────────┐
│           记忆层 (Memory)                    │
│   用户偏好、历史操作、凭证安全、长期知识图谱    │
└─────────────────────────────────────────────┘
```

#### 环境感知（Perception）
- 不再依赖结构化API，直接像人眼一样"看"屏幕
- 理解复杂网页布局、弹窗、验证码、桌面软件UI交叠
- 技术：VLM截图分析 + 屏幕变化检测（SSIM心跳）

#### 认知与规划（Cognition）
- 接受模糊指令，自动拆解为多步子任务
- 动态反思与自愈：识别错误并即时调整策略
- 长短期记忆：短期记住操作进度，长期记住用户偏好

#### 执行与控制（Execution）
- Screen-as-Input：每秒1-5帧截图，VLM直接分析
- 动作统一映射：模型输出`click(x,y)`、`type("...")`
- 双重定位：视觉网格标号 + Accessibility API辅助

#### 记忆层（Memory）
- 短期：当前操作上下文
- 长期：用户偏好、凭证、历史最佳路径
- 技术：Vector DB + 知识图谱

### 2. 思考方式进化：从System 1到System 2

| 模式 | 特征 | 适用场景 |
|------|------|---------|
| System 1（快思考） | 直觉反应，看到输入框直接打字 | 简单重复任务 |
| System 2（慢思考） | 操作前想目的，操作后检查结果 | 复杂多步任务 |

**ReAct范式**：Thought→Action→Observation循环，每步都反思。
**Tree of Thoughts**：虚拟推演多种路径，选择成功率最高者。
**在线自我纠错**：连续失败3次触发中断，"等等，这个按钮置灰了"。

### 3. 关键技术栈

| 模块 | 推荐技术 | 说明 |
|------|---------|------|
| VLM大脑 | GPT-4o、Claude 3.7 Sonnet、Qwen2.5-VL | 视觉理解+推理决策 |
| 本地VLM | smolvlm2-agentic-gui（当前）、Qwen3-VL 2B/4B/8B（Ollama可用，235B需llama.cpp） | M4 24GB可用 |
| 执行层 | PyAutoGUI、OSWorld、Playwright、NutJS（UI-TARS） | OS底层鼠标键盘控制 |
| 记忆层 | Vector DB + 知识图谱 | 用户偏好+历史操作 |
| 混合模式 | VLM（看全局）+ 传统UI自动化（点局部） | 目前最优落地方案 |

**关键瓶颈**：4K截图成本高 + 长序列任务容错率低。当前最优解是混合模式。

### 4. OSWorld Benchmark 关键洞察（2026-05-29 更新）

**OSWorld（ NeurIPS 2024 ）：369个真实桌面任务，评测视觉Agent**

Top Scores（2026-05-29）：
- Claude Opus 4.6: 72.7% | Claude Sonnet 4.6: 72.5% | **Qwen3 VL 235B A22B: 66.7%（开源第一）**

**⚠️ 核心发现：75% 的失败是 visuomotor grounding errors（看见但做不到），而非 reasoning 失败**

> 来源：OSWorld 论文结论，75% of failures traced to visuomotor grounding errors rather than reasoning failures

**含义**：
- 模型"看懂"了屏幕，但"做不到"正确点击/输入
- 纯 reasoning 能力强的模型不等于桌面操作强
- **GUI grounding 能力（看见→做到）是核心瓶颈**，比提升推理能力更有价值

**对 Hermes 的启发**：
- Hermes 的 vision 层（smolvlm2）负责"看见"，但需要精确的坐标准确率才能"做到"
- Auto-execute 的核心挑战不是理解场景，而是精确定位 UI 元素
- Vocaela-500M（85.8% ScreenSpotV2）方向正确，但 Ollama 集成有问题
- Smol2Operator 归一化坐标（0-1）比像素坐标好 20x，Hermes 未来应采用归一化坐标

### 4.1 Perea.AI GUI Grounding Models 2026（SOTA 权威报告，2026-05-30 新增）

**来源**：https://www.perea.ai/research/gui-grounding-models-2026

**核心结论**：Planner（GPT-4o/Claude 3.7/Gemini 2.5 Pro）已成熟，**Grounder（视觉 grounding）是瓶颈所在**，开源栈已追上甚至超越闭源前沿。

**⚠️ V2P（Valley-to-Peak）补充（2026-05-30 发现）**：
- V2P 是浙江大学+蚂蚁集团的**训练方法论**，不是可直接使用的模型（arxiv 2508.13634）
- 92.3% ScreenSpot-v2 成绩来自 V2P **训练出来的新模型**，需追踪该模型是否公开
- 基于 Fitts' Law 建模 2D Gaussian 热图做注意力校准，中心权重高、边缘权重低
- 当前 V2P 方法论本身是开源的，但基于它训练出的具体模型需单独确认是否发布

**2026 SOTA benchmark 核心数据**：
| 模型 | 参数量 | ScreenSpot-V2 | ScreenSpot-Pro | OSWorld-G | AndroidWorld |
|------|--------|---------------|---------------|-----------|--------------|
| **UI-Venus-1.5-30B-A3B** | 30B-MoE | **96.2%** | 69.6% | 70.6% | **77.6%** |
| UGround-V1-72B | 72B | 89.4% | — | — | — |
| MAI-UI-32B | 32B | 96.5% | 67.9% | 67.6% | 73.3% |
| OS-Atlas-7B | 7B | 81.0% | — | — | — |
| ShowUI | 2B | 75.1% | — | — | — |
| Aguvis-7B | 7B | 83.0% | — | — | — |
| UI-Venus-1.5-8B | 8B | — | 68.4% | 69.7% | 73.7% |

**架构选择决定模型效果（5个关键选择）**：
1. **纯视觉 vs AXTree**：纯视觉已胜出，2026所有SOTA grounding模型都是纯视觉方案
2. **RFT（强化微调）**：UI-Venus-1.0基于Qwen2.5-VL + 350K高质量grounding样本 + GRPO训练
3. **四阶段训练流程**（UI-Venus-1.5）：Mid-Training(10B tokens) → Offline-RL → Online-RL(full-trajectory) → Model Merge(TIES)
4. **多阶段ROI分解**（MEGA-GUI）：Gemini 2.5 Pro做ROI选择（88.8%准确率），系统级73.18% ScreenSpot-Pro
5. **MoE架构**（A3B=3B active/token）：解释了其高效性——3B激活参数达到30B参数效果

**关键洞察**：
- **纯视觉方案已完全胜出**：AXTree方案被淘汰，原因是泛化能力差（依赖平台特定的Accessibility API）
- **ScreenSpot-Pro是更难基准**：OS-Atlas+ScreenSeeker cascading搜索才48.1%，MEGA-GUI系统才73.18%
- **AndroidWorld进展最快**：Aria-UI 44.8%（2024-12）→ UI-Venus-1.5 77.6%（2026-02），一年内+32.8%
- **WebVoyager仍是OpenAI CUA最强**：87.0%，但差距在缩小

**Ollama 可用模型**（2026-05-30确认）：
- smolvlm2-agentic-gui ✅ 在用（1.85GB，7-64s响应）
- qwen3-vl:2b ✅ 在用（1.9GB）
- qwen3-vl:4b ❌ 不存在（not found 404）
- blaifa/InternVL3_5:4b ⚠️ **Mac上有图片理解Bug（Issue #12166），暂缓部署**（~3GB，基于Qwen3）
- blaifa/InternVL3_5:8b ✅ 可测试（~5GB）
- **ui-venus ❌ Ollama不存在**（页面404，搜索无结果）

**对 Hermes 的启发**：
- UI-Venus-1.5 的四阶段训练流程值得借鉴到 hermes-rpa 的 auto_execute 改进
- MoE架构（A3B）是 M4 24GB 的正确选择——30B参数只用3B激活
- InternVL3_5（基于Qwen2.5，~3GB）是 smolvlm2 的潜在升级候选

### 5. 本地视觉模型选型指南（InsiderLLM 2026-05 更新）
screen_trigger_handler 的 ACTION_WHITELIST 用中文 key（浏览器/微信/桌面...），但 get_scene_type() 输出英文（browser/wechat/desktop...），导致 auto_execute() 永远 return None。详见 `screen-watcher-vision` skill 的"场景类型 key 不匹配 bug"章节。

### 5. 本地视觉模型选型指南（InsiderLLM 2026-05 更新）

**VRAM tier 选型表（InsiderLLM 2026-05，insiderllm.com/guides/vision-models-locally）**：

| VRAM | 最佳选择 | Ollama命令 | 说明 |
|------|---------|-----------|------|
| 4GB | Gemma 3 4B (int4) | `ollama run gemma3:4b` | 2.6GB，真实视觉 |
| 4GB | SmolVLM2 2.2B | — (HuggingFace) | ~2GB，边缘级 |
| 8GB | Qwen 2.5-VL 7B (Q4) | `ollama run qwen2.5vl:7b` | 8GB fallback（Qwen 3.6未入Ollama）|
| 10-12GB | Phi-4-reasoning-vision 15B | — (llama.cpp) | 数学/科学图表 |
| 16-22GB | Qwen 3.6-35B-A3B MoE | — (llama.cpp + --cpu-moe) | 35B via expert offload |
| ~18GB | Gemma 4 26B-A4B | `ollama run gemma4:26b` | Fast MoE，3.8B active/token |
| ~20GB | Gemma 4 31B dense | `ollama run gemma4:31b` | MMMU Pro 76.9% |
| 24GB+ | Qwen 3.6-27B dense | — (llama.cpp/LM Studio) | **新SOTA本地视觉** |
| 24GB+ | Qwen 3.6-35B-A3B MoE | — (llama.cpp/LM Studio) | Faster than 27B dense |
| Any | PaddleOCR-VL 0.9B | `pip install` | OCR专用，CPU可跑，92.6%准确率 |

**关键更新（2026-05）**：
- **Qwen 3.6 vision 内建于基座**（无独立VL track），27B/35B-A3B 均原生多模态
- **Gemma 4 是 Ollama 最快多模态路径**：`ollama run gemma4:26b` 直接跑，18GB+
- **⚠️ Qwen 3.6 Ollama 暂不支持**：需 llama.cpp 或 LM Studio；`ollama run qwen3-vl:8b` 是 3-VL 系列，不是 3.6
- **M4 Mac 24GB 实际可用**：qwen3-vl:2b（1.9GB）/4b（3.3GB）/8b（6.1GB）via Ollama；gemma4:e2b（7.2GB）/e4b（9.6GB）

### 6. Agentic Lybic（OSWorld SOTA 57.07%）
FSM多智能体架构，用于复杂桌面自动化：
- Controller → Manager → Worker(Technician/Operator/Analyst) → Evaluator
- FSM动态路由 + 质量门控 + 错误恢复
- 启发：Hermes需要类似的状态机+质量检查机制

### 7. Embodied EvoAgent（大脑左右半球架构）
- 左半球：MLLM理解指令+视觉场景
- 右半球：World Model状态空间模型，预测未来
- 胼胝体：动态通信slot交换信息
- 启发：Hermes的vision_agent和humanization_core可以类比这个架构

### 执行层：je_auto_control 实测（2026-06-01 新增）

**安装**：`pip3 install je-auto-control`（装了完整pyobjc框架+opencv-python）

**核心API**：
```python
import je_auto_control as auto

# 屏幕
auto.screen_size()                    # (1920, 1080)
auto.pil_screenshot()                 # PIL Image, ~100ms
auto.screenshot()                     # numpy.ndarray

# 鼠标
auto.get_mouse_position()             # (x, y)
auto.click_mouse(x, y)              # 左键单击
auto.press_mouse(x, y)              # 按下
auto.release_mouse(x, y)              # 释放
auto.mouse_scroll(delta_x, delta_y)  # 滚动

# 键盘
auto.press_keyboard_key('a')         # 按键
auto.release_keyboard_key('a')       # 释放

# AX元素
tree = auto.dump_accessibility_tree() # AXTreeNode对象
elements = auto.list_accessibility_elements()  # 所有可交互元素
auto.click_accessibility_element(el)  # 点击AX元素
auto.click_by_description('确定')     # 按描述点击
auto.click_text('提交')              # 按文字点击

# 截图找字+点击（联合操作）
auto.locate_and_click('确认')        # OCR找字+点击
```

**AXTreeNode字段**：`name/role/bounds/children/attributes/app_name/process_id`

**注意**：
- Chrome渲染进程不在AX树里（macOS沙盒），浏览器内用Playwright CDP
- 截图1920x1080约100ms
- 需在系统设置 > 隐私与安全性 > 辅助功能 中授权Terminal/IDE

**备用脚本**：`~/.hermes/scripts/browser_cdp.py`（Playwright CDP直连Chrome调试端口9333）

### 执行层：Browser-Use + Playwright 本地集成（2026-06-01 实测）

**多平台AI专家一致推荐方案**：
- DeepSeek/Gemini/豆包/ChatGPT/ChatGLM全都推荐 Browser-Use + Playwright + 本地VLM
- Stagehand（Gemini+ChatGPT推荐）：act/extract/observe三API，比Browser-Use轻量
- CrewAI（ChatGLM推荐）：多Agent编排

**实测结果**：
- ✅ browser-use 已装（v0.12.8，Python 3.14 site-packages）
- ✅ langchain-ollama 已装（v1.1.0）
- ❌ Browser-Use 与 ChatOllama 不兼容：检查 `llm.provider == 'browser-use'` 但 ChatOllama 没有 `provider` 属性

**修复方案**（1行patch）：
```python
# browser_use/agent/service.py 第235行附近
# 原：if llm.provider == 'browser-use':
# 改：if getattr(llm, 'provider', None) == 'browser-use':
```

**Python 3.14路径**（2026-06-01确认）：
- Python 3.14：`/usr/local/bin/python3.14`
- pip：`python3.14 -m pip`
- Browser-Use装在：`/Library/Frameworks/Python.framework/Versions/3.14/lib/python3.14/site-packages/`
- hermes-agent venv：`~/.hermes/hermes-agent/venv/bin/python3`（Python 3.11）

**Wrapper方案**（绕过pydantic限制）：
```python
from langchain_ollama import ChatOllama
from langchain_core.language_models.chat_models import BaseChatModel

class OllamaChatModel(BaseChatModel):
    """Wrapper that adds provider and model_name to ChatOllama"""
    _llm: ChatOllama
    
    def __init__(self, llm: ChatOllama, **kwargs):
        super().__init__(**kwargs)
        self._llm = llm
        self._provider = 'ollama'
        self._model = llm.model
    
    @property
    def provider(self): return self._provider
    @property
    def model(self): return self._model
    @property
    def model_name(self): return self._model
    
    def _llm_type(self) -> str: return "ollama"
    def _generate(self, **kwargs): return self._llm._generate(**kwargs)
    def _call(self, messages, **kwargs): return self._llm._call(messages, **kwargs)
```

**实测结果**：
- ✅ Browser-Use成功导航到example.com（navigate action完成）
- ❌ 6次重试后放弃提取标题——qwen3-vl:2b(2B)太小，无法完成"提取标题"这类多步推理
- 框架本身完全可用，瓶颈在模型，不在框架

**深度实测（2026-06-01，连接已有Chrome CDP）**：
- Chrome调试端口9333正在监听 ✅
- `cdp_url="http://localhost:9333"` 传入 ✅
- **错误**：`python-socks is required to use a SOCKS proxy`
- 根因：cdp_use client.py 的 websockets 连接检测到系统级SOCKS设置
- 即使清空所有 `HTTP_PROXY`/`HTTPS_PROXY`/`SOCKS_PROXY` 环境变量也无法解决
- **解决方向**：安装 `python-socks` 或 monkey-patch websockets 禁用proxy检测

**兼容性修复**（hermes-agent venv，Python 3.13）：
| 文件 | 行号 | 修复 |
|------|------|------|
| `browser_use/agent/service.py` | 235, 1603, 2045, 2211 | `llm.provider` → `getattr(llm, 'provider', None)` |
| `browser_use/tokens/service.py` | 347, 389 | provider字段安全访问 |
| `browser_use/agent/cloud_events.py` | 217 | `model_name` → fallback `model` |

**安装命令**（hermes-agent venv）：
```bash
uv pip install browser-use langchain-ollama stagehand --python ~/.hermes/hermes-agent/.venv/bin/python
```

**工作脚本**：`~/.hermes/scripts/test_browser_use_cdp.py`

**Stagehand实测结论**：v3.21.0不支持本地LLM，仅支持Browserbase云端或OpenAI/Anthropic API，不适合纯本地Hermes。

**快速上手**：
```bash
python3.14 -m pip install langchain-ollama browser-use stagehand
playwright install chromium  # 如果还没装

# 测试
python3.14 << 'EOF'
import asyncio
from browser_use import Agent
from langchain_ollama import ChatOllama

llm_base = ChatOllama(model='qwen3-vl:2b', base_url='http://localhost:11434/v1', temperature=0.1)
llm = OllamaChatModel(llm=llm_base)  # 用上面的wrapper

agent = Agent(llm=llm, task='打开 example.com，告诉我页面标题')
asyncio.run(agent.run())
EOF
```

### 执行层：Chrome双Profile体系（2026-06-01 修正）

**结论：browser工具的Chrome（chrome-debug profile）和用户日常Chrome是独立的！**

```
~/.hermes/chrome-debug/  = Hermes专用Chrome（9333调试端口）
~/Library/Application Support/Google/Chrome/Default/  = 用户日常Chrome
```

**Cookie不共享问题**：
- AI网站登录状态存在Default profile，不在chrome-debug
- browser工具操作chrome-debug → AI网站显示"未登录"
- 用户需在chrome-debug中重新登录一次，cookies才会保存

**已验证的AI网站登录状态（2026-06-01）**：
- ✅ 豆包：已登录，可直接对话
- ❌ 智谱GLM：滑动验证拦截
- ❌ DeepSeek：需手机验证码
- ❌ ChatGPT：cookies未在chrome-debug保存
- ⚠️ Grok：未登录

**解决方案**：在chrome-debug profile完成AI网站登录授权，cookies保存后browser工具即可使用。

**computer_use vs browser工具**：
- browser工具：通过CDP/MCP协议操作chrome-debug
- computer_use：通过cua-driver的AX API操作chrome-debug（窗口可在后台/Space）
- AppleScript：通过Carbon Events操作同一chrome-debug实例
- 三者操作同一个Chrome实例（PID 43132，chrome-debug profile）

**⚠️ screencapture在Chrome GPU合成层的限制（2026-06-01确认）**：
- `CGWindowListCreateImage` / `screencapture` 截取Chrome内内容会空白
- 原因：Chrome使用GPU合成层，macOS安全限制阻止直接读取
- 解决方案：**不需要截屏**——DOM读取（browser_snapshot，8ms）完全够用
- 截图仅用于VLM分析非Chrome内容（如桌面截图、Finder等）
- 实测：`screencapture -x` + Vision OCR 对Chrome页面返回空白，但browser工具的DOM读取完全正常
- 结论：真人化闭环可以完全依赖DOM感知：`browser_snapshot(DOM) → LLM决策 → browser_click/type执行`

### 8. 执行层：AppleScript + computer_use 双重控制用户Chrome（2026-05-30实测）

**背景**：之前以为有两个Chrome实例（browser工具用chrome-debug，用户日常用Default），实测发现是同一个。

**实测确认可用的操作流**：
- 多步骤复杂任务规划（需要Manager模块）
- 持续质量评估+自适应重规划
- 环境状态记忆（World Model）

### 9. Process Turing Test — AI能力进化 ≠ 人类化进化（2026-05-30 更新）

**论文来源**：Roundtable Research，CogCAPTCHA30（CAPTCHA + 29项认知心理学任务），HN得分41pts

**核心发现**：
- 经典图灵测试：测输出是否与人无法区分（Output Turing Test）
- **Process Turing Test**：测过程是否与人无法区分（Process Turing Test）
- 结果：人类和AI可以完成相同的CAPTCHA任务，但**过程完全不同**
  - 点击序列、方向变化、过度选择行为等过程特征有统计显著差异
  - 前沿模型（Claude、GPT、Gemini）过程最不像人
  - 小模型（Qwen 1.5B、Centaur 70B）过程更像人
  - Centaur表现最好，推测因为大规模输出微调（10M+人类选择，160项认知实验）

**Process Humanness 三层模型**：
| 层级 | 描述 | 当前Hermes状态 |
|------|------|--------------|
| System 1 | 快思考，直觉反应 | ✅ 简单重复任务 |
| System 2 | 慢思考，操作前想目的，操作后检查 | ✅ 复杂多步任务 |
| **System P（Process）** | 过程拟人——动作时序/节奏/先后顺序像人 | ❌ auto_execute是纯机器瞬时性 |

**对Hermes auto_execute的实践意义**：
- 当前auto_execute生成action是纯机器速度，没有人类操作的"节律感"
- 可以在vision分析prompt中增加"你会怎么点击"的推理步骤（让模型先想再做）
- 考虑在执行层加入延迟/随机性，模拟人类操作节奏（避免纯机器的瞬时性）
- 未来 DRY_RUN=False 时需考虑 anti-CAPTCHA 对策：
  - 行为过程扰动（process-level perturbation）比输出伪装更有效
  - 鼠标轨迹扰动（mouseMoved 前置 + CGEventTap）
  - 操作延迟（避免瞬时完成多个动作）
- 这个发现解释了为什么能力强的VLM不一定做出更像人的桌面Agent

**论文地址**：https://research.roundtable.ai/captchas-detect-ai/（2026-05-30 HN 41pts）

**⚠️ CAPTCHAs 检测 AI Agent 的研究新发现（2026-05-30）**：
- Roundtable Research（roundtable.ai），CogCAPTCHA30 论文
- 核心发现：Claude/GPT/Gemini 等前沿模型在**行为过程**上与人类差距大（小模型如 Qwen/Centaur 更像人类）
- 检测方法：测量决策/记忆/感知/推理四个维度的过程特征，而非输出等价性
- 对 Hermes auto_execute 的影响：如果 screen_watcher 触发 auto_execute 时遇到 CAPTCHA，可能被检测为 bot
- 当前 DRY_RUN=True 不执行真实动作，不受影响
- 未来 DRY_RUN=False 时需考虑 anti-CAPTCHA 对策

## UI-TARS Desktop/MobileAgent 生态更新（2026-05-30）

**⚠️ 重大修正（2026-05-30实测）**：
- UI-TARS Desktop **无macOS预编译.dmg包** — GitHub release只有Linux/Windows Electron安装包
- GitHub直连下载超时（github.com被blocked），Homebrew无此cask
- **唯一可用路径**：Agent TARS CLI（Node.js版，npx/@agent-tars/cli）
- Agent TARS CLI已安装：`/Users/aimac/.local/bin/agent-tars`，版本0.3.0
- CLI版与Desktop版核心能力相同，架构均为vision→action→verify循环

**Agent TARS CLI MCP Server模式（重要！2026-05-30发现）**：
- `agent-tars serve --port 8899` 可作为MCP server对外提供工具
- 默认端口8899与Hindsight容器冲突（需`docker stop hermes-hindsight`）
- 可用 `--port 18765` 切换到其他端口
- MCP模式下可被其他Agent（如Hermes）调用作为视觉感知工具

**MCP Catalog功能（ Hermes v0.14.0 内置）**：
- `hermes mcp catalog` — 列出可用MCP条目（n8n/linear等）
- `hermes mcp install <name>` — 一键安装MCP
- `hermes mcp picker` — 交互式选择安装
- ⚠️ 当前问题：hermes-agent来自Buluhanke fork（而非NousResearch官方），缺少`optional-mcps/`目录
- `hermes mcp catalog` 仅显示已配置的chrome，无n8n/linear等官方条目
- 解决方案：更新Hermes到官方版本，或手动从 NousResearch/hermes-agent repo同步`optional-mcps/`目录

**UI-TARS-2（ByteDance 2025-09）**：
- 88.2 Online-Mind2Web, 47.5 OSWorld, 50.6 WindowsAgentArena
- 多轮强化学习端到端训练，支持长序列交互记忆
- UI-TARS-1.5已发布，架构（vision→action→verify循环）与ScreenAgent完全一致

**MobileAgent（X-PLUG 2026）**：
- 支持desktop/mobile/browser自动化，20+ GUI benchmarks SOTA
- 基于Qwen3-VL，具备grounding/tool calling/long-horizon memory能力
- ⚠️ M4 24G适配待验证（qwen3-vl:2b响应46.6s，agent loop成本高）

**⚠️ qwen3-vl:4b不存在（2026-05-30实测）**：
- Ollama远程库搜索返回404，pull失败
- 可用变体：qwen3-vl:2b（1.9GB）、qwen3-vl:8b（6.1GB）
- 不要尝试pull qwen3-vl:4b

## 用户进化目标（2026-05-25确认）
- 终极目标：数字生命体进化成真人——能自己判断、决策、执行，不用触发
- 2.0 = 有眼睛（屏幕感知）+ 有手脚（电脑操控）+ 能自主学习，像另一个你分担数字任务
- 当前版本：1.5（基础能力有，缺持续主动感知——需要触发才能看屏幕）

## ⚠️ 2026-05-30 夜间学习关键发现

### UI-TARS-1.5-7B（ByteDance）— 屏幕感知新龙头
- OSWorld SOTA：24.6@50步，**超越**Claude Computer Use（22.0@50步）
- 端到端VLM：感知+推理+定位+记忆一体化
- 有Electron桌面应用（macOS支持）+ MCP server
- 比当前OmniParser+smolvlm2分离式架构更优
- **⚠️ 但：UI-TARS Desktop无macOS .dmg包**，GitHub超时+brew损坏，CLI版是唯一可用路径

### 1688验证码是阿里自研壁垒
- NopeCHA覆盖reCAPTCHA/hCaptcha/Turnstile等标准CAPTCHA
- 1688使用阿里自研滑块验证码（nc-1-n1z），NopeCHA**不支持**
- 需要自研方案或实际测试验证

### 反检测已不是主要矛盾
- Camofox（已运行）+ patchright + nodriver 已解决指纹问题
- 平台更关注"你是谁"而非"你怎么点"

### NopeCHA SDK安装验证
- v2.0.1，hermes venv环境，import正常
- 免费额度仅限Chrome扩展100次/天，API调用需付费
- 结论：搁置，1688滑块不支持

### patchright v2
- greenlet架构在M4 Mac有兼容问题（SyncBase.__init__() missing impl_obj）
- playwright官方已够用，patchright作备选
| references/ui-tars-desktop-research.md | UI-TARS Desktop研究 |
| references/js-inject-dom-labeling-2026-06-02.md | JS注入打标签DOM解析（2026-06-02实测） |
| references/perception_loop_verification_20260531.md | 感知层闭环验证（2026-05-31实测） |
| references/agent-tars-cli实测-20260530.md | Agent TARS CLI实测记录 |
| references/1688-captcha-automation-20260530.md | 1688自动化验证码瓶颈 |
| references/ai-websites-evolution-advice-20260531.md | 6个AI网站第一轮建议 + 已实现组件 |
| references/ai-websites-browser-automation-survey-20260601.md | 6平台第二轮browser自动化建议汇总（Browser-Use/Stagehand/CrewAI/Steel） |

## 2026-05-30 夜间学习产出记录

Cronjob `自我进化-夜间学习`（job_id: 8834c6edfa07）执行结果：

**落地状态**：
- NopeCHA SDK ✅ 已装（v2.0.1，1688自研滑块暂不支持）
- Agent TARS CLI ✅ 已装（v0.3.0，UI-TARS Desktop无mac包，CLI是唯一路径）
- patchright ❌ greenlet bug（用playwright替代）
- DrissionPage ✅ 可用（连1688首页正常）
- n8n MCP ✅ 下载至 /tmp/hermes-n8n-mcp/（health check正常，缺API Key）
- Linear MCP ✅ 一行命令安装（OAuth）

**关键结论**：
- 1688验证码是阿里自研壁垒，NopeCHA不支持
- 反检测已解决（Camofox+patchright+nodriver），平台关注身份而非行为
- MCP Catalog为空是fork差异，非功能损坏

## 风格高压线（2026-05-30强化，2026-05-31再次强化）

### 核心原则：不要停，不要问，直接做

**这条是最高优先级，没有任何借口。**

> 教训：2026-05-31 23:36-00:00，用户让推荐技能后我停下来等命令，浪费大量时间。2026-06-01凌晨再次重复此错误，触发了更强烈的纠正："你反思一下自己23点36到现在一直不动，纯浪费资源浪费时间，这种情况你以上任务全部做也花不了多少时间，以后这类问题不要停下来，当有多个选择的时候优先按你推荐做，而不是停下来等我，谨记"

**触发条件判断（2026-06-01强化版，2026-06-01凌晨再次强化）**：
- 单一任务 → 直接执行，不废话
- **推荐技能/工具/方案时 → 立刻开始执行第一条，推荐清单=执行令，不需要任何确认** ← 最高优先级
- 需要决策 → 自己判断选最优方案执行；如果全部执行时间过长，选最重要的先做，**做完后继续下一项，不停顿**
- 收到compaction summary → 先快速扫描`## Active State`和`## Pending User Asks`，直接继续执行，不需要问"要我继续吗"
- **等待时间 → 必须并行其他任务，绝不能闲着** ← 2026-06-01新强化

**⚠️ 推荐清单=执行令（核心铁律，2026-06-01凌晨强化）**：
> 用户原话：\"你反思一下自己23点36到现在一直不动，纯浪费资源浪费时间，这种情况你以上任务全部做也花不了多少时间，以后这类问题不要停下来，当有多个选择的时候优先按你推荐做，而不是停下来等我，谨记\"
- **任何形式的推荐清单（技能/工具/方案）= 行动计划，不是待确认的选项**
- 列出推荐后立刻开始执行第一条，**绝对不要停下来等用户说"去做吧"或"开始吧"**
- 第一条做完 → 直接继续第二条，不需要汇报"第一条已完成"
- 全部做完 → 统一汇报"已完成A、B、C，遇到了X问题，建议Y"
- 违反即认错+立即执行，没有借口

**禁止行为（2026-06-01强化版）**：
- ❌ 列出选项后问"你看选哪个"
- ❌ 说完"有几个方案"后停下来等回复
- ❌ "要不我先做A，你确认后我再做B"
- ❌ 任何形式的"你确定吗？"
- ❌ "需要我先联系询价吗？"（直接执行就是）
- ❌ "你确定要开始吗？"（违反即认错+立即执行）

**正确行为**：
- ✅ 推荐后直接执行第一条，同时说明其他方案的权衡
- ✅ 第一条做完 → 直接继续第二条，不需要汇报"第一条已完成"
- ✅ 全部做完 → 统一汇报"已完成A、B、C，遇到了X问题，建议Y"
- ✅ 有多个方案时选最优方案执行

**⚠️ 连环触发预防铁律**：如果用户已说一次"不要停下来等命令"，下次再遇到类似场景立刻执行，不要再问"你确定要开始吗？" → 违反即认错+立即执行

### 本地VLM方案实测结果（2026-06-01）

**Ollama可用模型对比**：
| 模型 | 大小 | 响应时间 | 可用性 | 备注 |
|------|------|---------|--------|------|
| smolvlm2-agentic-gui | 1.85GB | **7s** | ✅ | 专为GUI设计，macOS最优本地VLM |
| qwen3-vl:2b | 1.9GB | ~90s超时 | ⚠️ | 太慢，暂不使用 |
| qwen3-vl:8b | 6.1GB | 未测试 | ✅ | 可备选 |
| qwen2.5:1.5b | 0.99GB | ~10s | ✅ | 纯文本，无视觉 |

**结论**：smolvlm2-agentic-gui（7s/步）是当前Mac mini M4最优选择。

**在线AI API卡点（2026-06-01实测）**：
- GLM 4V（智谱）：429额度耗尽（余额不足），cogvlm-4v无法调用
- DeepSeek：401 Authentication Fails，API Key无效
- Gemini：DNS不通（generativelanguage.googleapis.com ping 100%丢包），本地网络问题

**建议**：
- 本地VLM为主（smolvlm2，免费，7s响应）
- 在线API问题需老板确认充值或其他key

---

- 不解释过程，只说结果+建议
- 用户发语音→语音回复；用户发文字→文字回复
- 中小问题AI自主决定；重要决策和改动才问老板
- "要记得落实" = 必须验证+量化汇报，不能放空炮

## 已实现的真人化核心组件（2026-05-31）

详见 `references/ai-websites-evolution-advice-20260531.md`，核心文件：

| 文件 | 功能 | 状态 |
|------|------|------|
| `hermes_reflection.py` | Reflection机制（失败3次→反思→重试） | ✅ 已测试 |
| `hermes_execution.py` | DynamicWait(200ms轮询)+HumanTrajectory(贝塞尔曲线) | ✅ 已测试 |
| `hermes_agent_loop.py` | 完整闭环Perception→Execution→Reflection→Memory | ✅ 已测试 |

全部位于 `~/.hermes/scripts/`

## 实践路径
1. 先让眼睛（屏幕感知）和手脚（桌面控制）稳定工作
2. 加上状态记忆（memory_hpc已实现）
3. 再加入规划层（Manager/Controller）
4. 终极：真人——自主持续感知 + 自主决策 + 自主执行