---
name: network-discovery
description: "局域网设备发现 — arp/ping扫描/python socket/mDNS/Bonjour"
triggers:
  - network discovery
  - lan scan
  - 局域网发现
  - 设备扫描
  - nmap
  - ping sweep
  - mDNS
  - Bonjour
version: "1.0.0"
author: Hermes Agent
created: "2026-08-10"
tags:
  - network
  - discovery
  - lan
  - bonjour
  - mdns
---

# Network Discovery — 局域网设备发现

Mac mini M4 (macOS 26.5) 局域网设备发现工具合集，无需 nmap 即可完成常见发现任务。

## 工具清单

| 工具 | 安装 | 特点 |
|------|------|------|
| `arp -a` | 内置 | 快速，已知设备 |
| `ping` | 内置 | 基础扫描 |
| `dns-sd` | 内置(macOS) | mDNS/Bonjour发现 |
| Python socket | 内置 | 端口扫描 |
| `adb devices` | 需安装 | USB/网络设备 |

---

## 方法一：arp -a（最快，已知设备）

```bash
arp -a
```

输出示例：
```
? (192.168.8.1) at 94:83:c4:6d:55:84 on en0 [ethernet]
? (192.168.8.204) at d0:11:e5:b5:ec:37 on en0 [ethernet]
aimacdemac-mini.lan (192.168.8.112) at d0:11:e5:b5:ec:37 on en0 [ethernet]
```

---

## 方法二：ping sweep（完整网段）

```bash
# 扫描192.168.8.0/24网段
for i in $(seq 1 254); do
  ping -c1 -W1 192.168.8.$i 2>/dev/null &
done
wait
arp -a | grep ": at"
```

更快的方式（多进程并行）：
```bash
# 使用fping（需brew install fping）
brew install fping
fping -g 192.168.8.0/24 2>/dev/null
```

---

## 方法三：python socket 端口扫描

端口扫描脚本 `~/.hermes/scripts/lan_scan.py`：

```python
#!/usr/bin/env python3
"""局域网设备端口扫描"""
import socket
import concurrent.futures
import subprocess

COMMON_PORTS = [22, 80, 443, 445, 8080, 5000, 5555, 5556]
TIMEOUT = 1

def scan_host(ip):
    """扫描单个主机的常用端口"""
    open_ports = []
    for port in COMMON_PORTS:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(TIMEOUT)
            result = sock.connect_ex((ip, port))
            if result == 0:
                service = {22: 'ssh', 80: 'http', 443: 'https', 445: 'smb',
                          8080: 'http-proxy', 5000: 'adb', 5555: 'adb', 5556: 'adb'}
                open_ports.append(f"{port}({service.get(port, '?')})")
            sock.close()
        except:
            pass
    return ip, open_ports

def get_hostname(ip):
    """反向DNS查询hostname"""
    try:
        hostname = socket.gethostbyaddr(ip)[0]
        return hostname
    except:
        return ip

def scan_network(network="192.168.8"):
    """扫描整个网段"""
    print(f"🔍 扫描 {network}.0/24 ...")
    
    # 先ping扫描
    for i in range(1, 255):
        subprocess.Popen(
            ["ping", "-c", "1", "-W", "1", f"{network}.{i}"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    
    import time; time.sleep(2)
    
    # 并行端口扫描
    hosts = []
    for i in range(1, 255):
        hosts.append(f"{network}.{i}")
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(scan_host, ip): ip for ip in hosts}
        for future in concurrent.futures.as_completed(futures):
            ip, open_ports = future.result()
            if open_ports:
                hostname = get_hostname(ip)
                results.append((ip, hostname, open_ports))
    
    return results

if __name__ == "__main__":
    results = scan_network()
    print(f"\n📋 发现 {len(results)} 台活跃设备：\n")
    print(f"{'IP':<18} {'Hostname':<30} {'开放端口'}")
    print("-" * 60)
    for ip, hostname, ports in sorted(results, key=lambda x: [int(p) for p in x[0].split('.')[3:]]):
        print(f"{ip:<18} {hostname:<30} {', '.join(ports)}")
```

运行：
```bash
python3 ~/.hermes/scripts/lan_scan.py
```

---

## 方法四：dns-sd（mDNS/Bonjour 发现）

macOS 自带的Bonjour/mDNS服务发现：
```bash
# 浏览所有mDNS服务
dns-sd -B _http._tcp local. 2>/dev/null | head -20

# 浏览SSH服务
dns-sd -B _ssh._tcp local. 2>/dev/null

# 浏览AFP/SMB文件共享
dns-sd -B _afpovertcp._tcp local.
dns-sd -B _smb._tcp local.

# 主动查询特定类型
dns-sd -L "Mac mini" _device-info._tcp local.
```

---

## 方法五：adb devices（Android设备）

```bash
# USB连接的Android设备
adb devices

# 无线调试设备（需先配对）
adb connect 192.168.8.204:5555  # 小米MI 8
adb connect 192.168.8.248:5555  # 小米平板MRX-W29
adb devices
```

---

## 方法六：arp 静态条目

已知设备可手动添加：
```bash
# 添加静态ARP（需sudo）
sudo arp -s 192.168.8.204 00:11:22:33:44:55

# 删除条目
sudo arp -d 192.168.8.204
```

---

## 输出格式化

将发现结果格式化输出：

```bash
# 综合扫描（ping + 端口 + DNS）
for ip in $(seq 1 254); do
  addr="192.168.8.$ip"
  if ping -c1 -W1 $addr &>/dev/null; then
    hostname=$(host $addr 2>/dev/null | awk '{print $NF}' | tr -d '.')
    ports=$(python3 -c "
import socket; ports=[22,80,445,8080,5000,5555]
for p in ports:
    s=socket.socket(); s.settimeout(0.3)
    if s.connect_ex(('$addr',p))==0: print(p,end=' ')
    s.close()
")
    echo "$addr  $hostname  $ports"
  fi
done
```

---

## 已知设备参考

| 设备 | IP | MAC | 端口 |
|------|-----|-----|------|
| GL-Inet路由器 | 192.168.8.1 | 94:83:c4:6d:55:84 | - |
| Mac mini M4 | 192.168.8.112 | d0:11:e5:b5:ec:37 | ssh |
| 小米MI 8 | 192.168.8.204 | ? | 5555(adbd) |
| 小米平板MRX-W29 | 192.168.8.248 | ? | 5555(adbd) |
| Intel Mac Pro | 192.168.8.123 | ? | ssh |

---

## 坑点

1. **ping触发防火墙**：部分设备禁ping，ping不通≠不在线
2. **双网卡**：Mac mini同时有en0(以太网)和en1，需指定网卡 `ping -I en0 192.168.8.1`
3. **ARP缓存过期**：已知设备一段时间无活动后从arp表消失，需重新ping唤醒
4. **sudo完整arp**：普通用户看不到所有ARP条目（含静态），`sudo arp -a`更完整
5. **网段不同**：部分路由器用192.168.1.x或10.0.0.x，先确认当前网段 `ipconfig getifaddr en0`

---

## 验证

```bash
# 验证能发现本机和路由器
arp -a | grep -E "192.168.8.1|192.168.8.112" && echo "✅ 发现成功"

# 验证python端口扫描
python3 -c "
import socket
s = socket.socket()
s.settimeout(1)
r = s.connect_ex(('192.168.8.1', 80))
print('✅ 路由器80端口开放' if r == 0 else '❌ 连接失败')
s.close()
"
```
