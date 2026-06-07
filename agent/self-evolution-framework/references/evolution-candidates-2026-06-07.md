# 进化搜罗成果 — 2026-06-07

## 当下系统盘点

| 模块 | 现状 | 结论 |
|------|------|------|
| Gateway | 正常运行 PID 27356 | ✅ |
| 搜索入口 | search.py v3 (anysearch + last30days + agg兜底) | ✅ 够用 |
| 记忆系统 | fact_store + state.db + 47 skills | ✅ |
| 模型链路 | V2.aicodee.com → MiniMax-M3 | ✅ |
| CDP 浏览器 | Chrome 开着但 9333 没监听 | 🔴 已修复 |
| 浏览器自动化 | anti_detect_inject.py (12项) vs CloakBrowser (58项) | 🔄 CloakBrowser 补充 |
| 脚本群 | 3套reactor并行，无主调度 | ⚠️ 待整合 |
| 智能路由 | 固定 fallback，无自动选优 | ⚠️ 暂不动 |

## 候选方案评估

### ✅ CloakBrowser — 可用（互补，非替代）
- **价值**：58项底层反检测补丁，业界最强；Python 一行安装，Playwright API
- **限制**：独立 browser profile，**不共享用户 Chrome 登录态**
- **适合场景**：匿名爬虫、反检测验证、独立 session 自动化
- **不适合**：multi_ask_v3 这类需要操控用户已登录站点的场景
- **结论**：入库作为补充工具，不替换现有 CDP 方案

### ❌ Bifrost — 排除（改模型配置）
- **价值**：自动智能路由，23+ 提供商，11微秒开销
- **排除原因**：用户明确不需要改模型配置

### ❌ n8n — 排除（加一层而非替换）
- **价值**：可视化工作流编排
- **排除原因**：Hermes 已有 cronjob + screen_trigger + reactor 编排，再加一层是重复
- **无 Docker**：Node.js 版可装但没必要

### ❌ You.com — 暂缓（搜索够用）
- **价值**：1000次/月免费 API，无限网页搜索
- **排除原因**：用户说搜索先不动

## 实际执行的进化

### P0: CDP 9333 复活 ✅
- **根因**：Chrome GUI 打开，未带 `--remote-debugging-port`，端口从未监听
- **修复**：`bash ~/.hermes/scripts/chrome-on-demand.sh start`
- **验证**：`curl http://127.0.0.1:9333/json` → 返回 tab 列表

### P1: CloakBrowser 安装 ✅
- `pip install cloakbrowser` → 0.3.28
- `bot.sannysoft.com` 测试：满分
- `bot.incolumitas.com` behavioral score：0.0074（极低）
- 脚本已创建：`~/.hermes/scripts/multi_ask_cloak.py`

## 下次进化方向建议

1. **CloakBrowser 实用场景**：需要无登录态抓数据时直接用，不动现有 multi_ask
2. **脚本统一**：hermes_reactor_v3/v2/loop 三选一定主路，减少维护负担
3. **Bifrost / 智能路由**：等用户明确需要时再评估
4. **n8n**：暂不考虑，除非有明确的编排层需求
