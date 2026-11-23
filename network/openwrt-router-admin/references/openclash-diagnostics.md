# OpenClash data-plane diagnostics

Use when a router runs OpenClash and traffic through it stops or blackholes while
the proxy process is still alive. The failure is often one policy group pinned to
a dead node, not a broken process or missing firewall rule.

## Locate the fault

1. Confirm the data plane exists. On firewall4/nftables routers `iptables -t nat -S`
   is empty even when everything works. Check instead:
   ```sh
   nft list ruleset | grep -i -A2 clash
   ip rule
   ip route show table 354          # or the fwmark lookup table in use
   netstat -lntp | grep -E '7890|7895|9090'
   ```
2. Read the controller secret from `/etc/config/openclash` (UCI option), never echo
   it into reports. All calls below need `-H "Authorization: Bearer <secret>"`.
3. Enumerate **every** Selector group and its current node, not just the primary
   one. A catch-all/fallback group that matches the default rule can pin most
   traffic to a dead node while the main selector looks healthy:
   ```sh
   curl -s -H "Authorization: Bearer $SEC" http://127.0.0.1:9090/proxies \
     | jq -r '.proxies | to_entries[] | select(.value.type=="Selector") | [.key, .value.now] | @tsv'
   ```
4. Get the reason from the controller log (`/tmp/openclash.log`): repeated
   `<ip>:<port> i/o timeout` names the dead node. Compare with the group map from
   step 3.
5. Check delay before switching: `curl -s -H "Authorization: Bearer $SEC"
   "http://127.0.0.1:9090/proxies/<node>/delay?url=http://www.gstatic.com/generate_204&timeout=5000"`.

## Repair

Switch the affected group (URL-encode the group name, including emoji/CJK):

```sh
GROUP=$(python3 -c 'import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1],safe=""))' '组名')
curl -s -X PUT -H "Authorization: Bearer $SEC" \
  "http://127.0.0.1:9090/proxies/$GROUP" -d '{"name":"健康节点名"}'
```

Then re-read `.proxies[group].now` to confirm, and verify exit IP from a LAN
client twice with a few seconds between — Cloudflare-style exits rotate IPs, so a
single changed IP is not a stability check.

## Safe disconnect tests

Never stop the proxy in-band to test a direct route. If `router_self_proxy '1'`
is set, the router's own egress dies with the proxy and the SSH session may not
come back. Write one script on the router that stops the proxy, runs the short
test, restarts it, and logs to a local file; run it in the foreground with an
outer `timeout`. After the test, re-check the nft rules and **all** selector
`now` values — a restart alone does not clear a dead-node pin.

Push the script with `ssh <host> 'cat > /tmp/test.sh' <<'EOF' ... EOF` (scp is
available only when the router ships sftp-server).

## Making a group selection permanent

A PUT to `/proxies/<group>` changes the running selection only. Persistence comes
from the yaml's `store-selected: true`, which writes the selection to the core's
cache on a **clean stop**; OpenClash's `openclash_history_get.sh` then copies that
cache into `/etc/openclash/history/<config>.db`. There is no separate "save group
state" command: `yml_groups_get.sh`/`yml_groups_set.sh` handle group *structure*
in UCI, not the live `now` value.

To make "always follow the fastest node" permanent, point each traffic-facing
Selector group at a URLTest group (PUT `{"name":"♻️ 自动选择"}` into `节点选择`,
`漏网之鱼`, etc.), then perform one clean stop→start so the choice is flushed to
disk. Verify by reading back every group's `now` **after** the restart; a URLTest
group will re-measure and may land on a different node, which is the expected
sign that automatic selection is working, not that the setting was lost.

When reading yaml with grep, write the pattern to a script file and run it on the
router — `ssh host "grep -E 'a|b' file"` lets the LOCAL shell consume the `|`
and quotes.
