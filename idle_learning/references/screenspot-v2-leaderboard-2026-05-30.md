# ScreenSpot-V2 Leaderboard (2026-05-30 实际抓取)

## 数据来源
- URL: https://gui-agent.github.io/grounding-leaderboard/screenspot.html
- 抓取方式: browser_navigate + browser_console IIFE JS提取

## Full Rankings (Desktop | Web | AVG)

| Rank | Model | Desktop | Web | AVG | M4 24GB Viability |
|------|-------|---------|-----|-----|-----|
| 1 | UI-Venus-72B | 95.9 | 93.8 | 95.3 | ❌ Too large |
| 2 | Hcompany/Holo2-30B-A3B | 98.3 | 92.1 | 94.9 | ❌ Too large |
| 3 | Holo1.5-72B | 96.1 | 92.7 | 94.4 | ❌ Too large |
| 4 | UI-Venus-7B | 96.9 | 90.0 | 94.1 | ⚠️ ~7GB Q4, M4 tight |
| 5 | Holo1.5-7B | 96.7 | 91.1 | 93.3 | ⚠️ ~5GB Q4, tight |
| 6 | Hcompany/Holo2-8B | 97.2 | 89.0 | 93.2 | ⚠️ ~6GB Q4 |
| 7 | Hcompany/Holo2-4B | 95.6 | 89.5 | 93.2 | ✅ ~3-4GB Q4 |
| 8 | **GUI-ARP-7B** | 97.2 | 89.0 | 91.8 | ⚠️ Ollama不可用 |
| 9 | **Holo1.5-3B** | 95.0 | 88.0 | **91.7** | ✅ ~2-3GB, M4 viable |
| 10 | AGUVIS-7B | 93.3 | 81.5 | 87.3 | ⚠️ Ollama不可用 |
| 11 | **ZonUI-3B** | 92.3 | 82.9 | 86.6 | ⚠️ PyTorch only, no GGUF |
| 12 | **Qwen2.5-VL-7B-Instruct** | 87.6 | 84.4 | **86.5** | ✅ Ollama可用, ~5GB |
| 13 | OSAtlas-7B | 90.7 | 73.9 | 83.3 | ⚠️ Ollama不可用 |
| 14 | ShowUI (2B) | 78.9 | 75.4 | 77.3 | ⚠️ 4.2B > 24GB M4 |
| — | **smolvlm2-agentic-gui (当前在用)** | — | — | **61.71%** | ✅ 1.85GB |
| — | **qwen3-vl:2b (当前在用)** | — | — | ~70% est | ✅ 1.9GB, but slow 46s |

## 关键发现

### M4 24GB 可升级候选

1. **Holo1.5-3B (91.7%)** — 最高分可本地跑模型
   - 3B参数 ≈ smolvlm2同级内存占用
   - Desktop 95.0分非常亮眼（超过很多7B模型）
   - ⚠️ Ollama 池未知，需实测 `ollama pull holo1.5-3b` 或类似name

2. **Qwen2.5-VL-7B-Instruct (86.5%)** — 最低成本升级
   - 已在 Ollama 确认可用：`ollama pull qwen2.5-vl:7b`
   - 比 smolvlm2 高 25pp
   - 7B Q4约4.5-5GB，M4 24GB可运行
   - 适合：screen_watcher 离线分析、高精度GUI任务

3. **UI-Venus-7B (94.1%)** — 已知不可用
   - ⚠️ 2026-05-30 搜索确认 `ui-venus` 在 Ollama **不存在**（页面 404）
   - 不要尝试 pull

### Ollama 池已知状态（2026-05-30 更新）

| Model | Ollama | Size | ScreenSpot | Notes |
|-------|--------|------|-------------|-------|
| smolvlm2-agentic-gui | ✅ | 1.85GB | 61.71% | 当前在用 |
| qwen3-vl:2b | ✅ | 1.9GB | ~70% | 慢(46s) |
| qwen3-vl:4b | ❌ 404 | — | — | **不存在,不要pull** |
| qwen2.5-vl:7b | ✅ | ~5GB | 86.5% | 待实测 |
| blaifa/InternVL3_5:8B | ✅ | ~5GB | Unknown | 待测试 |
| Holo1.5-3B | ❓ | ~2-3GB | 91.7% | 需实测 |

## Browser Console 抓取技巧

```javascript
// 提取 leaderboard 表格（绕过 snapshot 8000字符截断）
(function(){
  const trs = document.querySelectorAll('table tbody tr');
  let out = [];
  for(const r of trs){
    const c = r.querySelectorAll('td');
    if(c.length >= 13) out.push(c[1].textContent.trim() + '|' + c[2].textContent.trim() + '|' + c[6].textContent.trim() + '|' + c[12].textContent.trim());
  }
  return out.join('\n');
})()
```

注意：browser_console 会累积变量声明，每次调用前先 `clear=true` 或用 IIFE 避免 `Identifier already declared` 错误。

## 相关 Reference

- `smolvlm2-agentic-gui-variants.md` — smolvlm2 各变体 benchmark 对比
- `vocaela-500m-benchmarks.md` — Vocaela-500M ScreenSpotV2 85.8%（24pp高于smolvlm2）
- `zonui-3b-benchmarks.md` — ZonUI-3B WACV 2026 benchmark
- `ui-tars-desktop-research.md` — UI-TARS Desktop 94.2% ScreenSpotV2