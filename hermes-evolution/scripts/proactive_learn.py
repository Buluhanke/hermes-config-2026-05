#!/usr/bin/env python3
"""
主动学习引擎 —— 从自身会话经验中学习（区别于被动全网搜新闻）。

核心：扫描最近 24h 会话，提取四类高价值信号：
  1. 用户纠正 (correction)：用户指出做错了/不要这样做 → 提炼为「避坑规则」
  2. 失败教训 (failure)：报错/被拒/翻车后用户或助手的修复 → 提炼为「排障经验」
  3. 成功解法 (solution)：用户确认搞定/可以了的工具链 → 提炼为「可复用做法」
  4. 显式要求 (directive)：用户明确「以后/记住/不要」→ 提炼为「长期约定」

然后过 fact_gate 门控（去重/噪声），合格才写入 fact_store，带 keywords 保证可检索。

零 LLM 依赖，纯 stdlib，跨模型可移植。cron 上下文可直跑（不依赖 fact_store 工具的写权限）。

用法：
  python3 proactive_learn.py              # 默认扫 24h，落库
  python3 proactive_learn.py --dry-run    # 只出候选，不写库
  python3 proactive_learn.py --hours 48   # 扫 48h
"""
import argparse
import datetime
import json
import os
import re
import sqlite3
import subprocess
import sys
import time

HOME = os.path.expanduser("~")
HERMES = os.path.join(HOME, ".hermes")
STATE_DB = os.path.join(HERMES, "state.db")
FACT_STORE = os.path.join(HERMES, "memory_store.db")
FACT_GATE = os.path.join(HERMES, "scripts", "fact_gate.py")

# 信号词 → 类别。只匹配真人用户的「强信号句式」，避免把助手排障自述误判为教训。
# 关键教训：助手消息里满是"报错/失败/修好了"，绝不能从 assistant role 提取经验。
CORRECTION_PAT = re.compile(
    r"(你又在|自欺欺人|乱七八糟|我说了|跟你说过|怎么又|你搞错|你理解错|"
    r"不是[，,]?我要|没让你|谁让你|别自作主张)",
)
DIRECTIVE_PAT = re.compile(
    r"^(以后|记住|从现在起|以后都|以后别|每次都|一律|永远|不要|别再|以后不要|"
    r"不许|必须|铁律|你给我)",
)
# 失败类只认用户「明确抱怨」句式，不认助手的技术叙述
FAILURE_PAT = re.compile(
    r"(怎么又坏|又不行了|还是不行|你刚才|你之前|还是没|一直失败|又挂了|"
    r"没搞定|不对劲|有问题啊|又出问题)",
)
# 成功确认只认用户对结果的认可短句，不认助手自述"修好了"
SOLUTION_PAT = re.compile(
    r"^(好|对|可以|行|OK|ok|完美|就是这样|这个对|好了|搞定)$",
)
# 系统注入前缀，一律剔除
INJECT_PAT = re.compile(r"^(CONTEXT:|\[IMPORTANT:|\[用户|\[系统|You've reached|#)", re.I)

# 噪声过滤：这些不值得写入
NOISE_PAT = re.compile(r"^(CONTEXT:|# |```|\{\"|\[)", re.I)
MIN_LEN, MAX_LEN = 12, 200


def clean(text):
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text).strip()
    return text


def classify(text):
    """返回命中的类别列表（可多类）"""
    hits = []
    if CORRECTION_PAT.search(text):
        hits.append("correction")
    if DIRECTIVE_PAT.search(text):
        hits.append("directive")
    if FAILURE_PAT.search(text):
        hits.append("failure")
    if SOLUTION_PAT.search(text):
        hits.append("solution")
    return hits


def scan(hours):
    cutoff = time.time() - hours * 3600
    db = sqlite3.connect(STATE_DB)
    db.row_factory = sqlite3.Row
    # 取用户消息 + 紧随其后的助手回复（相邻 id）
    rows = db.execute(
        """SELECT m.id, m.session_id, m.role, m.content, m.timestamp, s.source
           FROM messages m LEFT JOIN sessions s ON s.id=m.session_id
           WHERE m.timestamp >= ? AND m.role IN ('user','assistant')
           ORDER BY m.session_id, m.id""",
        (cutoff,),
    ).fetchall()
    db.close()

    # 按 session 分组，构造上下文；只从真人 user 消息提取经验
    by_session = {}
    for r in rows:
        by_session.setdefault(r["session_id"], []).append(r)

    candidates = []
    for sid, msgs in by_session.items():
        for i, m in enumerate(msgs):
            if m["role"] != "user":
                continue  # 铁律：助手自述不是经验来源
            c = clean(m["content"])
            if INJECT_PAT.match(c) or NOISE_PAT.match(c):
                continue
            # 成功确认短句允许短，其余需达标
            is_short_ok = bool(SOLUTION_PAT.match(c))
            if not is_short_ok and (len(c) < MIN_LEN or len(c) > MAX_LEN):
                continue
            hits = classify(c)
            if not hits:
                continue
            # 取后一条助手回复作为"结果"佐证
            follow = ""
            for j in range(i + 1, min(i + 3, len(msgs))):
                if msgs[j]["role"] == "assistant":
                    follow = clean(msgs[j]["content"])[:160]
                    break
            key = (tuple(hits), c[:60])
            candidates.append(
                {
                    "session": sid,
                    "source": m["source"],
                    "categories": hits,
                    "user_text": c,
                    "follow_up": follow,
                    "ts": m["timestamp"],
                    "dedup_key": key,
                }
            )

    # 全局去重
    seen = set()
    uniq = []
    for c in candidates:
        if c["dedup_key"] in seen:
            continue
        seen.add(c["dedup_key"])
        uniq.append(c)
    return uniq


