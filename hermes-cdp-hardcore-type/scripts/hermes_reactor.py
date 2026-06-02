"""
hermes_reactor.py — 进化一: Sense → Think → Act 反应堆循环
原文件: /Users/aimac/.hermes/scripts/hermes_reactor.py (155行)

用法:
    python3 hermes_reactor.py deepseek 15    # 跑15秒
    python3 hermes_reactor.py doubao 60      # 跑60秒

API (供高层 Agent 嵌入):
    class Reactor:
        def __init__(self, site, max_seconds=60, period=2.0)
        async def sense(self) -> dict           # 抓 tab 状态
        async def think(self, sense) -> list    # LLM 决策
        async def act(self, decisions) -> list  # 执行 CDP 动作
        async def run(self) -> list             # 循环直到超时
"""
import subprocess
import sys
import asyncio

# 直接从用户脚本 import
sys.path.insert(0, "/Users/aimac/.hermes/scripts")
try:
    from hermes_reactor import Reactor, sense_layer, think_layer, act_layer  # type: ignore
except ImportError:
    Reactor = None
    sense_layer = think_layer = act_layer = None


async def monitor(site: str, seconds: int = 15) -> list:
    """高层接口: 监控一个 AI 站点 N 秒, 返回行动历史"""
    if Reactor:
        r = Reactor(site=site, max_seconds=seconds, period=2.0)
        return await r.run()
    # 兜底: 子进程
    p = subprocess.run(
        [sys.executable, "/Users/aimac/.hermes/scripts/hermes_reactor.py",
         site, str(seconds)],
        capture_output=True, text=True, timeout=seconds + 10
    )
    return p.stdout.splitlines()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: hermes_reactor.py <site> [seconds]")
        sys.exit(1)
    site = sys.argv[1]
    seconds = int(sys.argv[2]) if len(sys.argv) > 2 else 15
    asyncio.run(monitor(site, seconds))
