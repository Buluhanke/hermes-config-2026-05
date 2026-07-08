#!/usr/bin/env python3
"""Hermes LLM 可观测性查询脚本 — refs: hermes-observability SKILL.md"""
import sqlite3, os, sys
from datetime import datetime

DB = os.path.expanduser("~/.hermes/llm_traces.db")

PRICING = {
    "anthropic/claude-sonnet-4":   {"input": 3.0, "output": 15.0},
    "anthropic/claude-opus-4":    {"input": 15.0, "output": 75.0},
    "anthropic/claude-haiku-4":    {"input": 0.8, "output": 4.0},
    "openai/gpt-4o":             {"input": 2.5, "output": 10.0},
    "openai/gpt-4o-mini":        {"input": 0.15, "output": 0.60},
    "openai/o3":                 {"input": 10.0, "output": 40.0},
    "openai/o4-mini":            {"input": 1.1, "output": 4.4},
    "google/gemini-2.5-pro":     {"input": 1.25, "output": 5.0},
    "google/gemini-2.5-flash":   {"input": 0.075, "output": 0.30},
    "deepseek/deepseek-chat":      {"input": 0.027, "output": 0.27},
    "zhipu/glm-4-flash":         {"input": 0.07, "output": 0.07},
    "minimax/M2.7-32k":          {"input": 0.07, "output": 0.14},
    "minimax/M2.7-32k-highspeed":{"input": 0.07, "output": 0.14},
    "minimax/M2-ultra-32k":      {"input": 0.35, "output": 1.4},
    "custom:zai":                 {"input": 2.0, "output": 8.0},
}
DEFAULT = {"input": 1.5, "output": 7.0}


def get_price(model: str) -> dict:
    if not model:
        return DEFAULT
    ml = model.lower()
    for key, val in PRICING.items():
        if key.lower() in ml:
            return val
    return DEFAULT


def calc_cost(prompt_toks: int, completion_toks: int, model: str) -> float:
    p = get_price(model)
    return (prompt_toks / 1_000_000 * p["input"] +
            completion_toks / 1_000_000 * p["output"])


def q(sql: str, params=()):
    with sqlite3.connect(DB) as conn:
        conn.row_factory = sqlite3.Row
        return conn.execute(sql, params).fetchall()


def cmd_stats(days: int = 7):
    rows = q("SELECT * FROM llm_traces WHERE timestamp >= datetime('now', ?)", (f"-{days} days",))
    if not rows:
        print(f"近 {days} 天无数据"); return
    total = len(rows)
    ok = sum(1 for r in rows if r["status"] == "success")
    err = sum(1 for r in rows if r["status"] == "error")
    lats = [r["latency_ms"] for r in rows if r["latency_ms"]]
    avg_lat = sum(lats)/len(lats) if lats else 0
    p95 = sorted(lats)[int(len(lats)*0.95)] if lats else 0
    pt = sum(r["prompt_tokens"] or 0 for r in rows)
    ct = sum(r["completion_tokens"] or 0 for r in rows)
    cost = sum(r["cost_usd"] or 0 for r in rows)
    print(f"=== Hermes LLM 可观测性 | 近 {days} 天 ===\n")
    print(f"总调用:   {total}")
    print(f"成功率:  {ok}/{total} ({ok/total*100:.1f}%)")
    print(f"错误:     {err} ({err/total*100:.1f}%)")
    print(f"延迟:     avg={avg_lat:.0f}ms  p95={p95:.0f}ms")
    print(f"Token:    输入={pt:,}  输出={ct:,}")
    print(f"成本:     ${cost:.4f}")


def cmd_daily(days: int = 30):
    rows = q(f"""
        SELECT DATE(timestamp) as day, COUNT(*) as cnt,
               ROUND(SUM(cost_usd),4) as cost, ROUND(AVG(latency_ms),0) as lat
        FROM llm_traces
        WHERE timestamp >= datetime('now', '-{days} days')
        GROUP BY day ORDER BY day
    """)
    print(f"=== 每日趋势 | 近 {days} 天 ===\n")
    print(f"{'日期':<14} {'调用':>6} {'成本':>10} {'延迟':>10}")
    print("-" * 44)
    for r in rows:
        print(f"{r['day']:<14} {r['cnt']:>6} ${r['cost'] or 0:>9.4f} {r['lat'] or 0:>9.0f}ms")


def cmd_providers():
    rows = q("""
        SELECT provider, model, COUNT(*) as cnt,
               ROUND(AVG(latency_ms),0) as lat,
               SUM(prompt_tokens) as pt, SUM(completion_tokens) as ct
        FROM llm_traces
        GROUP BY provider, model ORDER BY cnt DESC
    """)
    print("=== Provider / Model 分布 ===\n")
    hdr = f"{'Provider':<20} {'Model':<30} {'次数':>6} {'延迟':>8} {'Prompt':>10} {'Completion':>10}"
    print(hdr); print("-" * len(hdr))
    for r in rows:
        print(f"{r['provider'] or '':<20} {r['model'] or '':<30} {r['cnt']:>6} "
              f"{r['lat'] or 0:>7.0f}ms {r['pt'] or 0:>10,} {r['ct'] or 0:>10,}")


def cmd_errors(days: int = 7):
    rows = q("""
        SELECT timestamp, provider, model, error, latency_ms
        FROM llm_traces
        WHERE status='error' AND timestamp >= datetime('now', ?)
        ORDER BY timestamp DESC
    """, (f"-{days} days",))
    print(f"=== 错误记录 | 近 {days} 天 ({len(rows)} 条) ===\n")
    for r in rows:
        print(f"[{r['timestamp']}] {r['provider']}/{r['model']}")
        print(f"  {str(r['error'] or '')[:120]}")
        print()


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Hermes LLM 可观测性")
    p.add_argument("--stats", action="store_true")
    p.add_argument("--daily", action="store_true")
    p.add_argument("--providers", action="store_true")
    p.add_argument("--errors", action="store_true")
    p.add_argument("--days", type=int, default=7)
    args = p.parse_args()
    if args.daily: cmd_daily(args.days)
    elif args.providers: cmd_providers()
    elif args.errors: cmd_errors(args.days)
    else: cmd_stats(args.days)
