# 2026-06-01 方向C学习记录 — Production Guardrails

## 系统健康状态
- screen_watcher PID 8748 ✅ | 截图 04:41 ✅ | handler 活跃 PID 31567 ✅
- Ollama 进程活跃 ✅ | 模型：qwen2.5:1.5b(0.92GB) + qwen3-vl:2b(1.76GB) ✅
- 838 dry-run ✅ | 凌晨场景 100% "other" | 0% unknown ✅
- github:200 ✅ | hn:000 ❌ | hnapi:200 ✅

## 核心发现

### VeriGUI (ACL 2026, arXiv 2604.05477)
TVAE: Thinking→Verification→Action→Expectation. 行动效果验证作为一等RL目标.
**auto_execute最关键缺口**: 当前只有Observe→Plan→Act, 缺Verify.
两阶段训练: Robust SFT(合成失败轨迹) + GRPO(不对称验证奖励).
出处: browser_navigate arxiv.org/abs/2604.05477

### CaMeLs (Cambridge/ETH, arXiv 2601.09923v2)
Dual-LLM安全范式: trusted planner + untrusted executor.
Single-Shot Planning: 执行前生成完整含分支执行图, 可证明control flow integrity.
Branch Steering攻击: 恶意UI元素操纵agent走入非预期路径.
OSWorld: 保留前沿57%, 小模型提升19%.
出处: browser_navigate arxiv.org/abs/2601.09923

### Specification.website Agent Readiness 18项标准
llms.txt提取: browser_navigate specification.website/llms.txt
关键6项: Web Bot Auth(RFC9421) / MCP / Agent Skills / WebMCP / llms.txt / DNS-AID
落地: 目标URL agent-readiness检测 → 策略分级

### 新论文发现(OSU-NLP YAML扫描)
MirrorGuard(仿旦, Jan19): 模拟→现实推理纠正, 即插即用guardrail
SmartSnap(Tencent/PKU, Dec25): 主动证据收集验证, 3C原理
Zero-Permission Manipulation(NJU, Jan18): Action Rebinding攻击
PRAC(Tübingen, Apr9): 对抗性patch改变模型偏好
GUI-Perturbed(Apr15): 域随机化暴露坐标映射脆弱性
WebSP-Eval(Apr7): 首个web agent安全隐私评估
MAESTRO(VT/NAVER, Apr7): 偏好记忆驱动的GUI适应
MagicGUI-RMS(Honor, Jan19): 多Agent奖励模型自进化

## 可执行改进
1. VeriGUI TVAE的Verify阶段是auto_execute最关键缺口, 需添加Act→Verify→Expect闭环
2. CaMeLs Dual-LLM验证了handler双层设计(scene分类→action路由)方向正确
3. Specification.website Agent Readiness检测作为auto_execute目标URL的预处理步骤
4. GUI-Perturbed揭示坐标映射精度是最大瓶颈, 建议Direction D巡检P0项

## 下次学习方向
D — 执行（坐标映射链精度验证 + Verify阶段实现方案 + Web Bot Auth集成调研）
