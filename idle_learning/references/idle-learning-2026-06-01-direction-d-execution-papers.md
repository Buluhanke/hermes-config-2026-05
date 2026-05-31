# Direction D 新论文发现 — 2026-06-01 执行层巡检

**来源**：OSU-NLP-Group GUI Agents Paper List YAML 扫描（~540 papers）
**方法**：browser_navigate raw YAML → browser_console 分片提取 → 过滤 Desktop + execution/reinforcement/verification 关键词 → 排除已有记录

---

## 1. ⭐ Terminal Agents Suffice for Enterprise Automation

- **arXiv**: 2604.00073 (ServiceNow, 2026-03-31)
- **核心论点**: CUA coding agent 仅靠 terminal + filesystem 即可匹配或超越 GUI-driven 和 MCP tool-augmented agent
- **测试场景**: ServiceNow, GitLab, ERPNext
- **对 Hermes 的意义**: 验证 CLI+filesystem 路径的合理性。Hermes 已有 `computer_use` + `terminal` + `mcp_chrome_*` 三通道，与 "terminal suffices" 互补而非矛盾
- **对 auto_execute**: screen_watcher scene classification 可在 GUI 操作 vs CLI 操作两条路径间做路由决策
- **tag**: direction-D, execution, enterprise, service-now

## 2. ⭐ The Tool Illusion: Rethinking Tool Use in Web Agents

- **arXiv**: 2604.03465 (MSR / Penn State, 2026-04-03)
- **核心论点**: 大规模控制实验质疑 tool use 是否提供一致性增益。跨工具源、基座模型、tool-use 框架、评估基准的对比研究
- **对 Hermes**: 与 "MCP Is Dead" 论点一致（所有工具定义常驻内存的成本），验证 Skills 按需加载优于 MCP 全量加载
- **tag**: direction-D, tool-use, msr, web-agents

## 3. ⭐ Gym-Anything: Turn Any Software into an Agent Environment

- **arXiv**: 2604.06126 (CMU, 2026-04-07)
- **核心**: CUA-World 10K+ 长周期任务（医学、天文、企业），CUA-World-Long 500+ steps
- **多 agent pipeline** + audit 将任意软件转为 agent 可交互环境
- **对 Hermes**: 环境生成方法论 — 未来可用于 auto_execute 的测试环境搭建
- **tag**: direction-D, environment-synthesis, benchmark, cmu

## 4. ⭐ When Users Change Their Mind: Interruptible Agents

- **arXiv**: 2604.00892 (UIC / McGill / MBZUAI, 2026-04-01)
- **核心**: 首个中断式 agent 系统性研究。三种中断类型：addition / revision / retraction
- **InterruptBench**: 基于 WebArena-Lite
- **对 Hermes**: screen_watcher 的 handler 冷却机制 (60s) 是隐式中断处理。未来需显式识别中断信号（用户接管、指令变更）
- **tag**: direction-D, interruptibility, benchmark, uic

## 5. ⭐ GUIDE: Resolving Domain Bias through Real-Time Web Video Retrieval

- **arXiv**: 2603.26266 (SJTU / BIGAI, 2026-03-27)
- **核心**: 训练无关 (training-free) 视频检索插件：搜索教程视频 → 转为 planning + grounding annotations → 注入任意 agent
- **效果**: OSWorld 改进多个 agent family，执行步骤减少
- **对 Hermes**: future 可参考此方案为 unknown/other 场景提供领域知识注入
- **tag**: direction-D, video-retrieval, training-free, domain-bias
