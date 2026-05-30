# AI网站真人化建议汇总（2026-05-31凌晨）

## 平台访问结果

| 平台 | URL | 状态 | 备注 |
|------|-----|------|------|
| Gemini | gemini.google.com | ✅ 已登录 | 成功获取完整建议 |
| 豆包 | doubao.com | ⚠️ 已登录 | 响应待验证 |
| 智谱GLM | chatglm.cn | ❌ | 滑动验证拦截 |
| DeepSeek | chat.deepseek.com | ❌ | 手机验证码登录 |
| ChatGPT | chatgpt.com | ❌ | Cloudflare人机验证 |
| Grok | grok.com | ⚠️ 未登录 | 显示注册页面 |

## Gemini核心建议（最完整）

### 1. 思考层（Brain）
- **主力推理**: DeepSeek-R1（官方API/SiliconFlow免费额度）
- **多模态视觉**: Qwen2.5-VL 或 Llama-3.2-Vision (11B) via Ollama
- **用途**: 复杂Mac操作深度规划 + 视觉双重校验

### 2. 感知层进化
- **混合感知**: AX Tree（结构）+ 视觉Bounding Box（画面）
- **工具**: OmniParser（微软开源）屏幕切分
- **降级策略**: AX Tree找不到 → 立即切换视觉检测

### 3. 执行层进化
- **动态等待**: 200ms循环监听AX节点变化，非固定sleep
- **人类轨迹**: 贝塞尔曲线鼠标移动 + 随机输入速度
- **效果**: 绕过90%风控检测

### 4. 记忆与反思层
- **Reflection机制**: 连续失败 → 暂停 → 打包截图+AX喂给R1反思
- **微型SOP库**: Hindsight经验 → 几十Token的SOP小贴士

### 5. 工程建议
- **参考**: OSWorld/UFO开源代码处理边缘情况
- **M4算力分配**: 80%内存给Qwen2.5-VL做视觉，逻辑推理API调用

### 总结
> DeepSeek-R1做灵魂 + 本地视觉做眼睛 + 8ms AX Tree做神经 + Hindsight做经验书

## 已实现的核心组件

### 1. hermes_reflection.py
```
ReflectionMonitor: 失败计数 → 触发反思
ReActLoop: think/act/observe/reflect 历史追踪
quick_reflect: 快速反思入口
```
**核心流程**: 连续3次失败 → 截图+AX Tree → 反思Prompt → LLM分析 → 修正 → 重试

### 2. hermes_execution.py
```
DynamicWait: 200ms轮询间隔，条件满足即返回
HumanTrajectory: 贝塞尔曲线鼠标 + 自然打字速度(~47WPM) + 随机延迟
```
**核心流程**: 动态等待替代固定sleep + 人类轨迹模拟绕过风控

### 3. hermes_agent_loop.py
```
Perception → Cognition → Execution → Reflection → Memory
```
**核心流程**: 完整ReAct闭环 + VLM视觉校验 + LLM反思

## Ollama可用模型（2026-05-31确认）

| 模型 | 大小 | 状态 | 用途 |
|------|------|------|------|
| qwen3-vl:2b | 1.9GB | ✅ 可用 | 本地视觉校验 |
| smolvlm2-agentic-gui | 2.0GB | ✅ 可用 | GUI操作 |
| qwen2.5:1.5b | 1.0GB | ✅ 可用 | 纯文本推理 |

## 优先级调整

1. **P0**: 接入DeepSeek-R1作为主力推理（云端）
2. **P0**: 本地qwen3-vl:2b做视觉校验
3. **P1**: 实现Reflection机制（已部分实现）
4. **P1**: 动态等待+人类轨迹模拟（已实现）
5. **P2**: OmniParser集成

## 技术验证结果

- DynamicWait测试: 200ms轮询正常，3次尝试0.6s完成
- HumanTrajectory测试: 贝塞尔路径24点，自然打字~47WPM
- qwen3-vl:2b测试: 截图描述成功("macOS desktop showing Terminal")
- Reflection机制测试: 失败3次触发反思Prompt生成
