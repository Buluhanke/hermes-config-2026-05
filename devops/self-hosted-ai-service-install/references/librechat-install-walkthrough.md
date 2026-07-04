# LibreChat 0.8.7 Install Walkthrough — 2026-06-30

What actually happened when installing LibreChat on the Mac mini (24GB, ~5GB free after Hermes+Chrome+Claude).

## Sequence that worked

1. `git clone --depth 1 https://github.com/danny-avila/LibreChat.git LibreChat_install`
   - Full clone timed out past 60s. `--depth 1` finished in ~15s.
2. `cp .env.example .env` — got the template config
3. `cat .env | grep -i mongo` — discovered `MONGO_URI=mongodb://127.0.0.1:27017/LibreChat`
4. `which mongod` — NOT installed. **Stopped here and reported to user.**
5. `npm install` ran fine (3011 packages, ~1.8GB in `node_modules`)

## What blocked forward progress

- `mongod` not installed and not in any obvious tap
- `brew search mongodb` showed only `mongodb-atlas-cli` and `mongosh` — `mongodb-community` requires `brew tap mongodb/brew` first
- Memory: `top` showed `PhysMem: 19G used, 4675M unused` — tight but workable for `mongodb-community` (~300MB idle)

## Hermes gateway auth pitfall discovered

Tried to route LibreChat Custom Endpoint → `http://127.0.0.1:8642/v1`:
- First attempt with no `apiKey` → `401 invalid api key`
- Tried `OPENAI_API_KEY` from `.env` → still `401`
- `ps eww -p 2440 | grep API_KEY` showed **no API key env var in the gateway process** — meaning the gateway forwards auth to upstream provider
- Fix: set LibreChat `apiKey` to whatever the gateway validates, or use the gateway's actual auth scheme

## Patterns that should be reusable for Open WebUI / n8n / Flowise

- **Always `--depth 1`** on exploration clones of repos >100MB
- **Always check `which mongod` / `which redis-cli` / `which postgres`** before `npm install`
- **Always `top -l 1 -n 0` before** any `brew install` of a long-running service
- **Always present方案 A/B/C** with memory estimates before running anything that calls `brew services start`

## Files left on disk after this session

If the user asks to clean up later:
- `~/.hermes/LibreChat_install/` — full clone + node_modules (1.8GB)
- `~/.hermes/LibreChat_install/.env` — has placeholder config, no real keys
- No brew installs done yet (waiting for user go-ahead)

## What to do next time the user says "装 LibreChat"

Skip the exploration, go straight to:

```bash
brew tap mongodb/brew && brew install mongodb-community
brew services start mongodb-community
mongosh --eval "db.runCommand({ping:1})"
cd ~/projects && git clone --depth 1 https://github.com/danny-avila/LibreChat.git
cd LibreChat && cp .env.example .env
# edit .env → MONGO_URI + provider config
npm install
npm run backend:dev    # verify it starts cleanly
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3080/
```

Then verify the chat flow end-to-end with a real message before reporting "done".