# 2026-06-01 07:00 Idle Learning Session — Direction A (Vision巡检)

## System State Snapshot
- screen_watcher: PID 8748 (running since 01:27)
- current.png: 3.3MB, timestamp 06:46
- Ollama: qwen3-vl:2b (1.76GB) + qwen2.5:1.5b (0.92GB), runner PID 45946
- Dry-run count: 957 (up from 747 at 03:08)
- June 1 00:06~06:46 scene distribution: ~100% "other" (idle), 0% unknown
- June 1 non-other scenes: only 3 — 00:47 browser, 05:28 browser+desktop
- Gateway pollution: 1868 (~7.5/hr growth, cached module residual)

## InsiderLLM Vision Guide Cross-Validation
Confirmed our model selection is optimal:
- Qwen 3.6-27B (SOTA, ~17GB) needs llama.cpp/LM Studio, Ollama unsupported
- Gemma 4 26B-A4B (~18GB) exceeds 24GB system with overhead
- qwen3-vl:2b + qwen2.5:1.5b = 2.68GB total = optimal M4 24GB fit
- **P0 decision**: Skip model re-evaluation on future Direction A rounds until Ollama supports Qwen 3.6

## PromptArmor Agent Security Pattern Confirmed
- "ChatGPT for Google Sheets Exfiltrates Workbooks" (65pts HN, June 1)
- All 18+ PromptArmor disclosures follow same pattern: indirect prompt injection → tool privilege escalation → data exfiltration
- ChatGPT extension bypasses "requires human approval" settings
- Ollama Desktop (170K★): report submitted 2025-12-18, still unpatched
- Hermes guardrail (local VLM + ACTION_WHITELIST + scene classification + negation detection) validated as more resilient

## Key Commands Used
```bash
# Network pre-check
curl -s --max-time 5 https://github.com -o /dev/null -w "%{http_code}"
curl -s --max-time 5 https://news.ycombinator.com -o /dev/null -w "%{http_code}"

# HN Firebase (worked despite HN.com timeout)
python3 /tmp/hn_top_20260601_0650.py

# DDGS (worked for targeted queries)
ddgs text -q "insiderllm best vision models mac m4 2026 ollama updated" -m 5

# Production health
grep -c "AUTO-EXEC-DRY" ~/.hermes/logs/screen_trigger.log
grep "2026-06-01" ~/.hermes/logs/screen_trigger.log | grep "场景类型:" | sort | uniq -c | sort -rn
grep -c "screen_watch" ~/.hermes/logs/gateway.log
```
