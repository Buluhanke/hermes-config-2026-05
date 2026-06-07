#!/usr/bin/env python3
"""
Hermes 跨平台 Agent 状态广播 — 一键可重入脚本

用法:
  python3 status_broadcast.py

环境:
  - HERMES_PLATFORM 可选, 设了会被 agent_status.py 识别为对应平台
  - cron 建议每 15 分钟跑一次: */15 * * * * python3 ~/.hermes/skills/devops/hermes-agent-status-monitor/scripts/status_broadcast.py
"""
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HOME = Path.home()
STATUS_FILE = HOME / ".hermes" / ".agent_status.json"
SKILL_REGISTRY = HOME / ".hermes" / ".skill_registry.json"
AGENT_STATUS = HOME / ".hermes" / "scripts" / "agent_status.py"

# 与 agent_status.py skill_summary() 内部硬编码一致
CORE_SKILLS = [
    "hermes-agent", "browser-automation", "hermes-cdp-hardcore-type",
    "hermes-vision-agent", "hermes-memory-hpc", "unified-search-routing",
    "devops", "free-model-scanner", "hermes-humanization-core",
    "anysearch", "last30days", "cdp-browser-automation",
    "hermes-reactor-v2", "auto-self-healing", "skill-creator",
]

PLATFORM_EMOJI = {
    "telegram": "🔵Telegram",
    "weixin": "🟢WeChat",
    "wechat": "🟢WeChat",
    "qq": "🟡QQ",
    "qqbot": "🟡QQ",
    "unknown": "⚪cron",
    "cron": "⚪cron",
}

ONLINE_WINDOW_SEC = 300  # 5 分钟内更新算在线


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30)


def main():
    # 1. 抓 raw data
    list_out = run(["python3", str(AGENT_STATUS), "list"]).stdout
    skill_out = run(["python3", str(AGENT_STATUS), "skill_summary"]).stdout

    # 2. 解析总技能数 + 核心技能数
    total_skills = 0
    for line in skill_out.splitlines():
        if "Hermes 共享技能库（共" in line:
            try:
                total_skills = int(line.split("共")[1].split("个")[0].strip())
            except (IndexError, ValueError):
                pass
            break

    registry = json.loads(SKILL_REGISTRY.read_text()) if SKILL_REGISTRY.exists() else {}
    current_skills = set(registry.get("skills", {}).keys())
    if not total_skills:
        total_skills = len(current_skills)
    core_count = sum(1 for s in CORE_SKILLS if s in current_skills)

    # 3. 读状态文件，分离 agents 和 _meta
    if STATUS_FILE.exists():
        try:
            status = json.loads(STATUS_FILE.read_text())
        except Exception:
            status = {}
    else:
        status = {}

    agents = {k: v for k, v in status.items() if k != "_meta"}
    prev_meta = status.get("_meta", {}).get("last_broadcast", {})
    prev_skill_list = set(prev_meta.get("skill_list", []))

    # 4. 在线 agent（5 分钟内）
    now = datetime.now()
    online_agents = []
    for aid, info in agents.items():
        try:
            dt = datetime.fromisoformat(info.get("updated", ""))
            if (now - dt).total_seconds() < ONLINE_WINDOW_SEC:
                online_agents.append((aid, info))
        except Exception:
            pass

    platforms_active = sorted(set(info.get("platform", "?") for _, info in online_agents))
    agents_online = len(online_agents)

    # 5. skill diff
    if prev_skill_list:
        new_skills = sorted(current_skills - prev_skill_list)
        removed_skills = sorted(prev_skill_list - current_skills)
    else:
        new_skills = []
        removed_skills = []

    # 6. 报告
    time_str = now.strftime("%H:%M")
    platforms_str = " / ".join(PLATFORM_EMOJI.get(p, p) for p in platforms_active) or "（无）"
    new_line = ""
    if new_skills:
        head = ", ".join(new_skills[:8])
        tail = f" 等 {len(new_skills)} 个" if len(new_skills) > 8 else ""
        new_line = f"\n🆕 新增：{head}{tail}"
    if removed_skills:
        head = ", ".join(removed_skills[:5])
        new_line += f"\n🗑️ 移除：{head}"

    report = (
        f"📡 Hermes 状态广播 @ {time_str}\n"
        f"👥 在线 agent: {agents_online} | 平台: {platforms_str}\n"
        f"🔥 核心技能 {core_count} 个 | 📦 总计 {total_skills} 个技能"
        f"{new_line}"
    )

    # 7. 写 _meta（不污染 agents 顶层）
    new_status = dict(agents)
    new_status["_meta"] = {
        "last_broadcast": {
            "time": time_str,
            "iso": now.isoformat(),
            "agents_online": agents_online,
            "platforms": platforms_active,
            "core_skills": core_count,
            "total_skills": total_skills,
            "skill_list": sorted(current_skills),
            "new_skills": new_skills,
            "removed_skills": removed_skills,
            "report": report,
        },
        "generated": now.isoformat(),
    }
    STATUS_FILE.write_text(json.dumps(new_status, ensure_ascii=False, indent=2))

    # 8. 广播
    broadcast_msg = f"📡 {time_str} 状态广播：{agents_online} 个 agent 在线 | 核心技能 {core_count} | 总技能 {total_skills}"
    announce_result = run(["python3", str(AGENT_STATUS), "announce", broadcast_msg])

    # 9. 输出
    print("=" * 60)
    print(report)
    print("=" * 60)
    print(f"\n✅ {STATUS_FILE} 已更新 (agents={len(agents)}, online={agents_online})")
    print(f"   core={core_count} | total={total_skills} | new={len(new_skills)} | removed={len(removed_skills)}")
    if announce_result.stdout:
        print(f"\n广播: {announce_result.stdout.strip()}")
    if announce_result.returncode != 0:
        print(f"⚠️ announce 失败: {announce_result.stderr}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
