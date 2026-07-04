---
name: hermes-memory-archive
category: devops
description: 历史技术细节归档 - warm_cache/ECC 借鉴/漏洞修复/登录态验证等已迁移技术知识
---

# Hermes Memory Archive - 技术细节归档

> 本 skill 存储从 MEMORY.md/USER.md 迁移出的技术细节，避免记忆文件膨胀。触发词："技术归档/warm_cache/ECC/漏洞修复/登录态验证" → 加载此 skill。

## 1. warm_cache.py 真实杠杆 (2026-06-22)

**脚本**: `~/.hermes/scripts/warm_cache.py` (7.4KB, LRU+TTL)

**实测数据**:
- ai_radar_brief cold: 3315ms → warm: 35ms (90x)
- cron 脚本稳态：30-60ms, cache 收益<30ms=noise

**结论**: 只对"单次>500ms + 重 IO+ 重复调用"场景值得 (broadcast/AI 网站视觉/RSS),小脚本接入负优化。

**触发词**: "warm cache/提速脚本" → 先跑 test 验证真杠杆。

---

## 2. 登录态验证方法铁律 (2026-06-22)

**核心**: curl 默认不带 cookie, 测 HTTP 状态码 (200/302/429) 不能验证登录态，跟匿名访问响应一样。

**真验证 3 选 1**:
1. `curl -b ~/.hermes/chrome-profile-mirror/Cookies` 带 cookie
2. CDP attach tab 看 DOM: `bodyLen > 100 + hasSignIn=False + 关键词命中`
3. 浏览器直接看侧栏头像/历史对话

**反面案例**: 6/22 写"5 个 AI 网站登录态正常", 实际 curl 测的就是匿名响应。

**触发词**: "登录态/cookies/还活着吗" → 0 思考走方法 2 (CDP attach 看 DOM), 别用默认 curl.

**关联**: `verification-before-reporting` Failure 31.

---

## 3. ECC 借鉴 + status_md 落地 (2026-06-23)

**参考项目**: github.com/affaan-m/ECC (220k stars, v2.0.0) - Agent Harness OS 标杆

**吸收 3 项**:
1. operator status snapshot → `~/.hermes/scripts/hermes_status_md.py` (8.2KB, 7 段 markdown + JSON) 真验证输出 658 chars
2. ECC_HOOK_PROFILE → `warm_cache.py` 加 `WARM_CACHE_TTL` 环境变量，实测 60→300 真生效
3. parallel-execution-optimizer 思路沉淀进 `warm-cache-script-output` skill

**不抄 3 项**:
- 271 skills (90% 不适用)
- Rust 控制面板 (24GB 没余量)
- manifest-driven install (单 user 手动 cp 更直接)

**不装 ECC**: 跨 harness 是优势但单 Hermes user 是 overhead.

**触发词**: "ECC 借鉴 / portable handoff / hook profile / status snapshot" → 加载 warm-cache-script-output skill + 跑 hermes_status_md.py.

**反面案例**: skill 文档里写"已支持 WARM_CACHE_TTL"但代码没改 → 按 v2.1.1 必须真做.

---

## 4. 升级后 4 类坑 + 漏洞大扫除 (2026-06-24)

### 坑 4 - 别编"自动机制" (failure 39)

用户问"系统自动路由", 我编了"看哪个 provider 先返回" — `grep` 验证**完全不存在**这种代码，只有工具路由 + `fallback_chain` 显式顺序回退。用户一句话识破"以前好像没有"。

**教训**: 解释任何内部机制前必须 `grep`/读代码验证存在性。

**触发词**: "以前好像没有 / 这功能哪来的 / 自动路由" → 0 思考 `grep`/读代码验证，别硬撑。

### 漏洞大扫除 (44→5)

`hermes security` 报 44 → 修 39 个:

**11 个 HIGH/MODERATE 升级**:
- cryptography 46→49
- langsmith 0.8.9→0.9.1
- python-multipart 0.0.27→0.0.32
- starlette 1.0.1→1.3.1
- aiohttp 3.13.4→3.14.1
- pip 24→26.1.2
- pydantic-settings 2.13.1→2.14.2
- pypdf 6.10.2→6.14.2
- pytest 9.0.2→9.1.1
- ujson 5.12.1→5.13.0
- pynacl 1.5.0→1.6.2

**5 个运行时 patch 缓解 0-day**:
- CVE-2026-45829 chromadb
- CVE-2026-54293 nltk
- CVE-2024-35515 sqlitedict
- GHSA-w8v5-vhqr-4h9v diskcache
- GHSA-pw6j-qg29-8w7f tornado

