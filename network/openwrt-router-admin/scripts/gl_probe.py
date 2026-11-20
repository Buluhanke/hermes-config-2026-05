#!/usr/bin/env python3
"""Read-only OpenWrt/GL.iNet SSH probe. Credentials from env, never inline.

Env: ROUTER_HOST (required), ROUTER_USER (default root), ROUTER_PASS (required).
Optional argv[1]: command to run; defaults to a broad read-only inventory.
"""
import os
import sys

import paramiko

DEFAULT = (
    "echo LOGIN_OK; uname -a; "
    "echo ---release---; cat /etc/openwrt_release 2>/dev/null | head -6; "
    "echo ---addr---; ip -br addr; echo ---route---; ip route; "
    "echo ---proxy---; pgrep -af 'clash|mihomo' || true; "
    "echo ---wg---; lsmod 2>/dev/null | grep -i wireguard || true; "
    "which wg || true; ls /lib/netifd/proto/wireguard.sh 2>/dev/null || true"
)


def main() -> int:
    host = os.environ["ROUTER_HOST"]
    user = os.environ.get("ROUTER_USER", "root")
    pwd = os.environ["ROUTER_PASS"]
    cmd = sys.argv[1] if len(sys.argv) > 1 else DEFAULT

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        host, username=user, password=pwd, timeout=12,
        allow_agent=False, look_for_keys=False,
    )
    _, out, err = client.exec_command(cmd, timeout=60)
    sys.stdout.write(out.read().decode("utf-8", "replace"))
    error = err.read().decode("utf-8", "replace")
    if error.strip():
        sys.stderr.write("STDERR: " + error)
    client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
