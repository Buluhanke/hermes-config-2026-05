# 6平台AI Browser Automation 建议汇总（第二轮，2026-06-01）

## 调研背景
向6个AI对话网站发送查询："hermes的browser工具还有更好更智能的推荐"
目标：收集多平台对Hermes真人化browser自动化的最佳方案建议

## 各平台回复

### ✅ DeepSeek（Tab 0）
**方案：三路径 + Steel云端**

1. **@hasna/computer**（最推荐）
   - npm包，开箱即用，零配置
   - 支持多浏览器（Chrome/Firefox/Edge）
   - 内置重试+截图+等待

2. **Mano-P + Qwen**（隐私离线）
   - 本地模型，隐私优先
   - Qwen做推理，本地浏览器控制

3. **je_auto_control**（AX定位+OCR）
   - 已有完整pyobjc/opencv
   - AX元素定位+截图OCR

**额外建议：**
- **Steel云端浏览器**（反爬最强）
- **Browse.sh**（250+预置技能，本地Chrome CDP配置，YAML示例）

### ✅ Gemini（Tab 2）
**方案：Browser-Use + Stagehand + OmniParser + Playwright**

| 工具 | 特点 |
|------|------|
| **Browser-Use** | GitHub最火，AI驱动浏览器自动化 |
| **Stagehand** | act/extract/observe三API，企业级 |
| **OmniParser** | 纯视觉方案，学术前沿 |
| **Playwright** | 底层驱动，配合VLM使用 |

**安装命令：**
```bash
pip install browser-use playwright
playwright install chromium
```

### ✅ 豆包（Tab 3）
**方案：Browser-Use + Qwen3-V-14B本地VLM**

- **Browser-Use + Qwen3-V-14B**：全能型本地VLM
- **Camofox**：本地Firefox指纹伪装
- **本地CDP**：已有（Chrome 9333端口）
- **Stagehand企业级**：含安装命令和代码示例

**安装命令：**
```bash
pip install browser-use playwright
playwright install chromium
ollama pull qwen3-v:14b
```

### ✅ ChatGLM（Tab 5）
**方案：CrewAI + Playwright + 本地LLM**

架构：
```
Hermes AI Agent (CrewAI 编排层)
  → Planner Agent（规划）
  → Browser Agent（执行，Playwright）
  → Validator Agent（验证）
  → 本地LLM（Ollama/Llama3/Qwen2）
```

CrewAI封装了Playwright，提供Agent/Task/Crew/Process抽象。

### ❌ ChatGPT（Tab 4）
- cookies/session不足
- 显示"lukebu"但无对话能力
- 未能发出查询

### ⚠️ Grok（Tab 1）
- 超时未响应
- 可能需要注册登录

---

## 推荐方案排序（综合6平台）

| 排名 | 方案 | 推荐平台 | 核心工具 |
|------|------|----------|----------|
| 🥇 | **Browser-Use + Playwright + 本地VLM** | Gemini/豆包/DeepSeek | browser-use, playwright, smolvlm2 |
| 🥈 | **CrewAI + Playwright** | ChatGLM | crewai, playwright |
| 🥉 | **Stagehand** | Gemini/豆包 | stagehand（act/extract/observe） |
| 4 | **Steel云端** | DeepSeek | Steel浏览器（反爬最强） |
| 5 | **OmniParser纯视觉** | Gemini | 学术前沿方案 |
| 6 | **@hasna/computer** | DeepSeek | npm零配置 |

---

## Hermes已实现组件（对照建议检查）

| 组件 | 对应建议 | 状态 |
|------|----------|------|
| je_auto_control | DeepSeek三路径之一 | ✅ 已装（pip3 install je-auto-control） |
| Playwright CDP | Browser-Use底层驱动 | ✅ 已验证可用 |
| smolvlm2本地VLM | 豆包推荐Qwen3-V-14B替代 | ✅ 已装（Ollama） |
| browser_cdp.py | DeepSeek本地CDP | ✅ 已创建备用脚本 |
| cliclick | DeepSeek推荐 | ✅ 已装 |
| Reflection机制 | 失败自愈 | ✅ hermes_reflection.py |
| DynamicWait | 等待优化 | ✅ hermes_execution.py |
| HumanTrajectory | 贝塞尔曲线防检测 | ✅ hermes_execution.py |
| AgentLoop | 完整闭环 | ✅ hermes_agent_loop.py |

---

## 下一步建议

1. **优先集成Browser-Use** — 多个平台一致推荐，GitHub最火
2. **测试CrewAI编排层** — ChatGLM方案，可作为Hermes的任务规划层
3. **Stagehand备选** — 企业级稳定性，act/extract/observe三API
4. **Chrome登录状态修复** — ChatGPT需要重新在chrome-debug profile授权

---

## 文件位置
- 本归档：`~/Brain_Lab/ai_agent_browser_automation_survey.md`
- Hermes脚本：`~/.hermes/scripts/hermes_agent_loop.py`
- 备用CDP：`~/.hermes/scripts/browser_cdp.py`
