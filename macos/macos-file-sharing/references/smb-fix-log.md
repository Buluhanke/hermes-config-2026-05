# SMB File Sharing Fix — Session Reference
# 2026-07-27 | macOS 26.5.1 (Mac mini M4)

## Root Cause
`com.apple.smbd.plist` had `<Disabled>true</Disabled>` set at boot time.
smbd never auto-started. Port 445 was held by launchd socket activation.
New smbd processes failed with "failed to bind to port 445".

## Actual Error Log (reproduced)
```
2026-07-27 13:04:53.375711+0800  smbd  Error  unable to impersonate the anonymous account
2026-07-27 13:04:58.195655+0800  smbd  Error  smbd_detect_sg_mode: NOT enabling super guest mode, errno: 2
2026-07-27 13:04:58.206126+0800  smbd  Error  main: normal_mode, registering ports
2026-07-27 13:04:58.206057+0800  smbd  Error  failed to bind to port 445
```

## Working Fix Sequence
```bash
# 1. Kill any zombie smbd
sudo killall smbd
sleep 1

# 2. Bootout cleans launchd's in-memory state completely
sudo launchctl bootout system/com.apple.smbd
sleep 2

# 3. Bootstrap re-registers the service
sudo launchctl bootstrap system /System/Library/LaunchDaemons/com.apple.smbd.plist
sleep 2

# 4. Explicitly start
sudo launchctl start com.apple.smbd
sleep 3

# 5. Verify — smbd should appear in lsof
ps aux | grep -i smb | grep -v grep
lsof -i :445  # should show smbd with LISTEN
```

## Bonjour Verification Command
```bash
dns-sd -B _smb._tcp local. 2>&1 &
sleep 3
jobs -l
kill %1 2>/dev/null
```
Expected output:
```
Add  3  1  local.  _smb._tcp.  Aimac的Mac mini
Add  2 15  local.  _smb._tcp.  Aimac的Mac mini
```

## Why launchctl kickstart was used instead of killall/restart
- `sudo launchctl stop com.apple.smbd` + `start` failed with I/O error (plist in /System/Library)
- `launchctl bootout` cleanly removes from launchd domain without touching the plist file
- `killstart -kp` works when bootout is not available for a service

## Port 445 Launchd Ownership (Normal)
```
COMMAND   PID USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME
launchd     1 root   49u  IPv6 0x...      0t0  TCP *:microsoft-ds (LISTEN)
smbd   55845 root    3u  IPv6 0x...      0t0  TCP *:445 (LISTEN)
```
This is NORMAL on macOS — launchd pre-binds port 445 (socket activation),
then hands it off to smbd. Both entries existing simultaneously is correct.
