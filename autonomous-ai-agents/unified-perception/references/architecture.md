# Unified Perception Layer — Design & Architecture

## Why a Unified Perception Layer?

Before this layer, Hermes had:
- **browser_snapshot** → CDP AX tree → text snapshot + refs
- **baidu-ocr tool** → screenshot → raw text
- **Jina Reader** → URL → markdown
- **hermes-rpa** → AppleScript AXUI → window structure

Each spoke its own language. The Agent had to understand 4+ different output formats.
The ElementRegistry was implicit in agent-browser's ref IDs, but reset every turn.

The unification goal: **one data model, one registry, one LLM-facing format.**

## Data Flow Design

```
Agent decides to "look at the page"
         │
         ▼
perceive_what("browser")
         │
         ▼
PerceptionEngine.perceive_browser()
         │
         ├─ BrowserPerception.perceive_full()
         │     └─ subprocess: npx agent-browser snapshot -c -J <key>
         │           └─ parse axNodes[] + refs → PerceptionElement[]
         │
         ├─ ElementRegistry.register() — dedup + merge action history
         │
         └─ format_snapshot_for_llm() → LLM-readable text
```

## PerceptionElement ID Convention

The `perception_id` is a stable identifier for element merging:

- `browser_cdp:page@{nodeId}` — CDP AX node
- `browser_cdp:page@{ref}` — CDP element with an agent-browser ref (e1, e2...)
- `screenshot_ocr:region@{timestamp_index}` — OCR text region
- `jina_reader:url@{line_index}` — Jina markdown line

When `register()` sees an existing element with the same `perception_id`, it:
1. Keeps the old `action_count` + `last_action`
2. Updates all other fields (name, value, checked, etc.)
3. Returns the existing ref (e1, not a new one)

This means: "the '登录' button still has ref e1 even after the page updates."

## ElementRegistry Cross-turn State Flow

```
Turn 1: perceive_browser() → @e1 [button] "登录"  action_count=0
Turn 1: Agent clicks @e1 → perceive_element("e1", "click")  → count=1
Turn 2: page changes → perceive_browser() → @e1 [button] "登录"  action_count=1  (last: click)
Turn 2: format_snapshot → "@e1 [button] "登录" (last: click x1)"  ← Agent knows already clicked
```

This is the key behavioral difference from the raw browser_snapshot tool.

## Why Not Just Patch browser_snapshot?

The existing `browser_snapshot` tool:
- Returns text via JSON, not structured elements
- Has no action history tracking
- Has no cross-source unification
- Ref IDs are ephemeral (reset every snapshot)

The perception layer adds value *on top of* these existing tools without breaking them.
