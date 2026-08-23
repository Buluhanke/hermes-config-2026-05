# Remote Hermes Configuration Inspection

## Overview
Procedures for inspecting Hermes Agent configuration and skills on a remote machine when direct SSH access is challenging.

## Common Connection Issues & Fixes

### SSH Authentication Loops
When SSH connects but immediately closes after publickey/authentication:
```bash
# Typical symptom: Connection established then immediately closed
# debug1: Authentication succeeded (publickey).
# Connection to 192.168.8.236 closed.

# Workarounds:
1. Force password authentication (if password known):
   ssh -o PreferredAuthentications=password -o PubkeyAuthentication=no user@host

2. Use keyboard-interactive explicitly:
   ssh -o PreferredAuthentications=keyboard-interactive -o PubkeyAuthentication=no user@host

3. Check if account is disabled or shell is restricted:
   ssh -v user@host 2>&1 | grep -E "(Authenticated|shell|command)"

4. If using sshpass with keyboard-interactive:
   sshpass -p'your_password' ssh -o PreferredAuthentications=keyboard-interactive -o PubkeyAuthentication=no user@host 'command'
```

### VNC/RFB Access (Port 5900)
When SSH fails but VNC port is open:
1. Use Finder → Go → Connect to Server → `vnc://192.168.8.236:5900`
2. Or from terminal: `open vnc://username:password@192.168.8.236:5900`
3. Common credentials: often same as system login

## Remote Inspection Commands (when access obtained)

### Basic Health Check
```bash
hermes --version
hermes doctor
hermes status --all
```

### Configuration Review
```bash
hermes config
hermes config path          # Shows config location
hermes config env-path      # Shows .env location
hermes model                # Interactive model selector
```

### Skills & Tools Audit
```bash
hermes skills list          # All installed skills
hermes skills check         # Check for updates
hermes tools list           # Toolset status
hermes gateway status       # Gateway/platform connections
```

### Memory & Database Status
```bash
hermes memory status
ls -la ~/.hermes/*.db       # Check database sizes
wc -l ~/.hermes/memories/MEMORY.md  # Memory file length
```

### Cron Jobs & Background Processes
```bash
hermes cron list
ps aux | grep hermes        # Running Hermes processes
ls -la ~/.hermes/cron/      # Cron job definitions
```

### Log Investigation
```bash
ls -la ~/.hermes/logs/
grep -i error ~/.hermes/logs/gateway.log | tail -10
grep -i failed ~/.hermes/logs/gateway.log | tail -10
```

## Alternative Data Collection (when no shell access)

### File Synchronization (if AFP/SMB enabled)
1. Connect via Finder: `smb://192.168.8.236/Users/aimac/.hermes`
2. Or: `afp://192.168.8.236/Users/aimac/.hermes`
3. Download: config.yaml, .env, skills/, memories/MEMORY.md

### Port-Based Checks
```bash
# Check if dashboard is running (usually 3847)
curl -s http://192.168.8.236:3847 || echo "Dashboard not on 3847"

# Check gateway/proxy (usually 20128)
curl -s http://192.168.8.236:20128 || echo "Gateway not on 20128"

# VNC status (5900)
nc -z -w2 192.168.8.236 5900 && echo "VNC accepting connections" || echo "VNC not accessible"
```

## Configuration-Specific Verification

### Provider Validation
```bash
# Check custom providers in config
grep -A3 -B1 "custom_providers" ~/.hermes/config.yaml

# Validate API keys (redacted in output but present in file)
grep -E "api_key|base_url" ~/.hermes/config.yaml | head -10
```

### Memory Backend Check
```bash
grep -A5 -B2 "memory:" ~/.hermes/config.yaml
# Should show provider: holographic or other backend
```

### Toolset Validation
```bash
grep -A20 "platform_toolsets:" ~/.hermes/config.yaml
# Verify expected toolsets for each platform
```

## Troubleshooting Guide

### "Connection closed by port 22" after auth
- **Cause**: Account may have restricted shell (e.g., git-shell, rssh) or immediate logout command in ~/.ssh/rc
- **Fix**: 
  ```bash
  # Try to force a specific command
  ssh user@host 'echo "test"; ls -la ~/.hermes/'
  # Or request a shell explicitly
  ssh -t user@host bash
  ```

### Authentication succeeds but no response
- **Cause**: Session may be getting stuck in background process or tmux
- **Fix**:
  ```bash
  # Add timeout and verbose
  timeout 10 ssh -v user@host
  # Check if remote process is running
  ssh user@host 'ps aux | grep -E "(hermes|sshd)"'
  ```

### VNC shows grey/black screen
- **Cause**: Remote user not logged in or desktop session locked
- **Fix**: 
  - Ask remote user to log in and unlock screen
  - Or use SSH to start a desktop session: `ssh user@host '/System/Library/CoreServices/Finder.app/Contents/MacOS/Finder &'`

## Safety Notes
1. Never attempt to bypass authentication - if credentials don't work, stop and ask for proper access
2. When viewing .env or config files, avoid screenshotting or sharing sensitive data
3. Prefer read-only inspection commands unless explicit modification is requested
4. Always verify you're operating on the intended machine (check hostname, IP, username)

## Related Skills
- `hermes-agent`: Main configuration and setup procedures
- `hermes-config-tricks`: Local configuration modification techniques
- `hermes-backup-restore`: Safe backup and restore procedures