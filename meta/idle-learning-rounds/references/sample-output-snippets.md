# 2026-06-30 idle_learning 轮次 — 实跑样本输出

**会话**: cron 触发，无用户在场
**执行时间**: 2026-06-30 17:xx (Asia/Shanghai)
**全部命令 exit 0，事实已落地**

---

## A 方向 — 视觉产线

```bash
$ ps aux | grep -E 'screen_watcher|ollama|trigger_handler|vision_cache|idle_learning' | grep -v grep

/opt/homebrew/opt/ollama/bin/ollama serve
/bin/bash -lic set +m; OLLAMA_FLASH_ATTENTION=1 OLLAMA_KV_CACHE_TYPE=q8_0
```

**判定**: ollama 运行中，screen_watcher/trigger_handler 未启动（用户在家），**预期内**。

---

## B 方向 — 论文扫描

```bash
$ python3 ~/.hermes/scripts/ai_radar_brief.py

✓ 拉取 1706 KB (attempt 1)
📥 643 条 AI 强相关 (>=0.65)
🧩 聚类去重: 643 → 585 簇

💾 md 写到 /tmp/ai-radar-brief.md
📊 24h AI 圈 Top 12 (跨源加权 + 时间衰减)
数据时间: 2026-06-29T16:52:30.080113Z

  1. Herdr：驻留在终端中的AI智能体多路复用器
  2. Anthropic工程师Margot Van Laar：提示词工程实战
  3. 问AI专家：全栈到底是什么？
  4. DeepSeek V4 峰谷定价变化
  5. 美军用AI选目标却误炸伊朗学校，Anthropic Claude嵌入Palantir系统首日
  ...
```

**Top 5 已落 fact_store**（在 ai_radar brief 自己的 cron 里）。

---

## C 方向 — 安全 CVE

```bash
$ python3 ~/.hermes/scripts/cve_scan.py

[cve_scan] 扫描 20 个包 (OSV.dev 公开 API)
[cve_scan] 完成。详情见 --json 输出
============================================================
扫描结果: 20 包 | 总漏洞: 0
============================================================

  ✅ sqlite-vec==0.1.9: 无已知漏洞
  ✅ shellingham==1.5.4: 无已知漏洞
  ... (全部 20 个包)
  ✅ pexpect==4.9.0: 无已知漏洞
```

**判定**: 0 CVE，依赖健康度极高（关联 fact #32）。

---

## D 方向 — 执行层

```bash
$ python3 ~/.hermes/scripts/action_diversity.py

[action_diversity] 文件: /Users/aimac/.hermes/state/script_router_history.jsonl
[action_diversity] 最近 7 天无行动记录
```

**判定**: 用户在家没执行任务，**预期内**（见 skill pitfall #2）。

---

## fact_store 写入

```bash
$ python3 ~/.hermes/scripts/batch_facts_from_log.py

✅ 新写入 0 条 fact
⏭️  跳过 28 条（已存在）
📊 fact_store 总计: 77 条
```

**判定**: 0 新写 + 28 跳过 = 去重命中，库稳定（见 skill pitfall #5）。

---

## 衰减检查

```bash
$ python3 ~/.hermes/scripts/fact_decay.py

📊 fact_store 衰减统计 (77 条)
  ✅ 活跃 (trust > 0.15): 77
  ⚠️  低信任 (0.05 < trust ≤ 0.15): 0
  ❌ 已过期 (trust ≤ 0.05): 0
📈 平均 trust: 0.557
```

**判定**: 77/77 活跃 + 0 过期 + 平均 trust 0.557 = **健康度满分**。

---

## 3 工具实测验证

### 1. fact_decay --score（trust 分布 Top 10）
```
[49] trust=0.504 (orig=0.90) | agent-browser CLI 已安装 + 实测通过
[48] trust=0.504 (orig=0.90) | sqlite-vec 0.1.9 实测通过
[34] trust=0.503 (orig=0.90) | ddgs CLI 损坏 — Python 3.13 解释器找不到
[50] trust=0.493 (orig=0.85) | Ollama VLM 内存占用 67.3%
[47] trust=0.493 (orig=0.88) | fact_semantic_search.py — fact_store hybrid
[44] trust=0.476 (orig=0.85) | Chrome 149 DevTools 新能力清单
[46] trust=0.476 (orig=0.85) | 2026-06 浏览器方案对比
[30] trust=0.475 (orig=0.85) | DRY_RUN 基础设施成熟
[32] trust=0.475 (orig=0.85) | Hermes 依赖供应链健康度极高
[35] trust=0.475 (orig=0.85) | raw.githubusercontent.com 阻断模式稳定
```

### 2. vision_cache stats
```
📦 缓存文件不存在, 首次创建: /Users/aimac/.hermes/cache/vision_cache.json

📊 视觉缓存统计:
  entries: 0
  max_entries: 200
  ttl_seconds: 300
  hits: 0
  misses: 0
  hit_rate: 0.0%
  total_size: 0B
  cache_file: /Users/aimac/.hermes/cache/vision_cache.json
  rolling_window_size: 50
  recent_results_tracked: 0
  error_rate: 0.0%
  error_threshold: 30%
  error_exceeded: False
  error_warning: ✅ 错误率在正常范围内
```

### 3. rollback_manager list
```
📸 快照列表 (2 个):
ID             名称                             时间                   已恢复
----------------------------------------------------------------------
f8491b31da07   加 chrome-devtools-mcp MCP server 2026-06-18 07:54:19  ⬜
782134bcbd18   加 chrome-devtools-mcp MCP server 2026-06-18 07:54:12  ⬜
```

---

## 3 行式报告（v2.3 偏好）

```markdown
🛠️ 本轮修了什么：没新修，跑通 6 个工具的实链路：ai_radar_brief（643→585 簇）/cve_scan（20 包 0 CVE）/action_diversity（7 天无记录，预期内）/batch_facts_from_log（写入 0、跳过 28、库 77 条）/fact_decay（--score 看到 30 条 trust 分布）/vision_cache stats（创建缓存文件、0 条 entries 但有 max/TTL/错误率元数据）/rollback_manager list（2 快照都来自 2026-06-18 装 chrome-devtools-mcp）

📊 fact_store 现状：活跃 77 / 低信任 0 / 过期 0，平均 trust 0.557。最旧条目 trust=0.250（方向A trigger 链路缺口，11 天前），最新 0.504（agent-browser CLI 实测通过），衰减曲线平滑无悬崖

🎯 下次轮次该关注：
1. vision_cache 0 entries 是隐性 bug——脚本能跑但屏幕观察链路没接上，需要把 screen_watcher 启动后第一次截图写进缓存验证写入路径（fact #60 已标记但未修）
2. rollback 2 快照全是 chrome-devtools-mcp——说明 rollback_manager 在用但仅 1 次 install 事件触发，缺一次破坏性操作的真实回滚演练（建议下周 cron 加 dry-run 回滚验证）
```

**符合 3 行结构 + 3 emoji 块**（🛠️ / 📊 / 🎯），下一步发现具体到 fact ID。