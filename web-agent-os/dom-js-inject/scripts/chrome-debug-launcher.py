#!/usr/bin/env python3
"""
启动 chrome-debug Chrome 并开放 9333 调试端口
用 Playwright persistent_context 实现，保持 9333 端口监听
"""
import socket, sys, time
from playwright.sync_api import sync_playwright

CDP_PORT = 9333

def port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

if port_in_use(CDP_PORT):
    print(f"✅ 端口 {CDP_PORT} 已被占用，Chrome debug 已运行")
    sys.exit(0)

print("🚀 启动 Chrome debug...")
p = sync_playwright().start()
ctx = p.chromium.launch_persistent_context(
    '/Users/aimac/.hermes/chrome-debug',
    headless=True,
    args=[f'--remote-debugging-port={CDP_PORT}', '--no-first-run', '--no-default-browser-check']
)
print(f"✅ Chrome debug 运行中，端口 {CDP_PORT} 已开放")
print(f"   页面数: {len(ctx.pages)}")

while True:
    time.sleep(3600)
