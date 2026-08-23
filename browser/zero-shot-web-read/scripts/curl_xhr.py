#!/usr/bin/env python3
"""L2 零截图读取：直接重放网页消费的 XHR/REST 端点，拿后端原始 JSON。

用法:
  python3 curl_xhr.py "<url>" [field.path ...]

为什么比 DOM 截图更好 (pickuma 实战):
  - 现代 SPA 数据在 JS 消费的 XHR/fetch JSON 里，跳过浏览器直接拿干净结构
  - XHR 比 DOM 抗前端重构 (DOM 9个月坏6次, XHR 只坏2次且 schema 会 loudly 报错)
  - 零截图 / 零 OCR / 零浏览器窗口依赖

注意:
  - 只读路径优先；副作用路径(创建/删除/支付)禁止重放
  - 需要登录的端点要带 cookie: 加 -H "Cookie: ..."  (从 Network 面板复制)
  - 重放风险: nonce/CSRF/签名URL/Service Worker 可能让重放不安全
"""
import sys, json, subprocess, shlex

def main():
    if len(sys.argv) < 2:
        print("usage: curl_xhr.py <url> [field.path ...]")
        sys.exit(1)
    url = sys.argv[1]
    fields = sys.argv[2:]
    cmd = f'curl -s -m15 {shlex.quote(url)}'
    try:
        raw = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=20).stdout
        data = json.loads(raw)
    except Exception as e:
        print(f"ERR: {e}")
        if 'raw' in dir():
            print(raw[:500])
        sys.exit(1)

    def dig(obj, path):
        for k in path.split('.'):
            if isinstance(obj, dict):
                obj = obj.get(k)
            elif isinstance(obj, list) and k.isdigit():
                obj = obj[int(k)]
            else:
                return None
        return obj

    if not fields:
        print(json.dumps(data, ensure_ascii=False, indent=2)[:2000])
    else:
        for f in fields:
            print(f"{f} = {json.dumps(dig(data, f), ensure_ascii=False)[:400]}")

if __name__ == "__main__":
    main()
