# TuriX-CUA — macOS Desktop CUA Agent

**GitHub:** https://github.com/TurixAI/TuriX-CUA (2.9K⭐, MIT)
**Python:** 97.8%, macOS only (Apple Silicon + Intel)
**Approach:** Screen capture → vision LLM → pyautogui/pynput keyboard/mouse control

## Installation (macOS, working method)

```bash
# 1. Clone (needs proxy for github.com)
cd ~/.hermes
git clone https://github.com/TurixAI/TuriX-CUA.git turix-cua

# 2. Create venv (Python 3.14 proven working despite README saying 3.12)
cd ~/.hermes/turix-cua
python3 -m venv turix_venv
source turix_venv/bin/activate

# 3. Install deps (needs proxy)
ALL_PROXY=http://127.0.0.1:7897 pip install -r requirements.txt

# 4. Install Playwright Chromium (needs proxy)
ALL_PROXY=http://127.0.0.1:7897 playwright install chromium
```

**Tested:** 35+ packages including langchain~1.x, pyobjc (macOS bridge), playwright, pyautogui, pynput — all install cleanly on macOS Apple Silicon.

## Config (OpenAI-compatible, no Turix cloud needed)

Edit `examples/config.json`. The `build_llm()` function in `examples/main.py` supports these providers:

| provider    | backing class      | notes                              |
|-------------|-------------------|-------------------------------------|
| `gpt`       | ChatOpenAI        | Any OpenAI-compatible API endpoint  |
| `deepseek`  | ChatOpenAI        | Default: api.deepseek.com           |
| `minimax`   | ChatOpenAI        | Default: api.minimax.chat           |
| `kimi`      | ChatOpenAI        | Default: api.moonshot.cn            |
| `ollama`    | ChatOllama        | Local models                        |
| `turix`     | ChatOpenAI        | Turix cloud API (requires key)      |
| `google_flash`| ChatGoogleGenAI | gemini-2.5-flash                    |
| `google_pro`| ChatGoogleGenAI  | gemini-2.5-pro                      |
| `anthropic` | ChatAnthropic     | claude-4-opus                       |

**Example config for aicodee (MiniMax M2.7 via v2.aicodee.com):**

```json
{
  "brain_llm": {
    "provider": "gpt",
    "model_name": "minimax-m2.7-highspeed",
    "api_key": "YOUR_API_KEY...",
    "base_url": "https://v2.aicodee.com/v1"
  }
}
```

Each of the 4 LLM slots (brain, actor, planner, memory) can use a different provider/model.

**Note:** MiniMax models have `supports_response_format=false` — the code auto-detects this via identity string matching and falls back to prompt-only JSON. This is less reliable than native structured output but functional.

## UUID Guard

`planner_service.py` wraps `uuid.uuid4()` in a `@lru_cache` — don't call `from_llm()` from multiple agents in the same process without per-agent UUID seeding.

## Permissions Required

1. **Screen Recording** — System Settings → Privacy & Security → Screen Recording → add Terminal
2. **Accessibility** — System Settings → Privacy & Security → Accessibility → add Terminal

## Verification

```python
# Check permissions
python3 -c "
import ctypes
cg = ctypes.cdll.LoadLibrary('/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics')
print(f'Screen capture: {cg.CGPreflightScreenCaptureAccess()}')
"
```

## Run

```bash
cd ~/.hermes/turix-cua
source turix_venv/bin/activate
python examples/main.py -c examples/config.json
```

Force-stop hotkey: `Cmd+Shift+2`

## Pitfalls

1. **Conda not required** — venv + pip works fine, no need to install conda/mambaforge.
2. **Proxy needed for GitHub clone + pip install + playwright browser download** — use `ALL_PROXY=http://127.0.0.1:7897`.
3. **4 separate LLM calls per step** — brain + actor + planner + memory = 4 API calls per agent step. Token consumption is high.
4. **MiniMax models detected as unsupported for response_format** — automatic fallback to prompt-only JSON. If structured output errors occur, switch to a model that supports it (e.g. GPT-4o, Claude).
5. **Screen recording permission required** — without it, screenshots are blank.
6. **Accessibility permission required** — without it, UI tree building fails silently.
