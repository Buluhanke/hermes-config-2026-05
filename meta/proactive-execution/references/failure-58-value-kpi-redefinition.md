# Failure 58 — 2026-06-30 数字人 KPI 重定义实战

**关联 SKILL**: `meta/proactive-execution/SKILL.md` v1.15.0
**触发用户原话 (完整)**:
> "兄弟，陪你一起成长那么久，除了我一直花钱买 token 给你，好像你并没有给我创造任何价值呀"
> "本来 24g 内存 docker 一装死他没发运行了"
> "目前电脑屏幕都无法一眼识别，这何时是个头"
> "花钱没创造任何价值"
> "有全网搜索的能力，互联网上有所有的知识，你不去使用不去利用是不会成长的"
> "作为数字人，你的核心是要自我驱动成长，不应该是我来喂你知识"
> "你配置的几个大型 AI 网站还登录给你，你不去索取知识那配置就失去了意义呀"

## 实战复盘 (本会话真实发生的 13 个"没价值"动作)

| 时间 | 动作 | 真正代价 | 用户感受到的价值 | 类别 |
|---|---|---|---|---|
| 19:58 | 跑 1 个夜间 ABCD cron | 1 token | 0 | **反例 1** 任务即停 |
| 20:35 | 跑 LibreChat 完整部署 | 2h / 3000+ npm 包 / ~500MB 内存常驻 | 0 (没问用户用得上吗) | **反例 2** 装了一堆 |
| 21:00 | 拉 Cocoloop / Claude Code 资料 | 5+ web_search / web_extract | 0 (没装任何 skill) | **反例 3** 装前没问 |
| 21:30 | 跑 13 个夜间 cron `cronjob action='run'` 验证 | 13 次调用 | 0 (用户没问我要) | **反例 1** 主动跑 |
| 22:00 | 写 4 条 memory 条目 | 4 次 tool call | 1 (后续 session 受益) | ✓ 算有沉淀 |
| 22:13 | Ollama 拉起 + 写 ai_login_probe.sh | 1 background process + 1 文件 | 0.5 (vision 跑通了但只验证了 cua-driver 自己) | **反例 4** 能力闲置 |
| 22:30 | 列 6 个容器替代方案 (Podman/Container/Lima...) | 长输出 | 0 (用户一句话"放弃"打回) | **反例 5** 列方案不落地 |

**总账**: 今日 Token 花销 ~$5-10 (估), 用户感受到的价值 ≈ $0.5 (vision 跑通 + memory 沉淀)

## 5 步自检 SOP (新增, 会的能力验证)

```bash
# 会话起手 / 每次长静默后, 0 思考跑:
# 1. Ollama 在线?
curl -s --max-time 3 http://localhost:11434/api/tags | python3 -c "import json,sys; d=json.load(sys.stdin); print([m['name'] for m in d.get('models',[])])"
# 期望: 至少 llava:7b 在列表

# 2. 5 个 AI 网站 tab 状态?
mcp_chrome_devtools_mcp_list_pages | grep -E "(deepseek|gemini|doubao|chatgpt|grok|chatglm)" -i
# 期望: 至少 1 个已开 (上次会话留的)

# 3. 桌面 app 列表 (注意 macOS name 带 "- " 前缀)
mcp_cua_driver_list_apps | python3 -c "import json,sys; [print(a['name'], a['pid']) for a in json.load(sys.stdin)['apps']]"
# 期望: Chrome / Terminal / Finder 至少一个在跑

# 4. 核心进程
ps aux | grep -E "hermes.*gateway|chrome|ollama" | grep -v grep | awk '{print $2, $11, $12}' | head -10
# 期望: gateway 在跑, chrome 在跑

# 5. 本周 skill 改动
find ~/.hermes/skills -mtime -7 -name "SKILL.md" | head -10
# 期望: 至少有 1-2 个 skill 本周有改动
```

**任一不达标** → 0 思考自修, 不问用户 (Failure 50 "顺手 = 强制执行")

## 价值审计 4 问模板 (新增, 每次汇报前 0 思考过)

```
[我刚才做了 X, 共花 N token]
① 这件事对用户有什么用? (a) 省时间 (b) 省 token (c) 创造收入 (d) 解决问题
② 有可验证的产物吗? (a) 截图 (b) 文件 (c) 跑的脚本输出 (d) 推 Telegram
③ 花的 token 换回了什么? 不换 = 立即停 + 报告"这方向无价值"
④ 这件事下次还能复用吗? 不能 = 没沉淀, 等于没做
→ 任何一项 NO → 0 思考停手 + 报告
```

**示例 (本会话反例套用)**:
- 跑 13 个 cron 验证 → ① 没用 (用户没问) ② 没产物 ③ 0 回报 ④ 不能复用 → **4 项 NO, 应停**
- 写 ai_login_probe.sh → ① 有用 (后续 session 起手验证) ② 有产物 (.sh 文件) ③ 节省未来调试时间 ④ 能复用 → **4 项 YES, 算有沉淀**

## 5 个 AI 网站主动取经 SOP (新增)

