#!/usr/bin/env python3
"""
cua_gui_ops.py — cua-driver 的 GUI 操作包装（v2，2026-06-07 重构）

v1 → v2 进化：
  - v1 (cua_extract.py) 想用 cua-driver 抓 JS 渲染页 → 撞 Chrome AppleScript JS 关闭
  - v2 拆开：cua-driver 只做 GUI 操作（launch_app/click/hotkey/type_text），
    抓页完全交给 Playwright（playwright_extract.py）

为什么不直接调 mcp__cua_driver__* MCP 工具？
  - MCP 工具只在 Hermes 会话里能用，cron / subagent / 脚本调不到
  - 这个 CLI 包装让任何 Python/脚本/AI agent 都能调 cua-driver

cua-driver 状态（2026-06-07 实测）：
  - ~/.local/bin/cua-driver v0.5.1
  - Accessibility + Screen Recording 全 Granted
  - 后台驱动，**不抢用户光标/焦点**
"""
import sys
import os
import json
import subprocess
import argparse
from typing import Any

CUA_DRIVER = os.path.expanduser("~/.local/bin/cua-driver")
if not os.path.isfile(CUA_DRIVER):
    CUA_DRIVER = "/usr/local/bin/cua-driver"


def cua_call(tool_name: str, **kwargs) -> dict:
    """调 cua-driver MCP 工具（stdin 传 JSON args）"""
    try:
        result = subprocess.run(
            [CUA_DRIVER, "call", tool_name],
            input=json.dumps(kwargs),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            try:
                return {"ok": True, "data": json.loads(result.stdout)}
            except json.JSONDecodeError:
                return {"ok": True, "data": result.stdout}
        return {"ok": False, "error": result.stderr or result.stdout}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timeout"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ── 通用 GUI 操作（按 cua-driver 工具名一一对应）────────────

def launch_app(bundle_id: str, urls: list[str] | None = None, creates_new: bool = False) -> dict:
    """后台启动 app（不抢焦点）"""
    kwargs: dict[str, Any] = {"bundle_id": bundle_id}
    if urls:
        kwargs["urls"] = urls
    if creates_new:
        kwargs["creates_new_application_instance"] = True
    return cua_call("launch_app", **kwargs)


def click(pid: int, window_id: int, element_index: int) -> dict:
    """点 AX 元素（首选，不会因窗口移动失效）"""
    return cua_call("click", pid=pid, window_id=window_id, element_index=element_index)


def type_text(pid: int, window_id: int, text: str, element_index: int | None = None) -> dict:
    """输入文本（CGEvent 合成，含中文/特殊字符）"""
    kwargs: dict[str, Any] = {"pid": pid, "window_id": window_id, "text": text}
    if element_index is not None:
        kwargs["element_index"] = element_index
    return cua_call("type_text", **kwargs)


def hotkey(pid: int, keys: list[str], window_id: int | None = None) -> dict:
    """按组合键（例 ['cmd', 'c']）"""
    kwargs: dict[str, Any] = {"pid": pid, "keys": keys}
    if window_id is not None:
        kwargs["window_id"] = window_id
    return cua_call("hotkey", **kwargs)


def press_key(pid: int, key: str, window_id: int | None = None) -> dict:
    """按单键（return/escape/tab/up/down/left/right/space/delete 等）"""
    kwargs: dict[str, Any] = {"pid": pid, "key": key}
    if window_id is not None:
        kwargs["window_id"] = window_id
    return cua_call("press_key", **kwargs)


def list_apps() -> dict:
    """列所有 app（含已安装未启动）"""
    return cua_call("list_apps")


def list_windows(pid: int, on_screen_only: bool = False) -> dict:
    """列某 app 的窗口"""
    return cua_call("list_windows", pid=pid, on_screen_only=on_screen_only)


def get_window_state(pid: int, window_id: int, query: str | None = None) -> dict:
    """拿窗口 AX 树（要点击的 element_index 来自这里）"""
    kwargs: dict[str, Any] = {"pid": pid, "window_id": window_id}
    if query:
        kwargs["query"] = query
    return cua_call("get_window_state", **kwargs)


# ── 完整 GUI 任务示例 ──────────────────────

def gui_open_url(url: str, browser: str = "com.google.Chrome") -> dict:
    """后台开 URL 到指定浏览器（不抢焦点）"""
    return launch_app(bundle_id=browser, urls=[url])


# ── CLI ──────────────────────

def main():
    ap = argparse.ArgumentParser(description="cua-driver GUI 操作包装（v2）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    # launch
    p = sub.add_parser("launch", help="启动 app")
    p.add_argument("--bundle-id", required=True)
    p.add_argument("--url", action="append", help="打开 URL（可多次）")
    p.add_argument("--new", action="store_true", help="强制新实例")

    # list-apps
    sub.add_parser("list-apps", help="列所有 app")

    # list-windows
    p = sub.add_parser("list-windows", help="列某 app 窗口")
    p.add_argument("--pid", type=int, required=True)
    p.add_argument("--on-screen-only", action="store_true")

    # click
    p = sub.add_parser("click", help="点 AX 元素")
    p.add_argument("--pid", type=int, required=True)
    p.add_argument("--window-id", type=int, required=True)
    p.add_argument("--element", type=int, required=True)

    # type
    p = sub.add_parser("type", help="输入文本")
    p.add_argument("--pid", type=int, required=True)
    p.add_argument("--window-id", type=int, required=True)
    p.add_argument("--text", required=True)
    p.add_argument("--element", type=int)

    # hotkey
    p = sub.add_parser("hotkey", help="按组合键")
    p.add_argument("--pid", type=int, required=True)
    p.add_argument("--keys", nargs="+", required=True, help="例: cmd c")
    p.add_argument("--window-id", type=int)

    # open-url（高层便捷）
    p = sub.add_parser("open-url", help="后台开 URL 到浏览器")
    p.add_argument("--url", required=True)
    p.add_argument("--browser", default="com.google.Chrome")

    args = ap.parse_args()

    print(f"📦 cua-driver: {CUA_DRIVER} {'✅' if os.path.isfile(CUA_DRIVER) else '❌'}",
          file=sys.stderr)

    if args.cmd == "launch":
        result = launch_app(args.bundle_id, urls=args.url, creates_new=args.new)
    elif args.cmd == "list-apps":
        result = list_apps()
    elif args.cmd == "list-windows":
        result = list_windows(args.pid, on_screen_only=args.on_screen_only)
    elif args.cmd == "click":
        result = click(args.pid, args.window_id, args.element)
    elif args.cmd == "type":
        result = type_text(args.pid, args.window_id, args.text, args.element)
    elif args.cmd == "hotkey":
        keys = ["cmd" if k == "cmd" else k for k in args.keys]
        result = hotkey(args.pid, keys, args.window_id)
    elif args.cmd == "open-url":
        result = gui_open_url(args.url, args.browser)
    else:
        ap.error("unknown command")

    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get("ok") else 1)


if __name__ == "__main__":
    main()
