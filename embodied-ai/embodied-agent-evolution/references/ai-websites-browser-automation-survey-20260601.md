# 6平台Browser自动化方案调研（2026-06-01）

## 调研方法
同时向6个AI网站发送同一问题：
> "推荐当下最好最智能的browser自动化方案给Hermes AI Agent，可结合本地模型"

## 各平台回复汇总

### DeepSeek（✅ 6946字，完整）
**推荐排序**：
1. **Steel云端**（反爬最强）：`api.steel.dev`，住宅代理+隐身模式
2. **Browse.sh 250+技能**：预置浏览器技能库，开箱即用
3. **本地Chrome CDP**：零成本，隐私最强
4. **Camofox**（Firefox指纹伪装）：反爬+本地

### Gemini（✅ 1646字，完整）
1. **Browser-Use**（GitHub最火）：自动提取可交互元素打标签，降低本地模型推理负担
2. **Stagehand**（开发者API）：act/extract/observe三动作，极简抽象
3. **OmniParser + Playwright**：纯视觉方案，截图+UI元素检测

**关键洞察**：
- AXTree > 原始HTML
- 配合Readability.js提取正文，减少上下文长度
- 给控制上下文长度

### 豆包（✅ 3828字，完整）
**2026最佳性价比组合**：
1. **Browser-Use + Playwright + Qwen3-V-14B（本地）**
2. **Camofox + Hermes内置浏览器**
3. **本地Chrome CDP + Hermes + Ollama**
4. **Browserbase/Stagehand + 本地LLM**（企业级）

**最终推荐排序**（按"智能+本地+稳定"）：
1. Browser-Use + Playwright + 本地VLM — 全能、最智能
2. Camofox + Hermes内置 — 反爬最强、配置极简
3. 本地Chrome CDP + Ollama — 零成本、最安全
4. Browserbase/Stagehand — 企业级、高稳定

### ChatGPT（✅ 2316字，手动登录后）
**推荐架构**：
```
Qwen3 8B → Hermes Planner → Long Memory → Stagehand + Playwright → Chrome
                    ↓
            OmniParser + RapidOCR
                    ↓
              Perception
```

**核心建议**：Stagehand + Playwright + 本地Qwen3 8B是目前最接近"像人操作浏览器又不会天天失控"的方案。

### ChatGLM（✅ 2388字）
**CrewAI + Playwright方案**：
- Planner Agent：本地LLM分析任务
- Browser Agent：Playwright执行
- Validator Agent：检查结果

```python
from crewai import Agent, Task, Crew, Process
from langchain_ollama import ChatOllama

local_llm = ChatOllama(model="llama3", base_url="http://localhost:11434")
agent = Agent(llm=local_llm, task="...")
```

### Grok（⚠️ 585字，未发送成功）
未成功发送查询，内容参考价值有限。

## 跨平台共识

| 方案 | 推荐次数 | 来源 |
|------|---------|------|
| Browser-Use + Playwright | 4次 | DeepSeek/Gemini/豆包/ChatGLM |
| Stagehand | 2次 | Gemini/ChatGPT |
| 本地VLM（Qwen3） | 4次 | 全部推荐本地模型 |
| Steel/Camofox（反爬） | 2次 | DeepSeek/豆包 |
| CrewAI | 1次 | ChatGLM |

## 落地优先级

1. **Browser-Use**（已有，需修1行兼容性）
2. **Playwright CDP直连**（已有browser_cdp.py，完全可用）
3. **Stagehand**（act/extract/observe三API，比Browser-Use轻量）
4. **CrewAI**（多Agent编排，适合复杂任务）