# Cross-border network option decision table

Use when choosing what to deploy on a home router for cross-border access.
Facts here are about the *shape* of each option, not transient availability.

## Decision rules

- For logged-in services (AI accounts, anything with a session), the exit must be
  a **stable, dedicated IP**. Shared datacenter exits trigger verification or
  bans regardless of how well the tunnel connects.
- For general browsing and video, a shared/free exit can be a backup — set the
  expectation that it is intermittent and unsuitable for accounts.
- Prefer the router's native WireGuard client over a proxy core's WireGuard
  implementation when both exist; proxy cores have had protocol-specific defects.

## Options

| Option | What it actually is | Exit | Fit |
|--------|--------------------|------|-----|
| WireGuard on a fixed-IP VPS | End-to-end encrypted L3 tunnel to your own server | Your own stable IP | Primary; the only dependable choice for logged-in services |
| Cloudflare WARP | A privacy/encryption layer in the 1.1.1.1 app, not an anti-censorship tool | Shared Cloudflare IP near your real location; no country selection | Not a reliable primary; availability is intermittent; AI sites can see `warp=on` at `/cdn-cgi/trace` |
| edgetunnel | VLESS/Trojan/SS proxy implemented as a Cloudflare Worker/Page | Shared Cloudflare edge IP | Backup / video only; free-tier CPU limit causes Error 1101 under load; using it as a proxy sits outside Cloudflare's ToS |
| Proton VPN Free | Provider VPN; WireGuard config generated from the account web UI | Datacenter IP from a rotating free-country pool | General-purpose backup; not for logged-in AI; router counts as one device with unlimited devices behind it |

## Provisioning notes

- A Proton WireGuard `.conf` is account-bound: it must be generated at the
  provider's account site with the platform set to router. There is no reliable
  account-free path — third-party guest-session generators depend on proxy
  endpoints that go dead. Ask for the generated file rather than burning time on
  those generators.
- MASQUE (HTTP/3 over UDP 443) replaced WireGuard as WARP's preferred transport;
  reasoning based only on "WireGuard is blocked" is out of date.
- A tunnel that connects is not the same as a tunnel that works: verify the exit
  and DNS from a LAN client, and re-check after several minutes.
