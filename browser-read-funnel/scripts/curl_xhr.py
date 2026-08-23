#!/usr/bin/env python3
"""L2 零截图读取：直接重放网页消费的 XHR/REST 端点，拿后端原始 JSON。

用法:
  python3 curl_xhr.py "<url>" [field.path ...]
  python3 curl_xhr.py "<url>" --cookie "cookie.txt" "hits.0.title"
  python3 curl_xhr.py "<url>" -H "Authorization: Bearer xxx" "data.0.name"

为什么比 DOM 截图更好 (pickuma 实战):
  - 现代 SPA 数据在 JS 消费的 XHR/fetch JSON 里，跳过浏览器直接拿干净结构
  - XHR 比 DOM 抗前端重构 (DOM 9个月坏6次, XHR 只坏2次且 schema 会 loudly 报错)
  - 零截图 / 零 OCR / 零浏览器窗口依赖

登录态用法:
  - 从浏览器 DevTools → Network 复制请求的 Cookie 头, 存成 cookie.txt (raw header 值)
  - 或 -H "Cookie: ..." 直接传
  - 只读路径优先; 副作用路径(创建/删除/支付)禁止重放
  - 重放风险: nonce/CSRF/签名URL/Service Worker 可能让重放不安全
  - 安全铁律: Cookie 仅在运行时读取, 不落盘/不进 memory/不回显到对话以外; 用完即弃
"""
import sys, json, subprocess, shlex, argparse

def dig(obj, path):
    for k in path.split('.'):
        if isinstance(obj, dict):
            obj = obj.get(k)
        elif isinstance(obj, list) and k.isdigit():
            obj = obj[int(k)]
        else:
            return None
    return obj

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("fields", nargs="*", help="field paths e.g. hits.0.title")
    ap.add_argument("--cookie", help="path to file containing raw Cookie header value")
    ap.add_argument("-H", "--header", action="append", default=[], help="extra header, e.g. 'Authorization: Bearer x'")
    ap.add_argument("--max", type=int, default=2000, help="max chars of full dump when no fields")
    args = ap.parse_args()

    curl = ["curl", "-s", "-m15", args.url]
    if args.cookie:
        with open(args.cookie) as f:
            curl += ["-H", f"Cookie: {f.read().strip()}"]
    for h in args.header:
        curl += ["-H", h]

    try:
        raw = subprocess.run(curl, capture_output=True, text=True, timeout=20).stdout
        data = json.loads(raw)
    except FileNotFoundError:
        print("ERR: cookie file not found")
        sys.exit(1)
    except json.JSONDecodeError:
        print("ERR: response not JSON (maybe login wall / anti-bot). first 500 chars:")
        print(raw[:500])
        sys.exit(1)
    except Exception as e:
        print(f"ERR: {e}")
        sys.exit(1)

    if not args.fields:
        print(json.dumps(data, ensure_ascii=False, indent=2)[:args.max])
    else:
        for f in args.fields:
            print(f"{f} = {json.dumps(dig(data, f), ensure_ascii=False)[:400]}")

if __name__ == "__main__":
    main()