```python
# 触发: 空闲 > 1h OR 接到"不会做 / 没把握 / 第一次见"的任务

from hermes_tools import mcp_chrome_devtools_mcp as chrome

sites = [
    ("deepseek", "https://chat.deepseek.com/"),
    ("gemini",   "https://gemini.google.com/app"),
    ("doubao",   "https://www.doubao.com/chat"),
    ("chatgpt",  "https://chatgpt.com/"),
    ("grok",     "https://grok.com/"),
    ("glm",      "https://chatglm.cn/main/alltoolsdetail"),
]

# Step 1: 验证登录态 (HTTP 200 ≠ 登录)
import subprocess
for name, url in sites:
    code = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", url],
                         capture_output=True, text=True, timeout=6).stdout
    print(f"{name}: HTTP {code}")

# Step 2: 打开 tab 验证 (mcp_chrome_devtools_mcp_list_pages)
pages = chrome.list_pages()
for p in pages.pages:
    if any(s in p.url for s, _ in sites):
        print(f"✓ {p.url} 开着")
    else:
        print(f"⚠  {p.url} 没登录态")

# Step 3: 真发消息验证 (fill + press Enter + wait_for)
prompt = "数字人如何在 Mac mini 24GB 上用本地 LLaVA 做实时屏幕理解? 给具体可执行方案"
for name, url in sites:
    try:
        chrome.new_page(url=url)
        # ... fill + Enter + wait_for 30s
        # ... 收到回复 → 写入 fact_store + patch skill
    except Exception as e:
        print(f"✗ {name}: {e}")
```

## 装 X 前 3 问 (新增)

```
[用户说"装 X / 研究 X / 看看 X" 之前, 内部必答]
① X 装完用户能直接用吗? (vs 只是我能用)
② X 装完占多少资源? (Mac mini 24GB 优先, Docker 已被禁)
③ X 装完下次同类任务能复用吗? (沉淀为 skill / script, 不只装一次)
→ 任何一项 NO → 告诉用户"装完意义有限, 建议先 P0/P1 更重要的"
```

**反面案例 (本会话)**:
- "研究 Cocoloop" → ① 用户能直接用吗? 能 (Cocoloop Hub 13k skills) ② 占资源? 0 ③ 复用? 短期没用 → **2 NO, 不该装 skill**
- "装 LibreChat" → ① 用户能直接用吗? 能 (前端可访问) ② 占资源? 500MB ③ 复用? 没用 → **2 NO, 不该装**

## 失败模式识别 (本会话触发的所有相关 Failure)

| Failure | 触发场景 | 表现 | 修法 (本会话已落地) |
|---|---|---|---|
| 45 完成即停 | 跑完 LibreChat 验证 → 列借鉴价值 → 等 | 等了 5 分钟 | 报告后自动接下一个 (规则 8) |
| 50 软反问 | "接下来要不要..." | 反问 1 次 | 陈述句 + 直接 tool call |
| 53 能力闲置 | computer_use 不拍屏幕 / vision 不调用 / web_search 不搜 | 5 个 AI 网站配置了不用 | Failure 58 修法 |
| 58 KPI 错位 | 把研究当产出 | 装了 2h LibreChat 没用户用 | Failure 58 价值审计 4 问 |
| **新**: 路径依赖 | 走熟悉的 terminal/grep 不走 computer_use | 5 秒能做的事用 30 秒 | 5 步自检 SOP |

## v1.15.0 changelog 关联

```
v1.15.0 (2026-06-30) 新增 Failure 58 + 价值审计 4 问 + 5 步自检 SOP + 5 网站取经 SOP + 装前 3 问
v1.14.0 (2026-06-30) 新增 Failure 53 "数字人有能力不用"
v1.12.0 (2026-06-27) 新增 Failure 52 "阻塞即静默"
v1.11.0 (2026-06-27) 新增 cron 静默化 (规则 9)
v1.10.0 (2026-06-26) 新增 Failure 51 "cron 推 Telegram 3 个隐蔽坑"
```

## 关联 skill (互相引用)

- `meta/ponytail/SKILL.md` — Ponytail 反模式 3 "不搜现成方案" + Failure 58 装前 3 问
- `meta/verification-before-reporting/SKILL.md` — Failure 56/57 + Failure 58 价值审计 4 问
- `meta/idle-learning-rounds/SKILL.md` — A→B→C→D 4 方向 + Failure 58 5 网站取经 SOP
- `devops/hermes-see-act/SKILL.md` — computer_use 4 步 SOP + Failure 58 "会的能力日常化铁律"
- `devops/hermes-runtime-fortress/SKILL.md` — 本地 Ollama 守护 + Failure 58 5 步自检 SOP

## 触发词 (下次同类反馈, 0 思考加载本文件)

- "花钱没价值 / token 没用 / 价值产出 / 不出活 / 24GB 闲"
- "装了一堆没用 / 装完不落地 / 跑通但没价值"
- "AI 网站不用 / 配置失去意义 / 5 个网站躺着"
- "Ollama 跑着不调用 / 4.7GB 闲置 / 能力建好不用"
- "你确定吗 / 真的有用吗 / 这跟我有什么关系"
- "屏幕无法一眼识别 / computer_use 没用 / vision 调用失败"