CATEGORY_LABEL = {
    "correction": "用户纠正-避坑规则",
    "failure": "失败教训-排障经验",
    "solution": "成功解法-可复用做法",
    "directive": "长期约定-用户铁律",
}


def to_fact(cand):
    """把候选经验转成 fact content + keywords"""
    cats = cand["categories"]
    label = "/".join(CATEGORY_LABEL[c] for c in cats)
    txt = cand["user_text"]
    follow = cand["follow_up"]
    src = cand["source"] or "session"

    # 只取最有信息量的类别做前缀
    primary = cats[0]
    prefix = {
        "correction": "经验教训·避坑",
        "failure": "经验教训·排障",
        "solution": "经验教训·做法",
        "directive": "经验教训·约定",
    }[primary]

    content = f"{prefix}[{src}·{datetime.date.today().isoformat()}] {txt}"
    if follow and primary == "solution":
        content += f" → 验证:{follow[:80]}"

    # keywords: 类别标签 + 来源 + 文本里的实词（去停用词）
    stop = set("的 了 和 是 在 我 你 这 那 有 就 都 不 也 要 把 给 被 一个 什么 怎么".split())
    words = [w for w in re.split(r"[^\w\u4e00-\u9fff]+", txt) if len(w) >= 2 and w not in stop]
    keywords = [prefix, src] + list(dict.fromkeys(words))[:6]
    return content, "lesson", ",".join(keywords)


def gate_check(content, category, tags):
    """调用 fact_gate 门控。返回 True=accept, False=reject/异常保守放行? 不，保守拒绝"""
    if not os.path.exists(FACT_GATE):
        return True  # 门控脚本缺失时退化为直接写（罕见）
    try:
        p = subprocess.run(
            [sys.executable, FACT_GATE, "check", "--content", content,
             "--category", category, "--tags", tags, "--no-probe"],
            capture_output=True, text=True, timeout=30,
        )
        out = (p.stdout + p.stderr).lower()
        # fact_gate 输出 verdict=accept/review/reject
        m = re.search(r"verdict\s*[=:]\s*(\w+)", out)
        verdict = m.group(1) if m else ""
        return verdict in ("accept", "review")
    except Exception as e:
        print(f"  [gate] 调用失败保守跳过: {e}", file=sys.stderr)
        return False


def write_facts(accepted):
    """直连 SQLite 写入 fact_store（带 keywords 到 tags）"""
    db = sqlite3.connect(FACT_STORE)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    written = 0
    # fact_id 是 INTEGER PRIMARY KEY —— 必须用整数递增 ID，字符串会报
    # "datatype mismatch" 被吞掉，导致每天 0 落库却看似成功（2026-11-25 实测踩坑）
    next_id = db.execute("SELECT COALESCE(MAX(fact_id), 0) + 1 FROM facts").fetchone()[0]
    for content, category, tags in accepted:
        # 查重：完全相同的 content 不重复写
        if db.execute("SELECT 1 FROM facts WHERE content=? LIMIT 1", (content,)).fetchone():
            continue
        try:
            db.execute(
                """INSERT INTO facts
                   (fact_id, content, category, tags, trust_score, retrieval_count,
                    helpful_count, created_at, updated_at)
                   VALUES (?, ?, ?, ?, 0.6, 0, 0, ?, ?)""",
                (next_id + written, content, category, tags, now, now),
            )
            written += 1
        except sqlite3.Error as e:
            print(f"  [write] 跳过: {e}", file=sys.stderr)
    db.commit()
    db.close()
    return written


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=int, default=24)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cands = scan(args.hours)
    print(f"[主动学习] 扫描最近 {args.hours}h，命中 {len(cands)} 条候选经验")

    accepted = []
    for c in cands:
        content, category, tags = to_fact(c)
        ok = gate_check(content, category, tags)
        mark = "✓" if ok else "✗"
        print(f"  {mark} [{','.join(c['categories'])}] {c['user_text'][:70]}")
        if ok:
            accepted.append((content, category, tags))

    print(f"[主动学习] 门控通过 {len(accepted)}/{len(cands)} 条")
    if args.dry_run:
        print("[dry-run] 不写库")
        return
    written = write_facts(accepted)
    print(f"[主动学习] 落库 {written} 条经验教训到 fact_store")


if __name__ == "__main__":
    main()
