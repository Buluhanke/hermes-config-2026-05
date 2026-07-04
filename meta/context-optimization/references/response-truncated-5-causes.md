# Response Truncated — 5 Causes Deep Reference

Source: betterclaw.io/blog/hermes-response-truncated-fix (2026-06-28 updated)
Cross-ref: GitHub #7237 #4404 #14690 #22879 #26425
Captured: 2026-07-02 idle learning round

## Quick Decision Table

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Set max_tokens in config.yaml, still truncating | Bug #4404 — config value never reaches API | `HERMES_MAX_TOKENS=8192` in .env |
| Ollama truncating mid-sentence | Default num_ctx=2048 | Modelfile: `num_ctx 8192` + `num_predict 1024` |
| Works short prompts, fails long ones | Context-window math error | Match context_length to model |
| /compress not working or history lost | Compression bug #14690 | `hermes update` |
| OpenRouter: truncates on long responses | Credit reservation #22879 | Top up or switch provider |

## Full Reproduction Trace (from #7237)

1. Start `hermes chat` or gateway
2. Send: "Write a complete Python automated trading strategy with backtesting..."
3. Agent generates ~20s, then: `Error: Response truncated due to output length limit`
4. Output is cut mid-function — completely unusable

## Bug #4404 Details

The `_build_api_kwargs()` method in `agent/conversation_loop.py` never reads `self.max_tokens` from config. Community PR on `fix/model-max-tokens-config` branch. Workaround via HERMES_MAX_TOKENS env var works because it's read at a different point in the code path.

## Ollama Specifics

```
ollama show <model>          # shows current context window
ollama show --modelfile <model>  # shows current Modelfile params
```

Default Modelfile fix:
```
FROM hermes3:8b
PARAMETER num_ctx 8192
PARAMETER num_predict 1024
```

`num_ctx` = total context window (input + output).
`num_predict` = max output tokens specifically.

## Community Workarounds (when official fixes don't apply)

1. **Conversation loop continuation**: Hermes v0.17+ has auto-continuation for truncated responses — but it's not always reliable.
2. **Context-compression skill** (installed at ~/.hermes/skills/context-compression/): Anchored Iterative Summarization at 70-80% utilization threshold.
3. **Split work into sessions**: Use /task to break long work into separate sessions with independent context windows.
4. **Model downgrade**: Some smaller models have larger effective context windows (less internal overhead on attention).
