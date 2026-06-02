"""
hermes_vision_click.py — 进化二: 语义锚定 + 动态坐标
原文件: /Users/aimac/.hermes/scripts/hermes_vision_click.py (162行)

用法:
    python3 hermes_vision_click.py deepseek list                 # 列出元素
    python3 hermes_vision_click.py deepseek "开启新对话"          # 关键词点击
    python3 hermes_vision_click.py deepseek "130,90"              # 坐标点击

API (供 reactor 调):
    async def vision_click(ws, tab_id, mode, keyword=None, coord=None)
        → mode="list":   返回 [{tag, text, x, y, hint, role}, ...]
        → mode="click":  keyword 走匹配算法, coord 走物理点击

匹配算法 (按分排序):
    完全匹配 +10, 开头 +5, 包含 +2, 按钮 +2, 短文本 +1, 侧边栏 -5
"""
import subprocess
import sys
import os
import asyncio

# 直接从用户脚本 import (避免复制代码漂移)
sys.path.insert(0, "/Users/aimac/.hermes/scripts")
try:
    from hermes_vision_click import vision_click, list_elements  # type: ignore
except ImportError:
    # 用户脚本未在 path, 用 subprocess 兜底
    vision_click = None
    list_elements = None


async def click_keyword(tab_id: str, keyword: str, ws=None) -> bool:
    """关键词匹配点击 (语义锚定)"""
    if vision_click:
        return await vision_click(ws, tab_id, mode="click", keyword=keyword)
    # 兜底: 调外部脚本
    r = subprocess.run(
        [sys.executable, "/Users/aimac/.hermes/scripts/hermes_vision_click.py",
         tab_id, keyword],
        capture_output=True, text=True, timeout=30
    )
    return r.returncode == 0


async def click_coord(tab_id: str, x: int, y: int, ws=None) -> bool:
    """坐标直接点击 (绕过匹配算法)"""
    if vision_click:
        return await vision_click(ws, tab_id, mode="click", coord=f"{x},{y}")
    r = subprocess.run(
        [sys.executable, "/Users/aimac/.hermes/scripts/hermes_vision_click.py",
         tab_id, f"{x},{y}"],
        capture_output=True, text=True, timeout=30
    )
    return r.returncode == 0


async def enumerate_elements(tab_id: str, ws=None) -> list:
    """列出所有可交互元素"""
    if list_elements:
        return await list_elements(ws, tab_id)
    r = subprocess.run(
        [sys.executable, "/Users/aimac/.hermes/scripts/hermes_vision_click.py",
         tab_id, "list"],
        capture_output=True, text=True, timeout=30
    )
    return r.stdout


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: hermes_vision_click.py <tab_id> <list|keyword|x,y>")
        sys.exit(1)
    tab_id = sys.argv[1]
    arg = sys.argv[2]
    if arg == "list":
        asyncio.run(enumerate_elements(tab_id))
    elif "," in arg:
        x, y = map(int, arg.split(","))
        asyncio.run(click_coord(tab_id, x, y))
    else:
        asyncio.run(click_keyword(tab_id, arg))
