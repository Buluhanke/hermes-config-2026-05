#!/bin/bash
# 1688 找品 CDP 接入：复用用户已登录的常驻实例 (9333, ~/.chrome_1688_scraper)。
# 铁律：9333 在线就直接用，绝不新建实例、绝不注入 cookie、绝不 --headless。
# 只有 9333 完全没起时才用同一个已登录 profile 拉起（登录态仍在，无需重新登录）。
set -u
PORT=9333
PROFILE="$HOME/.chrome_1688_scraper"

if curl -s --max-time 2 "http://127.0.0.1:$PORT/json/version" >/dev/null 2>&1; then
  echo "[OK] $PORT 常驻实例在线，直接复用（不新建、不重注 cookie）"
  curl -s "http://127.0.0.1:$PORT/json/version" | python3 -c "import sys,json;print('     ',json.load(sys.stdin).get('Browser'))"
  exit 0
fi

echo "[!] $PORT 未在线，拉起用户已登录的常驻实例 (headful, -n -g -j, 不抢焦点) ..."
open -n -g -j -a "Google Chrome" \
  --args --remote-debugging-port=$PORT \
  "--remote-allow-origins=*" \
  --user-data-dir="$PROFILE" about:blank
for i in $(seq 1 30); do
  if curl -s --max-time 2 "http://127.0.0.1:$PORT/json/version" >/dev/null 2>&1; then
    echo "      ✓ $PORT UP"
    break
  fi
  sleep 0.5
done
curl -s --max-time 2 "http://127.0.0.1:$PORT/json/version" >/dev/null 2>&1 || { echo "✗ $PORT 未起，检查 Chrome"; exit 1; }
echo "[完成] 复用常驻实例。验证登录态: python3 preflight_1688.py --cdp http://127.0.0.1:$PORT"
