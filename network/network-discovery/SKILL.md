---
name: network-discovery
description: "局域网发现 arp ping端口扫dns-sd mDNS。Use when 摸局域网设备IP开放端口"
triggers:
  - network discovery
  - lan scan
  - 设备发现
  - 局域网
  - 局域网扫描
  - local network scan
author: hermes-agent
version: 1.0.0
tags:
  - network
  - lan
  - discovery
  - arp
  - bonjour
  - mdns
platform: macOS
requirements:
  - python3
  - dns-sd (built-in macOS)
  - arp / arp -a (built-in)
  - ping (built-in)
---

# Network Discovery Skill

局域网设备发现工具集。覆盖 arp 缓存读取、ping 批量扫描、Python socket 端口扫描、dns-sd Bonjour/mDNS 发现，以及静态 ARP 映射管理。

**不依赖 nmap** — 使用纯 Python socket 实现端口扫描。

---

## 目录

1. [前置检查：确认网卡和网段](#1-前置检查确认网卡和网段)
2. [快速发现：arp -a 读取已知设备](#2-快速发现arp--a-读取已知设备)
3. [Ping 批量扫描](#3-ping-批量扫描)
4. [Python 端口扫描](#4-python-端口扫描)
5. [dns-sd mDNS/Bonjour 发现](#5-dns-sd-mdnsbonjour-发现)
6. [静态 ARP 映射](#6-静态-arp-映射)
7. [完整输出格式化](#7-完整输出格式化)
8. [坑点与注意事项](#8-坑点与注意事项)
9. [验证步骤](#9-验证步骤)

---

## 1. 前置检查：确认网卡和网段

```bash
# 列出所有网络接口和当前 IP
ifconfig | grep -E "^[a-z]|inet " | grep -A1 -E "^[a-z]+[0-9]:"

# 示例输出（Mac mini M4 通常是 en0）：
# en0: flags=8863<UP,BROADCAST,SMART,RUNNING,SIMPLEX,MULTICAST> mtu 1500
#     inet 192.168.8.100 --> 192.168.8.1 netmask 0xffffff00 broadcast 192.168.8.255

# 确认当前网段（通常 192.168.8.0/24）
ipconfig getifaddr en0   # 返回本机 IP，例如 192.168.8.100
route -n get default | grep gateway  # 返回网关，例如 192.168.8.1
```

> **坑点：Mac mini M4 可能是双网卡（en0 Wi-Fi + en1 以太网）。**
> 需要同时扫描两个接口。先用 `ifconfig` 确认哪个是活跃网卡。
> en0 通常是 Wi-Fi，en1 是以太网（如果接了转接线）。

---

## 2. 快速发现：arp -a 读取已知设备

```bash
arp -a
```

输出示例：
```
? (192.168.8.1) at aa:bb:cc:dd:ee:ff on en0 permanent [ethernet]
? (192.168.8.100) at ff:ee:dd:cc:bb:aa on en0 permanent [ethernet]
```

**格式化解析（Python）：**
```python
import subprocess
import re

def parse_arp():
    """读取 arp -a 输出，解析 IP、MAC、hostname"""
    result = subprocess.run(["arp", "-a"], capture_output=True, text=True)
    devices = []
    # 匹配格式: hostname (IP) at MAC on iface [ethernet]
    pattern = re.compile(r"\((\d+\.\d+\.\d+\.\d+)\)\s+at\s+([0-9a-f:]+)\s+on\s+(\w+)")
    for line in result.stdout.splitlines():
        m = pattern.search(line)
        if m:
            ip, mac, iface = m.groups()
            hostname = line.split("?")[0].strip() or ip
            devices.append({
                "ip": ip,
                "mac": mac.upper(),
                "hostname": hostname,
                "iface": iface,
                "source": "arp"
            })
    return devices
```

> **坑点：arp -a 只显示本机已经通信过的设备（即 ARP 缓存）。**
> 新上线的设备未通信过则不会出现。需要用 ping 扫描强制填充缓存后再读 arp。

---

## 3. Ping 批量扫描

对整个网段（1-254）并发 ping，填充 ARP 缓存，然后读 `arp -a` 获取完整设备列表。

### 3.1 并发 Ping（推荐）

```bash
# Mac mini M4 / macOS 标准语法
# -c1: 发1个包  -W1: 等待1秒  &> /dev/null: 丢弃输出
SUBNET="192.168.8"
for i in $(seq 1 254); do
  ping -c1 -W1 ${SUBNET}.${i} &> /dev/null &
done
wait
echo "Ping sweep complete — reading ARP cache..."
arp -a
```

### 3.2 带超时的单线程顺序扫描（不稳定网络用）

```bash
SUBNET="192.168.8"
for i in $(seq 1 254); do
  if ping -c1 -W2 ${SUBNET}.${i} &> /dev/null; then
    echo "${SUBNET}.${i} is UP"
  fi
done
```

> **坑点1：macOS 的 ping -W 参数含义与 Linux 不同。**
> macOS 用 `-W timeout`（秒），Linux 用 `-W deadline`。上面命令兼容 macOS。

> **坑点2：大量并发 ping 可能触发防火墙或网络限速。**
> Mac 内置防火墙通常不拦截 ICMP，但如果网络设备有速率限制，254 个并发请求可能被拦截。并发数可降至 32：
> ```bash
> # 分批扫描，每批32个
> for batch_start in $(seq 1 254 | paste -sd " " | tr ' ' '\n' | head -n 254); do
>   for i in $(seq $batch_start $((batch_start+31))); do
>     [ $i -le 254 ] && ping -c1 -W1 ${SUBNET}.${i} &> /dev/null &
>   done
>   wait
> done
> ```

---

## 4. Python 端口扫描

纯 Python socket 扫描常见端口，不依赖 nmap。

### 4.1 快速端口扫描脚本

```python
#!/usr/bin/env python3
"""
lan_scan.py — 局域网端口扫描器
扫描目标 IP 的常见端口：22 (SSH), 80 (HTTP), 445 (SMB), 8080 (HTTP-ALT), 5000 (HTTP-ALT)
"""
import socket
import concurrent.futures
from datetime import datetime

# ---------- 配置 ----------
TARGET_IPS = [f"192.168.8.{i}" for i in range(1, 255)]
COMMON_PORTS = [
    (22, "SSH"),
    (80, "HTTP"),
    (445, "SMB"),
    (8080, "HTTP-ALT"),
    (5000, "HTTP-ALT"),
    (8443, "HTTPS-ALT"),
    (5900, "VNC"),
    (3389, "RDP"),
]
TIMEOUT = 1.0  # 秒
# --------------------------

def scan_port(ip: str, port: int) -> dict | None:
    """扫描单个 IP:端口，返回开放信息或 None"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        result = sock.connect_ex((ip, port))
        sock.close()
        if result == 0:
            return {"ip": ip, "port": port}
    except Exception:
        pass
    return None

def scan_host(ip: str) -> dict:
    """扫描一个 IP 的所有端口"""
    open_ports = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(scan_port, ip, p): p for p, _ in COMMON_PORTS}
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                _, name = COMMON_PORTS[futures[future]]
                open_ports.append({"port": result["port"], "service": name})
    return {"ip": ip, "open_ports": open_ports}

def get_hostname(ip: str) -> str:
    """尝试反解 hostname"""
    try:
        hostname, _, _ = socket.gethostbyaddr(ip)
        return hostname
    except Exception:
        return ip

def scan_subnet():
    """扫描整个网段"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting scan of {len(TARGET_IPS)} IPs...")
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        futures = {executor.submit(scan_host, ip): ip for ip in TARGET_IPS}
        done = 0
        for future in concurrent.futures.as_completed(futures):
            done += 1
            if done % 50 == 0:
                print(f"  Progress: {done}/{len(TARGET_IPS)}")
            result = future.result()
            if result["open_ports"]:
                result["hostname"] = get_hostname(result["ip"])
                results.append(result)
    return sorted(results, key=lambda x: list(map(int, x["ip"].split("."))))

if __name__ == "__main__":
    active_devices = scan_subnet()
    print("\n" + "=" * 60)
    print(f"  LAN SCAN RESULTS — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    if not active_devices:
        print("  No devices with open ports found.")
    for dev in active_devices:
        ports_str = ", ".join(f"{p['port']}/{p['service']}" for p in dev["open_ports"])
        print(f"\n  IP:      {dev['ip']}")
        print(f"  Hostname: {dev['hostname']}")
        print(f"  Ports:   {ports_str}")
    print("\n" + "=" * 60)
```

**运行：**
```bash
python3 lan_scan.py
```

### 4.2 扫描特定 IP

```bash
# 交互式运行：修改 TARGET_IPS 列表，或用命令行参数指定
python3 - <<'EOF'
import socket
def scan(ip, ports=[22,80,445,8080,5000]):
    open_ports = []
    for port in ports:
        try:
            s = socket.socket(); s.settimeout(1)
            if s.connect_ex((ip, port)) == 0: open_ports.append(port)
            s.close()
        except: pass
    return open_ports

ip = "192.168.8.1"  # 改这里
print(f"Scanning {ip}...")
ports = scan(ip)
print(f"Open ports: {ports if ports else 'none found'}")
EOF
```

---

## 5. dns-sd mDNS/Bonjour 发现

dns-sd 是 macOS 内置的 Bonjour/mDNS 服务发现工具。

### 5.1 浏览所有 mDNS 服务

```bash
# 实时浏览（Ctrl+C 停止）
dns-sd -B _services._dns-sd._udp local.

# 同时浏览多个常用服务类型：
dns-sd -B _http._tcp local. &
dns-sd -B _ssh._tcp local. &
dns-sd -B _smb._tcp local. &
dns-sd -B _device-info._tcp local. &
dns-sd -B _airplay._tcp local. &
wait
```

### 5.2 扫描局域网内所有 mDNS 广播

```bash
# 获取局域网内所有发布服务的设备
dns-sd -B _services._dns-sd._udp local.

# 然后对每个发现的实例查询其 IP
dns-sd -L <instance> <service> local.
```

### 5.3 获取本局域网所有 Bonjour 设备（一次性）

```bash
#!/bin/bash
# bonjour_discovery.sh — 一次性收集局域网 mDNS/Bonjour 设备
echo "=== Bonjour/mDNS Discovery ==="
# 触发一次浏览并收集 3 秒内的所有响应
dns-sd -B _services._dns-sd._udp local. 2>&1 | head -20 &
sleep 3
kill %1 2>/dev/null
```

> **坑点1：mDNS 只在本广播域内传播**，跨子网（如 AP/路由隔离）无法发现。
>
> **坑点2：部分设备禁用 Bonjour**（隐私设置关闭），不会出现在 dns-sd 结果中。

---

## 6. 静态 ARP 映射

用于手动指定 IP→MAC 映射，解决 ARP 缓存过期或 ARP 欺骗防护。

```bash
# 添加静态 ARP 条目（需要 sudo）
sudo arp -s 192.168.8.50 aa:bb:cc:dd:ee:ff

# 查看静态条目
arp -a | grep permanent

# 删除静态条目
sudo arp -d 192.168.8.50

# 批量添加（脚本）
cat <<'EOF' | sudo sh
arp -s 192.168.8.50 AA:BB:CC:DD:EE:FF
arp -s 192.168.8.60 11:22:33:44:55:66
EOF
```

> **坑点：静态 ARP 在重启后丢失。** 如需永久生效，使用 `arp -S`（Solaris 语法，macOS 不支持）。macOS 可通过 launchd 或 pf 规则持久化，但较复杂，不建议日常使用。

---

## 7. 完整输出格式化

### 7.1 汇总脚本（推荐工作流）

将所有发现方法的结果合并输出为统一格式：

```python
#!/usr/bin/env python3
"""
lan_discovery.py — 完整局域网发现汇总脚本
整合 arp 缓存 + ping 扫描 + socket 端口扫描
"""
import socket
import subprocess
import re
import concurrent.futures
from datetime import datetime

SUBNET = "192.168.8"
TIMEOUT = 1.0

def ping_host(ip: str) -> bool:
    """ping 一个 IP，成功返回 True"""
    try:
        result = subprocess.run(
            ["ping", "-c1", "-W1", ip],
            capture_output=True, timeout=2
        )
        return result.returncode == 0
    except Exception:
        return False

def get_mac_from_arp(ip: str) -> str:
    """从 arp 缓存中查找 MAC 地址"""
    try:
        result = subprocess.run(["arp", "-a"], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if ip in line:
                m = re.search(r"\(([\d.]+)\)\s+at\s+([0-9a-f:]+)", line)
                if m and m.group(1) == ip:
                    return m.group(2).upper()
    except Exception:
        pass
    return "N/A"

def get_hostname(ip: str) -> str:
    """反向 DNS 解析 hostname"""
    try:
        hostname, _, _ = socket.gethostbyaddr(ip)
        return hostname
    except Exception:
        return ip

def scan_common_ports(ip: str) -> list[dict]:
    """扫描常见端口"""
    ports = [(22,"SSH"),(80,"HTTP"),(445,"SMB"),(8080,"HTTP-ALT"),(5000,"HTTP-ALT")]
    open_ports = []
    for port, name in ports:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(TIMEOUT)
            if s.connect_ex((ip, port)) == 0:
                open_ports.append({"port": port, "service": name})
            s.close()
        except Exception:
            pass
    return open_ports

def discover(subnet: str = SUBNET):
    ips = [f"{subnet}.{i}" for i in range(1, 255)]
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Ping sweeping {subnet}.1–254 ...")

    # 1. 并发 ping 填充 ARP 缓存
    reachable = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as ex:
        futures = {ex.submit(ping_host, ip): ip for ip in ips}
        for f in concurrent.futures.as_completed(futures):
            if f.result():
                reachable.append(futures[f])

    print(f"  Found {len(reachable)} live hosts. Enriching with MAC + ports ...")

    # 2. 收集每个在线 IP 的信息
    devices = []
    for ip in reachable:
        mac = get_mac_from_arp(ip)
        hostname = get_hostname(ip)
        open_ports = scan_common_ports(ip)
        devices.append({
            "ip": ip,
            "mac": mac,
            "hostname": hostname,
            "open_ports": open_ports,
        })

    # 3. 排序并输出
    devices.sort(key=lambda d: list(map(int, d["ip"].split("."))))
    return devices

def format_output(devices: list[dict]):
    print(f"\n{'='*62}")
    print(f"  LAN DISCOVERY REPORT — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*62}\n")
    print(f"  {'IP':<16} {'MAC':<18} {'Hostname':<30} Ports")
    print(f"  {'-'*16} {'-'*18} {'-'*30} {'-'*20}")
    for dev in devices:
        ports = ", ".join(f"{p['port']}/{p['service']}" for p in dev["open_ports"]) or "—"
        print(f"  {dev['ip']:<16} {dev['mac']:<18} {dev['hostname']:<30} {ports}")
    print(f"\n{'='*62}")
    print(f"  Total devices found: {len(devices)}")
    print(f"{'='*62}")

if __name__ == "__main__":
    devices = discover()
    format_output(devices)
```

**运行：**
```bash
python3 lan_discovery.py
```

**输出示例：**
```
============================================================
  LAN DISCOVERY REPORT — 2026-08-10 14:32:05
============================================================

  IP               MAC                Hostname                    Ports
  ---------------- ------------------ ---------------------------- --------------------
  192.168.8.1     AA:BB:CC:DD:EE:FF  router.local                80/HTTP, 443/HTTP-ALT
  192.168.8.100   FF:EE:DD:CC:BB:AA  macmini.local               22/SSH, 5000/HTTP-ALT
  192.168.8.102   11:22:33:44:55:66  iphone.local                62078/HTTP-ALT

============================================================
  Total devices found: 3
============================================================
```

---

## 8. 坑点与注意事项

| 坑点 | 说明 | 解决方案 |
|------|------|---------|
| **需要 sudo 完整 ARP** | `arp -a` 显示所有缓存，但 `arp -s` 添加静态条目需要 sudo | 用 `sudo arp -s ...` |
| **en0/en1 双网卡** | Mac 有时同时有 en0 (Wi-Fi) 和 en1 (以太网) | 先 `ifconfig` 确认活跃网卡，只对活跃网卡扫描 |
| **ping 触发防火墙** | 部分路由器/AP 有速率限制，254 并发 ping 可能被拦截 | 降低并发数（32）或加延迟 |
| **ping -W 平台差异** | macOS `-W` 是秒，Linux `-W` 是 deadline | macOS 用 `-W1`（1秒），不要套用 Linux 语法 |
| **ARP 缓存有时效** | 设备下线后 MAC 仍留缓存一段时间 | 结合 ping 结果交叉验证 |
| **mDNS 跨子网** | dns-sd 只在同一广播域，路由隔离的子网无法发现 | 使用 Bonjour over multicast across router，或直接 ping/socket 扫描 |
| **静默丢包** | 部分设备不响应 ICMP ping 但端口开放 | 用 socket 端口扫描作为 ping 的补充 |
| **Python 脚本编码** | 输出中文字符确保终端编码为 UTF-8 | `export LC_ALL=en_US.UTF-8` 或 `PYTHONIOENCODING=utf-8` |
| **nmap 未安装** | 本 skill 不依赖 nmap，端口扫描用 Python socket 实现 | 如需 nmap 可 `brew install nmap`，但本 skill 覆盖范围无需安装 |

---

## 9. 验证步骤

验证本 skill 是否正常工作。假设网关 = `192.168.8.1`，本机 = `192.168.8.100`。

### Step 1：确认本机 IP 和网关已知

```bash
# 验证能获取本机 IP（应在输出中找到）
ipconfig getifaddr en0
# 期望: 192.168.8.100（或类似）

# 验证能获取网关
route -n get default | grep gateway
# 期望: 192.168.8.1
```

### Step 2：ARP 发现验证

```bash
# 1. 确认 ARP 缓存非空（至少包含网关和本机）
arp -a | grep -E "192\.168\.8\.1|192\.168\.8\.100"
# 期望: 两条记录，显示 MAC 地址

# 2. 如果缓存为空，先 ping 触发
ping -c1 -W1 192.168.8.1
ping -c1 -W1 192.168.8.100
arp -a | grep "192.168.8"
# 期望: 现在有记录
```

### Step 3：Ping 扫描验证

```bash
# 扫描小范围（1–10），验证有响应
for i in 1 2 3 10; do
  ping -c1 -W1 192.168.8.${i} && echo "192.168.8.${i} UP"
done
# 期望: 至少 192.168.8.1 (网关) UP，其他看实际情况
```

### Step 4：Python 端口扫描验证

```bash
python3 - <<'EOF'
import socket
ip = "192.168.8.1"  # 网关
try:
    s = socket.socket(); s.settimeout(2)
    r = s.connect_ex((ip, 80))
    s.close()
    print(f"Gateway port 80: {'OPEN' if r == 0 else 'CLOSED'}")
except Exception as e:
    print(f"Error: {e}")
EOF
# 期望: Gateway port 80: OPEN（大多数路由器都有 Web 管理界面）
```

### Step 5：dns-sd 验证

```bash
# 检查是否有 mDNS 服务在广播
dns-sd -B _http._tcp local. 2>&1 &
sleep 2
kill %1 2>/dev/null
# 期望: 如有 AirPlay/打印机/Hue 灯等设备，显示服务实例
```

### Step 6：汇总脚本验证

```bash
# 完整流程测试（只扫前10个IP加快验证）
python3 - <<'EOF'
import socket, subprocess, re, concurrent.futures
SUBNET = "192.168.8"
ips = [f"{SUBNET}.{i}" for i in range(1, 11)]

def ping(ip):
    return subprocess.run(["ping","-c1","-W1",ip], capture_output=True).returncode == 0

alive = [ip for ip in ips if ping(ip)]
print(f"Alive (1-10): {alive}")
print(f"Expected: 192.168.8.1 (gateway) at minimum")
EOF
# 期望: ['192.168.8.1', ...]
```

### 验证通过标准

- ✅ `arp -a` 包含网关 IP 和本机 IP
- ✅ ping 扫描能发现网关 `192.168.8.1`
- ✅ Python socket 能检测网关端口 80 开放
- ✅ `dns-sd -B _http._tcp local.` 无报错（即使无结果也不算失败）
- ✅ 汇总脚本输出包含 IP + MAC + hostname + ports 四列

---

## 快速命令索引

| 场景 | 命令 |
|------|------|
| 快速 ARP 缓存查看 | `arp -a` |
| 快速 ping 扫描全网段 | `for i in $(seq 1 254); do ping -c1 -W1 192.168.8.$i & done; wait` |
| Python 端口扫描 | `python3 lan_scan.py` |
| 完整汇总发现 | `python3 lan_discovery.py` |
| Bonjour/mDNS 发现 | `dns-sd -B _services._dns-sd._udp local.` |
| 添加静态 ARP | `sudo arp -s 192.168.8.xx AA:BB:CC:DD:EE:FF` |
| 查本机 IP | `ipconfig getifaddr en0` |
| 查网关 | `route -n get default \| grep gateway` |
