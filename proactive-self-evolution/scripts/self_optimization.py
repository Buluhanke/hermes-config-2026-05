#!/usr/bin/env python3
"""
Autoresearch 风格的自我优化循环
定义目标 → 执行 → 评估 → 保留/丢弃 → 重复

使用方式:
  /opt/homebrew/bin/python3 ~/.hermes/scripts/self_optimization.py

Cron配置:
  hermes cron create --name "Hermes自我优化循环" \
    --script self_optimization.py --schedule "0 2 * * *" \
    --no-agent --deliver telegram
"""
import json, time, subprocess
from pathlib import Path
from datetime import datetime

LOG_DIR = Path.home() / ".hermes" / "logs" / "self_optimization"
LOG_DIR.mkdir(parents=True, exist_ok=True)

METRICS_FILE = LOG_DIR / "metrics.json"

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")

def load_metrics():
    if METRICS_FILE.exists():
        return json.loads(METRICS_FILE.read_text())
    return {"total_tasks": 0, "success_tasks": 0, "error_tasks": 0,
            "self_repairs": 0, "skill_improvements": 0, "runs": []}

def save_metrics(m):
    METRICS_FILE.write_text(json.dumps(m, indent=2, ensure_ascii=False))

def github_search(query, sort="stars"):
    """GitHub API 搜索，降级到 ddgs"""
    import urllib.request
    url = f"https://api.github.com/search/repositories?q={query.replace(' ', '+')}&sort={sort}&per_page=5"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read())
            return [(i["full_name"], i["stargazers_count"], i.get("description",""))
                    for i in data.get("items", [])]
    except Exception:
        pass
    # 降级到 ddgs
    try:
        r = subprocess.run(["ddgs", "text", "-q", query, "-m", "5"],
                         capture_output=True, text=True, timeout=30)
        results = []
        for line in r.stdout.splitlines():
            if line.strip() and not line.startswith("#"):
                results.append((line.strip(), 0, ""))
        return results
    except Exception:
        return []

def evaluate_result(name, desc, target_keywords):
    """评估结果是否值得保留"""
    for kw in target_keywords:
        if kw.lower() in (name+desc).lower():
            return True
    return False

def run_self_optimization():
    metrics = load_metrics()
    run_id = len(metrics["runs"]) + 1
    log(f"=== 开始第 {run_id} 轮自我优化 ===")

    search_agenda = [
        {"query": "screen understanding AI agent visual grounding", "domain": "vision"},
        {"query": "desktop computer use agent macos automation", "domain": "cua"},
        {"query": "CAPTCHA bypass AI agent browser automation", "domain": "anti-captcha"},
        {"query": "hermes-agent NousResearch self-evolution", "domain": "agent"},
    ]

    target_keywords = {
        "vision": ["screen", "visual", "desktop", "gui", "ui automation"],
        "cua": ["computer use", "desktop", "agent", "automation", "macos"],
        "anti-captcha": ["captcha", "fingerprint", "detection"],
        "agent": ["agent", "evolution", "self-improve", "hermes"],
    }

    results = {"run_id": run_id, "timestamp": datetime.now().isoformat(),
               "findings": [], "improvements_count": 0}

    for item in search_agenda:
        raw = github_search(item["query"])
        kept = [(n,s,d) for n,s,d in raw if evaluate_result(n, d, target_keywords[item["domain"]])]
        if kept:
            results["findings"].append({"domain": item["domain"], "items": kept})
            results["improvements_count"] += len(kept)
            log(f"  [{item['domain']}] 保留 {len(kept)} 个")

    metrics["runs"].append(results)
    metrics["total_tasks"] += 1
    metrics["skill_improvements"] += results["improvements_count"]
    save_metrics(metrics)
    log(f"=== 第 {run_id} 轮完成: {results['improvements_count']} 个改进 ===")

    # 归档到 Brain_Lab
    brain_lab = Path.home() / "Brain_Lab"
    brain_lab.mkdir(exist_ok=True)
    summary = [f"# 自我优化循环 - 第{run_id}轮\n",
               f"时间: {results['timestamp']}\n", f"改进: {results['improvements_count']}\n\n"]
    for f in results["findings"]:
        summary.append(f"## {f['domain'].upper()}\n")
        for name, stars, desc in f["items"]:
            summary.append(f"- **{name}** ({stars}★)\n  {desc}\n")
    brain_lab.joinpath(f"self_optimization_round{run_id}.md").write_text("".join(summary))

    return results

if __name__ == "__main__":
    r = run_self_optimization()
    print(json.dumps(r, indent=2, ensure_ascii=False))