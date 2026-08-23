# LAN Device Discovery on macOS

## Quick scan workflow

```bash
# 1. Ping sweep to populate ARP cache
for i in $(seq 1 254); do
  (ping -c 1 -W 1 192.168.8.$i >/dev/null 2>&1 &)
done
wait
sleep 2

# 2. Read ARP table (dedupe by MAC — same device appears on en0 + en1)
arp -a | grep -v "^?" | grep -v "mdns\|224\.\|239\."

# 3. OUI lookup to identify vendor (first 3 octets)
# Apple OUI prefixes: d0:11:e5 (Mac mini), 72:fc:2a, 92:f1:69, 88:63:df, b4:2e:99, 9e:12:ab (iPhone), 94:83:c4 (GL-iNet router)

# 4. Port scan to identify available services
for port in 22 445 548 5000 5900 7000; do
  nc -z -w 2 <IP> $port && echo "$port OPEN" || echo "$port CLOSED"
done
```

## macOS naming confusion

| What you see | Where it comes from |
|---|---|
| `mac.lan` in ARP | Bonjour hostname (the *local hostname* set in Sharing prefs) |
| "Aimac" | ComputerName (set in System Settings → General → About) |
| Same device on en0 + en1 | Dual-band Macs advertise on both interfaces |

**Both names are real.** When a user says "find my Mac Air/Mac mini", check both.

## Router DHCP leases (GL-iNet / OpenWRT)

```bash
# Try these paths on GL-iNet routers
curl -s --connect-timeout 3 "http://192.168.8.1/tmp/dhcp.leases"
curl -s --connect-timeout 3 "http://192.168.8.1/cgi-bin/luci/admin/network/hosts"
```

## Key services on a typical Mac

| Port | Service | Notes |
|---|---|---|
| 22 | SSH | Disabled by default; must enable in System Settings → General → Sharing → Remote Login |
| 5000 | AirPlay Remote Disc | Shows up when "Look for AirPlay devices" is on |
| 7000 | Apple File Service | AFP replacement (macOS 11+) |
| 548 | AFP | Disabled by default in modern macOS |
| 5900 | VNC | Disabled by default; enable in Screen Sharing |

## Common pitfalls

- **ARP cache is sparse** unless devices recently communicated. Ping sweep first.
- **192.168.8.236 is the Mac mini "Aimac"** — confirmed 2026-07-23. MAC prefix `92:f1:69` = Apple.
- **Ping sweep backgrounding**: macOS `nc` uses `-w` not `-W`. `nc -z -w 2 <IP> <port>` works.
