# CDP WebSocket 原生 Python — 实测验证代码（2026-05-14）

## 实测结果

```
WS握手: OK
Step 1: 页面 Links | https://httpbin.org/links/10/0 | 元素9 | 状态:9deebcb1cab9
选中: '1' score=inf | 验证✓ URL变化 → https://httpbin.org/links/10/1
Step 2: 页面 Links | https://httpbin.org/links/10/1 | 元素9 | 状态:33475330b1ed
选中: '0' score=inf | 验证✓ URL变化 → https://httpbin.org/links/10/0
图节点:2, 边:2, 记忆条目:2
```

## 完整可运行代码

```python
import socket, os, json, struct, base64, time, threading, urllib.request, random, math, hashlib

CDP_HOST, CDP_PORT = "127.0.0.1", 9333

def get_target():
    with urllib.request.urlopen(f"http://{CDP_HOST}:{CDP_PORT}/json", timeout=5) as r:
        for t in json.loads(r.read()):
            if t.get("type") == "page": return t["id"], t.get("url")
    return None, None

tid, url = get_target()
s = socket.socket(); s.settimeout(20); s.connect((CDP_HOST, CDP_PORT))
PATH = f"/devtools/page/{tid}"
key = base64.b64encode(os.urandom(16)).decode()
hs = f"GET {PATH} HTTP/1.1\r\nHost: {CDP_HOST}:{CDP_PORT}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
s.sendall(hs.encode())
resp = b""
while b"\r\n\r\n" not in resp: resp += s.recv(4096)

results, mid = {}, [0]
def recv_loop():
    while True:
        try:
            h = s.recv(2)
            if not h: break
            l = h[1] & 0x7F
            if l == 126: l = struct.unpack(">H", s.recv(2))[0]
            elif l == 127: l = struct.unpack(">Q", s.recv(8))[0]
            p = b""
            while len(p) < l: p += s.recv(l - len(p))
            try:
                m = json.loads(p.decode())
                if m.get("id") is not None: results[m["id"]] = m
            except: pass
        except: break
t = threading.Thread(target=recv_loop, daemon=True); t.start()
time.sleep(0.3)

def cdp(method, params=None, timeout=15):
    m = mid[0]; mid[0] += 1; ev = threading.Event(); results["_e"+str(m)] = ev
    p = json.dumps({"id": m, "method": method, "params": params or {}})
    mk = os.urandom(4); ms = bytearray(c ^ mk[i%4] for i,c in enumerate(p.encode()))
    fr = bytearray([0x81])
    if len(p) < 126: fr.append(0x80 | len(p))
    elif len(p) < 65536: fr.append(0xFE); fr.extend(struct.pack(">H", len(p)))
    else: fr.append(0xFF); fr.extend(struct.pack(">Q", len(p)))
    fr.extend(mk); fr.extend(ms); s.sendall(bytes(fr))
    ev.wait(timeout); results.pop("_e"+str(m), None)
    return results.pop(m, {})

# State Embedding
def encode_state(page_info, clickables):
    parts = [(page_info.get("title") or "").strip().lower()[:30], str(page_info.get("linkCount", 0))]
    texts = sorted([(c.get("text") or "").strip()[:20] for c in clickables])[:10]
    parts.extend(texts)
    return hashlib.md5("|".join(parts).encode()).hexdigest()[:12]

# WorldGraph
class WorldGraph:
    def __init__(self):
        self.nodes = {}; self.edges = {}; self.transitions = {}
    def add_node(self, se, pi, cl):
        if se not in self.nodes: self.nodes[se] = {"page_info": pi, "actions": [c.get("text","")[:50] for c in cl], "visits": 0}
        self.nodes[se]["visits"] += 1
    def add_edge(self, fs, act, ts, r=0.0):
        self.edges[(fs, act)] = ts
        t = self.transitions.setdefault(fs, {}).setdefault(act, {"s":0,"a":0,"r":0.0})
        t["a"] += 1; t["r"] += r
        if r > 0: t["s"] += 1
    def stats(self, fs, act):
        return self.transitions.get(fs, {}).get(act, {"s":0,"a":0,"r":0.0})

# Constrained UCB1
class ConstrainedUCB1:
    def __init__(self, wg, c=1.414): self.wg = wg; self.c = c
    def score(self, fs, act):
        st = self.wg.stats(fs, act); a = st["a"]
        if a == 0: return float("inf")
        total = sum(t["a"] for t in self.wg.transitions.get(fs, {}).values())
        return (st["r"]/a) + self.c * math.sqrt(math.log(total+1)/a)

# GoalController
class GoalController:
    def __init__(self, gc): self.gc = gc; self.depth = 0
    def allowed(self, candidates):
        return [c for c in candidates if not any(kw in (c.get("text") or "").lower() for kw in self.gc.get("forbidden_keywords",[]))]
    def step(self): self.depth += 1
    def reset(self): self.depth = 0

# Verifier
def verify(before_url, after_url, before_cl, after_cl, target_text):
    if after_url != before_url: return True, f"URL变化"
    diff = abs(len(before_cl) - len(after_cl))
    if diff >= 3: return True, f"DOM变化({diff})"
    bt = {c.get("text","") for c in before_cl}; at = {c.get("text","") for c in after_cl}
    if target_text in bt and target_text not in at: return True, "目标消失"
    return False, "无变化"

# HumanizationLayer
class HumanizationLayer:
    def __init__(self, cfg): self.cfg = cfg
    def delay(self): time.sleep(random.uniform(self.cfg["min_delay"], self.cfg["max_delay"]))
    def scroll(self, cdp_fn):
        if random.random() > self.cfg["scroll_before_click"]: return
        cdp_fn("Runtime.evaluate", {"expression": "window.scrollBy(0,200)", "returnByValue": False})
        time.sleep(0.4)
    def apply(self, action, cdp_fn):
        self.delay(); self.scroll(cdp_fn)

# MemorySystem
MEM_FILE = "/tmp/hermes_os_memory.json"
class MemorySystem:
    def __init__(self):
        self.data = {}
        if os.path.exists(MEM_FILE):
            try: self.data = json.load(open(MEM_FILE))
            except: pass
    def record(self, se, act, ok, r=0.0):
        d = self.data.setdefault(se, {}).setdefault(act, {"s":0,"a":0,"r":0.0})
        d["a"] += 1
        if ok: d["s"] += 1
        d["r"] = d.get("r",0)+r
        json.dump(self.data, open(MEM_FILE,"w"), ensure_ascii=False)

# === INIT ===
wg = WorldGraph(); ucb1 = ConstrainedUCB1(wg)
gc = GoalController({"forbidden_keywords": ["广告","博彩","赌博"], "max_depth": 50})
hl = HumanizationLayer({"min_delay": 0.3, "max_delay": 1.0, "scroll_before_click": 0.3})
mem = MemorySystem()

# === 完整循环 ===
# （获取页面 → 编码 → UCB1选动作 → humanize → 执行 → 验证 → 更新）
# 见 hermes_web_agent_os.py

s.close()
```

## WebSocket 帧格式要点

```
发送帧: 0x81 + 0x80|length + 4字节mask + payload^mask
长度<126:  1字节长度
长度<65536: 0xFE + 2字节big-endian
长度≥65536: 0xFF + 8字节big-endian
```

## 关键坑

1. **页面导航后 Target detach**：每次 Page.navigate 后重新 get_target()
2. **mask byte 计算**：payload 长度在 126-65535 时用 0xFE，但之前版本错误地先设了 0x80 导致协议错
3. **recv线程必须 daemon**：否则主线程退出后子线程卡住
