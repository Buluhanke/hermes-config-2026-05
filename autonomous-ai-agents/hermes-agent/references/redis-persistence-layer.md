# Redis Persistence Layer — Hermes Agent

## What it does

Redis serves as a **hot-backup / crash-recovery layer** on top of Hermes's existing SQLite store. It is completely additive — SQLite remains the authoritative store, Redis is a non-critical cache that provides resilience for in-memory state.

**Three state types are currently persisted:**

| State | Location | Risk if lost |
|-------|----------|--------------|
| `_session_messages` (in-memory list) | `run_agent.py` AIAgent | **Critical** — crash during long task = entire conversation lost |
| `_todo_store` (in-memory list) | `tools/todo_tool.py` TodoStore | Medium — todos gone after crash |
| BrowserSupervisor snapshot | `tools/browser_supervisor.py` | Low — browser can be reconnected |

## Architecture

```
Hermes Agent (AIAgent)
  └─ _flush_messages_to_session_db()  ← SQLite write (primary, authoritative)
       └─ save_messages()              ← Redis write (hot backup, non-critical)
  └─ TodoStore.write()                ← both SQLite + Redis in same method
```

**Key design decisions:**
- Redis is **never the source of truth** — SQLite is always authoritative
- All Redis writes are wrapped in `try/except` — Redis failure never breaks the main path
- 24h TTL on all keys (auto-cleanup of stale sessions)
- Write-through: every Redis write is paired with a periodic SQLite flush (every 5 seconds)
- Session registry (`hermes:active_sessions` set) enables crash-recovery discovery

## File layout

```
~/.hermes/hermes-agent/
├── redis_persistence.py          # The Redis layer module
├── run_agent.py                   # Patched: _flush_messages_to_session_db()
└── tools/todo_tool.py            # Patched: TodoStore.write()
```

## Redis key patterns

```
hermes:{session_id}:messages      # JSON array of session messages
hermes:{session_id}:todos         # JSON {items: [...]} todo store
hermes:{session_id}:browser_state # JSON BrowserSupervisor snapshot
hermes:{session_id}:active        # Session metadata (registered_at, source)
hermes:active_sessions            # SET of currently-active session IDs
```

## Crash recovery procedure

```python
from redis_persistence import RedisPersistence, recover_session_state, list_recoverable_sessions

# 1. Find sessions that were running
active = list_recoverable_sessions()

# 2. Recover state for each
for session_id in active:
    state = recover_session_state(session_id)
    # state = {
    #   "messages": [...],        # or None
    #   "todos": {"items": [...]}, # or None
    #   "browser_state": {...}    # or None
    # }

# 3. Reconstruct AIAgent state
agent._session_messages = state["messages"] or []
agent._todo_store.write(state["todos"]["items"]) if state["todos"] else None
```

## Adding new state to the layer

To add another in-memory state type:

1. Choose a `kind` string (e.g., `"context"`)
2. Add methods in `RedisPersistence`:
   ```python
   def save_context(self, session_id: str, context: Dict) -> bool: ...
   def load_context(self, session_id: str) -> Optional[Dict]: ...
   ```
3. Call from the appropriate location in the source:
   ```python
   from redis_persistence import RedisPersistence
   rp = RedisPersistence.get_instance()
   if rp.available:
       rp.save_context(self.session_id, self._context)
   ```

## Installation prerequisites

Redis must be running on localhost:6379 (the Mac mini's Homebrew Redis service):

```bash
# Check if running
redis-cli ping  # → PONG

# Start if not
brew services start redis

# Python client (already in Hermes venv)
~/.hermes/hermes-agent/venv/bin/pip show redis  # should show 7.4.0+
```

## Gateway restart verification

After modifying `redis_persistence.py` or patching `run_agent.py`/`todo_tool.py`, always verify the gateway restarts cleanly:

```bash
~/.hermes/hermes-agent/venv/bin/hermes gateway restart
# Expected: "✓ Service restarted"

# Verify no import errors
cd ~/.hermes/hermes-agent && venv/bin/python -c "import redis_persistence; print('OK')"
```

## Relationship to SQLite

SQLite (`hermes_state.py`) is Hermes's **primary authoritative store**:
- WAL mode, FTS5 full-text search
- Survives process crashes (WAL journal)
- `_session_messages` in AIAgent is a **cache** of the SQLite data
- The Redis layer backs the **cache**, not the store

If Redis is unavailable: Hermes continues normally (all writes go to SQLite, Redis writes silently fail).

If SQLite is unavailable: Hermes **cannot function** (session history, compression, kanban — all depend on it).

## Future extensions (not yet implemented)

- **Browser session recovery**: Serialize BrowserSupervisor state → Redis → reconnect on restart
- **Task queue persistence**: RQ (Redis Queue) for long-running task checkpoint/resume
- **Memory provider over Redis**: `memory_manager` provider using Redis as backend
- **Pub/sub for multi-instance coordination**: Multiple Hermes instances sharing state via Redis pub/sub