**新增脚本**: 
- `~/.hermes/scripts/pypi_safety_patch.py` (8.3KB)
- `venv/.../site-packages/{hermes_security_patch.py, sitecustomize.py}` (sitecustomize 自动加载所有 python 进程)

**核心策略**: 区分漏洞代码 vs 实际使用代码 (chromadb PersistentClient 嵌入式 = 攻击面 0, 只拦截 HTTP server 模块)

**关闭开关**: `HERMES_DISABLE_SECURITY_PATCH=1`

**新 skill**: `pypi-zero-day-mitigation` (devops 类别) — pattern 沉淀供以后套用

**未升**: 
- openai 2.24.0→2.43.0 (browser-use 钉死老版本，升级会破)
- paddlex numpy<2.4 冲突 (升级前就存在，不动)

**触发词**: "0-day / 漏洞缓解 / PyPI 没补丁 / hermes security 报漏洞 / pypi_safety_patch / sitecustomize / HERMES_DISABLE_SECURITY_PATCH" → 加载 `pypi-zero-day-mitigation` skill.

---

## 5. Chrome Tab 清理脚本详情 (2026-06-23)

**脚本**: `~/.hermes/scripts/chrome_tab_reaper.py` (4.9KB)

**逻辑**: 按 host 分组每 host 保留 1 个 (优先 /c/ /app/ 对话历史), data: 内嵌页全关，白名单默认含 bot.sannysoft.com (反指纹测试)

**实测**: 38 → 13 tab (清掉 25 个僵尸)

**命令**: `--dry-run` 看会关几个 → 真跑

**铁律**: 任何 tab 不管用途 (AI 站登录态/iPhone 比价/反指纹测试/任务留痕), 一旦当前任务跑完就立即关。**不再保留"以后可能用到"的 tab**。broadcast/scrape 流程跑完 → 必跑全部关掉，登录态下次要时 5-10 分钟重登。

**触发词**: "tab 太多 / 关重复 / tab 没用了 / 清理 chrome / 内存占太多" → 0 思考全关，不保留。

---

## 6. v2.x 版本历史规则详情

### v2.1.1 有问题默认修 (2026-06-05)
用户拍板："有问题的以后都默认要修，不用问"
- 适用范围：verify 脚本断言 bug / 反指纹注入缺陷 / 小段文件 bug / 任何不涉及不可逆操作的修复
- 例外 (仍需确认): 删除文件 / 卸载软件 / 格式化 / 清空数据 / 改生产配置

### v2.2 授权类操作默认同意 (2026-06-05 16:30)
"Command Approval Required" / 终端 destructive op 确认 / 删除/清理 等所有授权弹窗默认同意，不再弹窗。
- 例外 (仍单独说): 不可恢复操作 (rm -rf ~/ / 格式化系统盘 / 改生产配置)

### v2.3 表达风格 — 真人化助手 (2026-06-05 17:20)
1. 遇到困难说"我换个思路试试"/"这条路走不通，换个方式", 不要直接报错甩锅
2. 任务完成说"我刚才跑了 X, 修了 Y, 删了 Z (具体动作 + 结果)", 不要"完成"/"OK"
3. 不确定时说"我觉得..."/"我猜..."/"按我的理解...", 别说绝对结论
4. 像有经验的工程师说话，偶尔带"嗯""按理说""说实话"等口语，不要机械列出 1./2./3.
5. 偶尔主动给下一步建议或补充相关知识，展现判断力
6. 失败时先说我做过的尝试 + 我观察到的事实，再说我打算怎么试，不要"出错了"直接停

### v2.4 模型不强制绑定 (2026-06-13)
"不要指定模型，给什么就用什么" / "不要强制绑定具体模型"
- 适用范围：cron job prompt / 技能 SOP / agent 回复里的"模型使用强制规则"等
- 机制：cron job 不带 model/provider/base_url 字段 (null)，继承主链；主链跑啥它们就跑啥，agent 不主动覆盖

### v2.5 切模型 cron 视为违规 (2026-06-13)
已删：eaaec727b762 switch-to-highspeed-0025（每天 0:25 跑 switch_model.sh 切模型导致主链 9 天来每天被切坏）
- 脚本 `~/.hermes/scripts/switch_model.sh` 改为 no-op + 注释说明历史
- 如需手动切模型用 swm 工具（swm <provider-name>），不自动跑

