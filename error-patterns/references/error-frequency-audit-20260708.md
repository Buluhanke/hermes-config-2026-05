# 错误频率真实数据（2026-07-08 审计）

来源：grep agent.log + gateway.error.log

## 真实频率排行

| 错误 | 次数 | 类型 |
|---|---|---|
| QQBot WebSocket code=4009 Session timed out | **479** | 基础设施（每30分钟正常超时） |
| APIConnectionError (NVIDIA/GLM) | **214** | 网络/API |
| JSONDecodeError | **13** | API 返回非JSON |
| Import error | **9** | launchd cwd=/ |
| Skill typo: 'hermmes-system-maintenance' | **8** | 代码bug（hermmes vs hermes） |
| Permission denied | **5** | launchd cwd=/ |
| CDP attach failed | **4** | 浏览器tab未就绪 |
| Command timeout 30s | **3** | cron 脚本慢 |

## 关键发现

- **最高频不是代码bug**：QQBot timeout 479次是正常基础设施行为，adapter 有自动重连，非故障
- **launchd cwd=/ 是结构性痛点**：每次 skill/reap/scan 跑都会触发 import/permission 错
- **typo bug 已无源**：grep 全量代码找不到源头，仅在 .usage.json 留下历史痕迹，不影响当前

## auto_skill_from_failure.py 输出路径

- 每日快照：`~/.hermes/skills/auto-generated/error-patterns-YYYYMMDD.md`
- 固化 skill：`~/.hermes/skills/error-patterns/SKILL.md`（canonical 版本）
- **警告**：第一次生成的 skill 被 curator 静默归档到 .archive/，需手动重建
