#!/bin/bash
# 一键起 1688 找品用的后台隐藏 CDP Chrome + 注入默认 Chrome 的登录 cookie。
# 不抢焦点（open -n -g -j），不弹窗，不落盘明文 cookie。
set -u
PORT=9222
PROFILE="$HOME/chrome-cdp-profile"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

echo "[1/4] 拉起后台隐藏 CDP Chrome (-n -g -j, 不抢焦点) ..."
open -n -g -j -a "Google Chrome" \
  --args --remote-debugging-port=$PORT \
  --remote-allow-origins='*' \
  --user-data-dir="$PROFILE" about:blank
# 等 9222 起来
for i in $(seq 1 20); do
  if curl -s "http://127.0.0.1:$PORT/json/version" >/dev/null 2>&1; then
    echo "      ✓ 9222 UP"
    break
  fi
  sleep 0.5
done
curl -s "http://127.0.0.1:$PORT/json/version" >/dev/null 2>&1 || { echo "✗ 9222 未起，检查 Chrome"; exit 1; }

echo "[2/4] 注入默认 Chrome 的 1688/taobao 登录 cookie (不落盘) ..."
python3 "$(dirname "$0")/inject_cookies.py" $PORT

echo "[3/4] 自检 9222 可用性 ..."
curl -s "http://127.0.0.1:$PORT/json/version" | python3 -c "import sys,json;d=json.load(sys.stdin);print('      ✓',d.get('Browser'))"
echo "[4/4] 完成。现在可直接跑: python3 scripts/cdp1688.py --dims \"25*13*32\" --cat \"牛皮纸手提袋\" ..."
