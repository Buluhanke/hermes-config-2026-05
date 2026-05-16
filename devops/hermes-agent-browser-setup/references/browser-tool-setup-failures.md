# Browser Tool Setup Failures & Solutions

## Symptom
Browser automation tools report as "enabled" in `hermes tools list` but fail silently or throw errors when invoked. No Browserbase API key configured, Camofox not installed.

## Two Backend Options

### 1. Browserbase (Recommended — Cloud, Zero Setup)

**Prerequisites:**
- Browserbase account at https://browserbase.com (free tier available)
- API key from the dashboard

**Setup:**
```bash
# Add to ~/.hermes/.env
BROWSERBASE_API_KEY=your_key_here
```

**Verification:**
```bash
hermes tools list  # browser toolset must show enabled
```

Browserbase handles everything in the cloud — no local browser, no dependencies.

---

### 2. Camofox (Local — Harder Setup)

Camofox is a local anti-detection browser server wrapping Camoufox.

**Known Failure Modes:**

#### Failure A: npm install EACCES (permission denied)
```
npm error EACCES: mkdir '/usr/local/lib/node_modules/camofox-browser'
```
**Cause:** npm tried to write to system directory.  
**Fix:**
```bash
mkdir -p ~/.npm-global
npm config set prefix ~/.npm-global
export PATH="$HOME/.npm-global/bin:$PATH"
npm install camofox-browser
```

#### Failure B: npm install timeout (download too large)
```
[Command timed out after 300s]
```
**Cause:** Camofox downloads ~300MB Camoufox browser engine on first run. Network timeout.  
**Fix options (in order of reliability):**
1. **Use Browserbase instead** (simplest path)
2. **Clone on a fast connection machine, then rsync/scp to target**
3. **Run on Mac mini (192.168.0.4) via SSH:** `ssh aimac@192.168.0.4` then clone and install there

#### Failure C: Docker not available
```
docker: command not found
```
**Fix:** Skip Docker route, use npm or manual clone.

#### Failure D: Git clone also times out
**Fix:** Use Browserbase (no download required), or mirror the repo via a faster proxy.

**Post-install setup:**
```bash
# Start the server
npm start

# In ~/.hermes/.env on the machine running Hermes:
CAMOFOX_URL=http://localhost:9377
```

---

## Quick Diagnosis Checklist

```bash
# 1. Is browser toolset enabled?
hermes tools list | grep browser

# 2. Is a browser backend configured?
grep -E "BROWSERBASE|CAMOFOX" ~/.hermes/.env

# 3. Is camofox-server running (if using Camofox)?
curl -s http://localhost:9377/health || echo "Camofox not running"
```

---

## Decision Matrix

| Situation | Recommended Backend |
|----------|---------------------|
| Quick setup, don't care about cost | Browserbase API key |
| Free tier needed, fast network | Camofox via npm |
| Network restricted/slow | Browserbase (cloud) |
| Running on Mac mini with good network | Camofox via npm |
| Docker available | Camofox via Docker |
| No npm, no docker, no git | Browserbase only |

---

## On This System (Mac-Pro.local)

- Docker: ❌ not installed
- Node/npm: ✅ available (v22.16.0 / 10.9.2)
- Camofox npm install: ❌ timed out (300MB download)
- GitHub network: ❌ also timed out
- Browserbase: ✅ available (just needs API key)
