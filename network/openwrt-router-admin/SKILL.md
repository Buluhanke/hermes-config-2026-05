---
name: openwrt-router-admin
description: "路由 SSH 管理：探测→备份→变更→LAN实测。Use when 在OpenWrt/GL.iNet配VPN"
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux, windows]
metadata:
  hermes:
    tags: [OpenWrt, GL.iNet, Router, SSH, WireGuard, OpenClash, VPN]
    related_skills: [network-discovery, hermes-browser-local-login]
---

# OpenWrt / GL.iNet Router Admin

Remote-administer an OpenWrt-family router (GL.iNet included) over SSH. The router
is usually the LAN default gateway and may itself be a secondary router behind a
different gateway. Treat every network mutation as capable of cutting the link you
are connected through.

## When to Use

Use when the task requires logging into a router to configure or inspect it:
setting up VPN/WireGuard/OpenClash, changing firewall or routing, diagnosing why
LAN clients are or are not going through a proxy, or verifying an exit IP/DNS
leak. Skip for pure LAN device discovery with no login — use `network-discovery`.

## Always-on rules

- **Probe read-only before touching anything.** Know the topology and what is
  already running before you change it.
- **Back up first.** No local, listing-verified backup of `/etc/config` (plus the
  relevant plugin directory) means no mutation.
- **A running proxy process is not proof of proxied traffic.** Verify from a LAN
  client, not from the router — the router's own traffic commonly bypasses its
  proxy.
- **Keep a rollback path for the default gateway** you are connected through.
  Never change routing in a way that strands the SSH session without a backup.
- **Passwords from the user stay out of committed files and echoed output.** Use
  `allow_agent=False, look_for_keys=False` with paramiko for a supplied password;
  read it from an env var rather than hardcoding it in a reusable script.

## Procedure

1. **Connect.** `scripts/gl_probe.py` takes `ROUTER_HOST` / `ROUTER_USER` /
   `ROUTER_PASS` from the environment and runs a command read-only:
   ```bash
   ROUTER_HOST=192.168.8.1 ROUTER_USER=root ROUTER_PASS='...' \
     python3 ~/.hermes/skills/network/openwrt-router-admin/scripts/gl_probe.py
   ```
   If the first password is rejected, verify the literal bytes
   (`printf %s "$PASS" | xxd`) before assuming an encoding problem — a wrong
   character is far more common than a CJK/UTF-8 transport failure.

2. **Read-only probe:** `uname -a`, `/etc/openwrt_release`, `ip -br addr`,
   `ip route`, `pgrep -af 'clash|mihomo'`, `lsmod | grep -i wireguard`,
   `which wg`, and which controller ports answer. Record what is already there.

3. **Identify the topology.** Compare the LAN bridge address with the WAN/upper
   address and the default route. If the router's own default route points at a
   different gateway, it is a secondary/旁路由 — client traffic may or may not be
   routed through it. Check the client's real exit with `curl https://ipinfo.io/json`
   from the client machine, not the router.

4. **Back up to local scratch and verify the archive listing:**
   ```bash
   ROUTER_HOST=... ROUTER_PASS='...' python3 scripts/gl_probe.py \
     'tar -czf /tmp/cfg.tgz /etc/config /etc/openclash 2>/dev/null; base64 /tmp/cfg.tgz' \
     | base64 -D > ~/backup.tgz
   tar -tzf ~/backup.tgz | head
   ```

5. **Mutate** with the smallest change that achieves the goal. For WireGuard,
   `lsmod | grep wireguard` plus `/usr/bin/wg` plus `/lib/netifd/proto/wireguard.sh`
   means native client support is present; importing a generated `.conf` through
   the router's own client is cleaner than forcing a proxy-core implementation
   with known protocol issues.

6. **Verify from a LAN client:** exit IP, DNS leak check, and persistence over a
   few minutes — intermittent failure is the common mode for tunnels in this
   region. Report the measured result, not the intended one.

7. **Roll back** from the local backup if verification fails, and say explicitly
   that the change was reverted.

## References

- `references/vpn-options.md` — decision table for WireGuard/WARP, edgetunnel,
  Proton, and fixed-IP VPS; which exits are safe for logged-in services.

## Pitfalls

- **Skipping the backup because the change "looks small"** — network config
  mistakes take down every device behind the router at once.
- **Concluding proxy success from `pgrep` or an `Unauthorized` controller** — a
  proxy process running and a controller answering both lack evidence about LAN
  client traffic; measure the client's exit IP.
- **Treating the router's own `curl ipinfo.io` as the client result** — on a
  secondary-router setup the router's traffic often takes a different path.
- **Configuring a VPN before checking whether its exit is a datacenter IP** —
  shared/datacenter exits trigger verification or bans on logged-in AI services;
  choose the exit based on the target service before provisioning.
- **Presenting an unfinished attempt as a working recipe** — if setup stops at a
  missing user-supplied credential, record only the steps that ran and say where
  it stopped.