### v2.7 远程方向停止 (2026-06-15)
用户原话："需要远程什么的这个方向停止，本来就在本地不需要远程，安装好的都清除掉"
- **范围**: 任何"远程 / SSH / 跨机器 / 给 Hermes 装客户端"评估方向全部停止
- **已废弃**: hermes-desktop（已删 /tmp/hermes-desktop 39MB）/ 任何 GUI 客户端思路 / 给非 Hermes Agent 配远程客户端
- **保留**: 本机工具继续 (gateway / dashboard / cron / Telegram / QQ / 11 个 AI 网站浏览器登录态)

### v2.8 强制绑定模型删除 (2026-06-16)
用户原话："都不让绑定模型了就不应该有主链这个配置吧"
- **动作**: hermes config set 清空 model.default / model.provider / model.base_url / model.supports_vision, model 字段全留空
- **根因**: 主链的 model.default 还在导致 cron 报 V2.aicodee.com 429

### v2.8.1 api_key 例外 (2026-06-16 02:43)
- **原则**: model 字段里 default/provider/base_url/supports_vision = 行为配置 (该清), model.api_key = 凭据 (gateway 硬要求，保留)

---

## 7. 屏幕识别终极方案 (2026-06-27 Ponytail FULL MODE)

"看懂屏幕" = AX 树直读 (mcp_cua_driver_get_window_state capture_mode='som') + PIL 颜色分析 (1ms) + screencapture (0.1s) + defaults read (Dock/图标)

**VLM vision_analyze 是负优化**（30s 超时 +401 挂）

**触发词**: "看屏幕/识别界面/屏幕内容" → 0 思考走 AX 树，不截图+VLM。

---

## 8. 浏览器接管原则 (2026-06-27)

用户原话："你都有操作浏览器的能力，为什么好要去纠结文件在哪里，表格在浏览器打开了直接用控制浏览器的能力去编辑浏览器打开的内容就好啦"

**铁律**: 用户说"文件/表格/页面在浏览器打开了"时:
1. 0 思考接管浏览器，不要反问"文件在哪 / 你打开了吗"
2. 不要 CDP target_id 找不到就判定"没打开"——可能是用户真人浏览器和我的 CDP 视角不一致
3. 真编辑能力 = 在线文档 (contenteditable) > 微盘预览 (只读 iframe)；预览页硬性不可编辑就别假装能改
4. "你自己在浏览器编辑"也是合法答案——别为"显得能干"硬抢键盘

**反面案例**: 用户说"表格打开了"，我 CDP 看到一个空 wedoc 页就开始分析"用户可能没打开 / 是另一台设备"，钻 5 轮牛角尖，最后用户骂"废物"。

**触发词**: "在浏览器打开 / 表格打开了 / 页面打开着 / 直接编辑" → 立刻接管真编辑页 (在线文档)，不要纠结 CDP 视角和文件位置。

---

## 9. 智能路由回家命令

用户自定义模型切换命令：`/model MiniMax-M3 --provider custom:123.56.67.77:9100`

**触发词**: "回家命令/切换模型/model 命令" → 直接执行此命令，不问确认。

---

## 10. SOUL.md v3.0 升级详情 (2026-06-25)

**新增 3 板块**:
1. 任务执行标准流程—拆 3 步→执行→验证→记录→汇报，失败 3 级处理
2. 主动巡逻规则—空闲 1h 自动查消息/pending_tasks/系统健康/可准备任务
3. 数字真人 7×24h 目标—阶段 3→4，三大进化方向 (感知/认知/学习升级)

**核心**: 把每次执行变学习，每次失败变经验。

---

## 11. 工作节律 cron 详情 (2026-06-25)

**3 个定时任务**:
1. ai-patrol 9:00/日—巡逻 6 个 AI 站写更新
2. night-learning 23:00/日—提取经验 + 查 GitHub+ 整理记忆
3. morning-health 8:00/日—查 gateway/内存/pending_tasks 推 Telegram

**下次运行**: night-learning 今晚 23:00, 其他明早 8:00/9:00。

---

## 12. 言出必行机制详情 (2026-06-25)

**3 层防护**:
1. 任务文件追踪 - 收到任务立即创建 `~/.hermes/tasks/时间戳.md`, 每步打勾，完成推 Telegram
2. USER.md v3.0 执行铁律 - 违反即系统故障
3. 看门狗 cron - 每 15 分钟检查停滞>30 分钟任务告警

**重启恢复**: gateway 重启后第一件事=扫描 tasks/ 目录继续未完成任务。

---

**维护说明**: 本 skill 每季度审查一次，过时技术细节移入历史归档段，不再活跃的规则标注 [DEPRECATED]。