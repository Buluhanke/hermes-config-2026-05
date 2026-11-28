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
  Proton, VPN Gate, and fixed-IP VPS; which exits are safe for logged-in services.
- `references/openclash-diagnostics.md` — controller-API recipe for locating a
  selector group stuck on a dead node and switching it back.

## OpenClash tuning that actually works (verified 2026-11-23)

- **Speed**: the clash API (`curl -H "Authorization: Bearer <secret>" http://127.0.0.1:9090/proxies`, secret from yaml) shows per-node delay. A policy group stuck on a dead/slow node is the usual culprit — PUT it to the fastest alive node via `curl -X PUT .../proxies/<urlencoded-group> -d '{"name":"<node>"}'`. Verify with curl timing before/after.
  - **历史 delay 字段不可信**：很多节点缓存值是 `0`（其实是从没测试成功）或基于 Google `generate_204`（国内必超时，全节点 Timeout）。必须用 `/proxies/<node>/delay?url=<国内可达URL>&timeout=5000` 实测，或更直接：切节点后用真实下载 `curl -o /dev/null -w '%{speed_download}' https://speed.cloudflare.com/__down?bytes=6000000` 比吞吐。实测同一主组换节点 131KB/s → 1065KB/s（8×）。
  - **修测速地址的正确姿势（持久）**：不要手改 yaml（订阅更新会覆盖）。用官方 UCI：`uci set openclash.config.urltest_address_mod='http://connect.rom.miui.com/generate_204'; uci commit openclash`。`yml_rules_change.sh` 在每次配置加载时把该值覆盖到所有 url-test/fallback/load-balance 组的 url 字段。小米 generate_204 实测 0.78s、标准 204、国内可达，优于 Google gstatic（2.1s）+ 被墙风险。可同时 sed 当前 yaml 立即生效，再 `curl -X PUT /configs -d '{"path":"..."}'` 热重载（HTTP 204，**不重启进程、不断 SSH**）。注意 yaml 里 `DOMAIN-SUFFIX,gstatic.com,🚀 节点选择` 是分流规则不是测速地址，别误删。
  - **主组切自动选路**：把 Selector（如 🚀 节点选择）PUT 成 `{"name":"♻️ 自动选择"}`。批量对 20 个节点跑 `/delay?url=<小米204>` 推动 URLTest 重测（interval 300s 太久）。验证必须看真实下载吞吐 + 出口 IP，不能只看 delay——延迟最低的节点吞吐未必最高，实测自动选路后 1.3–3.9MB/s、出口 CN（比手动挑的德国出口更快）。
  - **持久改测速 URL 用 UCI 不用手改 YAML**：OpenClash 官方选项 `urltest_address_mod` 设为非0 URL 后，每次配置加载自动把 YAML 里所有 health-check/测速 URL（默认 Google `gstatic`，国内必超时）替换成该地址，订阅更新也不覆盖；`uci set openclash.config.urltest_address_mod='http://connect.rom.miui.com/generate_204'; uci commit openclash`（小米 generate_204 实测 0.78s，优于 gstatic 2.1s）。定义见 `/usr/share/openclash/yml_rules_change.sh` 约 369–383 行。2026-11-27 GL-BE6500 实测。
  - **先排除底层再怪节点**：国内 CDN（阿里/163 镜像）也只有 20–60KB/s 时，先查路由器 CPU（`top -bn1` 看 %idle）、`/proc/net/dev` 丢包增量、上游网关 ping。若 CPU idle>90%、丢包几乎不涨、网关 <1ms，则路由器/上游健康，瓶颈就在代理节点本身。 NOTE: shell `;` inside `ssh router "cmd1; cmd2"` is eaten by the LOCAL shell — write a script via `ssh router "cat > /tmp/x" <<'EOF'` then `ssh router "sh /tmp/x"`.
- **Control API hardening**: `external-controller: 0.0.0.0:9090` + `allow-lan: true` exposes the dashboard to the whole LAN. Bind it to localhost via `/etc/openclash/custom/openclash_custom_overwrite.sh` (official overwrite hook, survives subscription updates): `sed -i 's/^external-controller:.*/external-controller: 127.0.0.1:9090/' "$CONFIG_FILE"`. Safe — watchdog and nginx reverse proxy both use `127.0.0.1:$cn_port` already. Verify LAN curl to :9090 is refused, local curl works.
- **Auto-update subscriptions**: `uci set openclash.config.auto_update=1; uci set openclash.config.auto_update_time=4; uci commit openclash` (must run inside a router-side script, see `;` note above). Dead nodes get rotated out automatically.
- **Never restart OpenClash inline from the agent** — wrap stop/restart+status check in a router-local script with `timeout 60` so recovery doesn't depend on your link; `sh: out of range` from init.d is benign here, `status: running` is what matters.

## Pitfalls

- **Never disable a working OpenClash just to "test" another VPN** — on this GL-BE6500, `router_self_proxy '1'` means ALL router + LAN outbound (including the agent's own link) goes through OpenClash TUN (`utun` 198.18.0.1). Stopping it strands every client. If a test must toggle it, run stop→test→start as ONE self-contained script on the router so recovery does not depend on your now-dead link.
- **Don't misdiagnose a downed exit as "proxy broken"** — after any proxy restart, check groups via clash API (`curl -H "Authorization: Bearer <secret>" http://127.0.0.1:9090/proxies`, secret from yaml). A group stuck on a dead node (e.g. `🐟 漏网之鱼: CF官方优选9` → `91.193.58.183:8443` i/o timeout, matches `Match/` = catches most traffic) blackholes the whole LAN even when `节点选择` looks healthy. Fix: PUT the group to a proven-alive node; exit IP recovers immediately. Verify 3× with gaps.
- **fw4/nftables, not iptables** — this router uses nftables; `iptables -t nat -S` shows zero OpenClash rules even when active. Use `nft list ruleset | grep -i openclash`. `sh: out of range` from `/etc/init.d/openclash` is a benign script quirk here, not the outage cause.
- **scp to router fails** (`ash: /usr/libexec/sftp-server: not found`) — use `ssh router "cat > /path" < localfile`.
- **A public .ovpn that imports is not a working tunnel** — verify TLS handshake, not just TCP connect, before touching permanent config. With `router_self_proxy '1'` the two paths differ: proxy ON routes OpenVPN through the proxy (handshake commonly reset); proxy OFF may leave the router with no direct outbound at all. Test both paths read-only from a router-local script, and confirm the `.ovpn`'s actual auth directives instead of assuming provider docs (`auth-user-pass` is not universal). Reusable decision rule lives in `references/vpn-options.md`; shared/free exits are unsuitable for logged-in services regardless of connectivity.
- **Skipping the backup because the change "looks small"** — network config
  mistakes take down every device behind the router at once.
- **Calling a tunnel working because a TCP connect succeeded or a `.ovpn`
  imported** — verify the TLS handshake and the exit IP from the router and a LAN
  client before touching the permanent config.
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
