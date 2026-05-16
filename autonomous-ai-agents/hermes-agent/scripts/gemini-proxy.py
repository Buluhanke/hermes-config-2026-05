#!/usr/bin/env python3
"""
Google Gemini 本地代理 — 解决 Google OpenAI 兼容端点的双 Auth 问题。

问题：Google Gemini 的 OpenAI 兼容端点要求 API key 同时出现在：
  1. URL ?key= 参数
  2. Authorization: Bearer <key> header

但 Hermes 标准 OpenAI 格式只能从 header 取 Bearer token，无法同时满足。

解决方案：本地代理监听 http://127.0.0.1:8899，接收 Hermes 请求，
将 Authorization header 里的 Bearer token 替换为真实 GEMINI_API_KEY，
同时构造正确的 Google API URL（?key= 在参数里）。

用法：
  export GEMINI_API_KEY=你的key
  python3 gemini-proxy.py

然后在 config.yaml 里配置 provider：
  providers:
    gemini:
      api_key: fake  # 随便填，代理处理真实 key
      base_url: http://127.0.0.1:8899/v1

注意：代理必须在 gateway 之前启动。gateway 重启后代理仍然需要运行。
"""
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.request
import urllib.error

PORT = int(os.environ.get("GEMINI_PROXY_PORT", "8899"))
GEMINI_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")
GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/openai"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stdout.write(f"[gemini-proxy] {fmt % args}\n")
        sys.stdout.flush()

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "ok",
            "proxy": "gemini-proxy",
            "key_set": bool(GEMINI_KEY)
        }).encode())

    def do_POST(self):
        if not GEMINI_KEY:
            self.send_error(500, "GEMINI_API_KEY not set")
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body)
            model = data.get("model", "gemini-2.5-flash")
        except Exception:
            model = "gemini-2.5-flash"

        # Google 要求：key 同时在 URL 参数和 Authorization header
        url = f"{GEMINI_BASE}/chat/completions?key={GEMINI_KEY}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GEMINI_KEY}",
        }

        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = resp.read()
                self.send_response(resp.status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(result)
        except urllib.error.HTTPError as e:
            err_body = e.read()
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(err_body)
        except Exception as e:
            self.send_error(500, str(e))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()


if __name__ == "__main__":
    if not GEMINI_KEY:
        print("⚠️  GEMINI_API_KEY not set. Set with: export GEMINI_API_KEY=...")
    print(f"[gemini-proxy] Starting on http://127.0.0.1:{PORT}")
    server = HTTPServer(("127.0.0.1", PORT), Handler)
    server.serve_forever()
