#!/usr/bin/env python3
"""
verify_critical_step.py — 关键节点视觉验证模板 (复制修改即可用)

来源: 2026-06-29 visual_verifier session
适用: 任何 "点完按钮后, 想确认操作真的生效" 的场景

用法 (复制本文件, 改 expected 和 click 动作):
    python3 verify_critical_step.py \\
        --app "Safari" \\
        --window-id 12345 \\
        --pid 67890 \\
        --expected-text "提交成功" \\
        --expected-no-text "错误" \\
        --action click:element_index=42

设计原则 (Ponytail 6 步):
  1. 截图前 (before) → 触发动作 → 截图后 (after)
  2. diff + OCR + color 一次跑完
  3. 结构化输出 JSON, 可直接喂给 LLM 判断
  4. 失败不抛异常, 永远返回 dict

为什么需要这个模板:
  - AX 拿到 "提交" 按钮并 click, 不代表真提交成功
  - mac_vision_fallback 走 VLM 太重, 关键节点都用 VLM 慢 + 贵
  - visual_verifier 本地 + 400ms 即可, 这就是该走的路
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".hermes" / "scripts"))
from visual_verifier import verify_after_click, verify_state


def screencapture_window(window_id: int, out_path: str) -> bool:
    """截指定窗口 (用 screencapture -l, 不抢前台)"""
    r = subprocess.run(
        ["/usr/sbin/screencapture", "-x", "-l", str(window_id), "-o", out_path],
        capture_output=True, timeout=10,
    )
    return r.returncode == 0 and Path(out_path).exists() and Path(out_path).stat().st_size > 0


def screencapture_full(out_path: str) -> bool:
    """全屏截图 (兜底)"""
    r = subprocess.run(
        ["/usr/sbin/screencapture", "-x", "-t", "png", out_path],
        capture_output=True, timeout=10,
    )
    return r.returncode == 0


def main():
    ap = argparse.ArgumentParser(description="关键节点视觉验证模板")
    ap.add_argument("--app", default="", help="目标 app 名称 (可选, 仅日志)")
    ap.add_argument("--pid", type=int, default=0, help="目标 pid")
    ap.add_argument("--window-id", type=int, default=0, help="目标 window_id (0 = 全屏)")
    ap.add_argument("--expected-text", action="append", default=[],
                    help="期望出现的文字 (可多次传)")
    ap.add_argument("--expected-no-text", action="append", default=[],
                    help="期望不出现的文字 (反向校验)")
    ap.add_argument("--expected-color", default="",
                    help="期望颜色 RGB, 格式 r,g,b")
    ap.add_argument("--action", default="",
                    help="触发动作: click:element_index=N 或 type:text='...'")
    ap.add_argument("--wait-ms", type=int, default=1500,
                    help="动作后等多少 ms 再截 after (默认 1500)")
    ap.add_argument("--before", default="/tmp/_verify_before.png")
    ap.add_argument("--after", default="/tmp/_verify_after.png")
    args = ap.parse_args()

    log = {"ts": int(time.time() * 1000), "app": args.app, "pid": args.pid}

    # 1. 截 before
    cap_fn = (lambda p: screencapture_window(args.window_id, p)) \
        if args.window_id else screencapture_full
    if not cap_fn(args.before):
        log["error"] = f"before screenshot failed: {args.before}"
        print(json.dumps(log, ensure_ascii=False, indent=2))
        sys.exit(1)

    # 2. 触发动作 (这里留空, 实际场景由 cua-driver MCP 完成)
    if args.action:
        log["action"] = args.action
        # 示例: mcp_cua_driver_click(pid=..., element_index=...)
        # 实际由 agent 在 MCP 上下文里执行, 这里只占位

    # 3. 等动画/网络
    time.sleep(args.wait_ms / 1000.0)

    # 4. 截 after
    if not cap_fn(args.after):
        log["error"] = f"after screenshot failed: {args.after}"
        print(json.dumps(log, ensure_ascii=False, indent=2))
        sys.exit(1)

    # 5. verify_after_click (diff + 期望 text)
    expected = {}
    if args.expected_text:
        expected["text"] = args.expected_text
    if args.expected_color:
        rgb = tuple(int(x) for x in args.expected_color.split(","))
        expected["color"] = list(rgb)

    click_result = verify_after_click(args.before, args.after, expected or None)
    log["verify_after_click"] = click_result

    # 6. verify_state (反向校验 no_text)
    if args.expected_no_text:
        checks = [{"type": "no_text", "value": args.expected_no_text, "required": True}]
        if args.expected_text:
            checks.insert(0, {"type": "text", "value": args.expected_text, "required": True})
        state_result = verify_state(args.after, checks)
        log["verify_state"] = state_result
        log["passed"] = state_result.get("success", False) and click_result.get("expected_met", False)
    else:
        log["passed"] = click_result.get("expected_met", False)

    print(json.dumps(log, ensure_ascii=False, indent=2))
    sys.exit(0 if log["passed"] else 2)


if __name__ == "__main__":
    main()