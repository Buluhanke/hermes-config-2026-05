# OpenRouter Free Models Reference

## Testing an OpenRouter API Key

```python
import urllib.request, json

api_key = "YOUR_API_KEY-v1-YOUR-KEY-HERE"
url = "https://openrouter.ai/api/v1/models"
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}"})

with urllib.request.urlopen(req, timeout=15) as resp:
    data = json.loads(resp.read())
    models = data.get('data', [])
    # Handle both string '0' and numeric 0 for pricing
    free = [m for m in models if m.get('pricing', {}).get('prompt') == 0 or m.get('pricing', {}).get('prompt') == '0']
    print(f"Total: {len(models)}, Free: {len(free)}")
    for m in free[:10]:
        print(f"  {m['id']} — {m['name']} ({m.get('context_length', 0):,} tokens)")
```

## Free Models (as of 2026-05-02)

Currently 33 completely free models available on OpenRouter. Most are rate-limited at any given time — try alternatives if one returns 429.

### ✓ Currently Available & Reliable
These models showed consistent availability during testing:

| Model ID | Name | Context Length | Best For |
|----------|------|----------------|----------|
| `nvidia/nemotron-3-super-120b-a12b:free` | NVIDIA Nemotron 3 Super | 262,144 | General purpose, current session model |
| `openrouter/owl-alpha` | Owl Alpha | 1,048,756 | Agentic workloads, long context |
| `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` | NVIDIA Nemotron 3 Nano Omni | 256,000 | Multimodal reasoning |
| `nvidia/nemotron-3-nano-30b-a3b:free` | NVIDIA Nemotron 3 Nano | 256,000 | Efficient reasoning |
| `poolside/laguna-m.1:free` | Poolside Laguna M.1 | 131,072 | Coding agent |
| `poolside/laguna-xs.2:free` | Poolside Laguna XS.2 | 131,072 | Compact coding agent |
| `nousresearch/hermes-3-llama-3.1-405b:free` | Nous Hermes 3 405B | 131,072 | Complex reasoning |
| `openai/gpt-oss-20b:free` | OpenAI GPT OSS 20B | 131,072 | Open-weight model |
| `openai/gpt-oss-120b:free` | OpenAI GPT OSS 120B | 131,072 | MoE language model |
| `meta-llama/llama-3.3-70b-instruct:free` | Meta Llama 3.3 70B Instruct | 65,536 | General chat, reasoning |
| `meta-llama/llama-3.2-3b-instruct:free` | Meta Llama 3.2 3B Instruct | 131,072 | Advanced natural language |
| `z-ai/glm-4.5-air:free` | Z.ai GLM 4.5 Air | 131,072 | Lightweight flagship variant |
| `inclusionai/ling-2.6-1t:free` | inclusionAI Ling-2.6-1T | 262,144 | Trillion-parameter flagship |
| `tencent/hy3-preview:free` | Tencent Hy3 preview | 262,144 | MoE for agentic workflows |
| `qwen/qwen3-next-80b-a3b-instruct:free` | Qwen3 Next 80B A3B Instruct | 262,144 | Instruction-tuned chat |
| `qwen/qwen3-coder:free` | Qwen3 Coder 480B A35B | 262,000 | MoE code generation |
| `google/gemma-4-31b-it:free` | Google Gemma 4 31B Instruct | 262,144 | Dense multimodal model |
| `google/gemma-4-26b-a4b-it:free` | Google Gemma 4 26B A4B IT | 262,144 | MoE instruction-tuned |
| `google/gemma-3-27b-it:free` | Google Gemma 3 27B IT | 131,072 | Multimodal vision-language |
| `google/gemma-3-12b-it:free` | Google Gemma 3 12B IT | 32,768 | Multimodal vision-language |
| `google/gemma-3-4b-it:free` | Google Gemma 3 4B IT | 32,768 | Multimodal vision-language |
| `google/gemma-3n-e2b-it:free` | Google Gemma 3n E2B IT | 8,192 | Mobile-optimized multimodal |
| `google/gemma-3n-e4b-it:free` | Google Gemma 3n E4B IT | 8,192 | Low-resource device optimized |
| `liquid/lfm-2.5-1.2b-instruct:free` | LiquidAI LFM2.5 1.2B-Instruct | 32,768 | Fast on-device instruction |
| `liquid/lfm-2.5-1.2b-thinking:free` | LiquidAI LFM2.5 1.2B-Thinking | 32,768 | Reasoning-focused agentic |
| `minimax/minimax-m2.5:free` | MiniMax M2.5 | 196,608 | SOTA large language model |
| `nvidia/nemotron-nano-12b-v2-vl:free` | NVIDIA Nemotron Nano 12B 2 VL | 128,000 | Multimodal reasoning (video) |
| `nvidia/nemotron-nano-9b-v2:free` | NVIDIA Nemotron Nano 9B V2 | 128,000 | Scratch-trained LLM |
| `venice:uncensored:free` | Venice Uncensored Dolphin Mistral 24B | 32,768 | Uncensored chat |
| `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` | NVIDIA Nemotron 3 Nano Omni (reasoning) | 256,000 | Perception/context sub-agent |

### 📝 Notes on Availability
- **Rate limiting**: Most free models experience upstream rate limits. If you get 429 errors, try another model from the list.
- **Context lengths**: Vary significantly — choose based on your needs (8K for simple tasks, 256K+ for long documents/code).
- **Specializations**: Some models excel at specific tasks (coding, multimodal, reasoning, etc.).
- **Current session model**: `nvidia/nemotron-3-super-120b-a12b:free` was verified working during this session.

## Config for Hermes custom_providers

```yaml
model:
  default: MiniMax-M2.7-highspeed  # your main model
  provider: aicodee

fallback_providers:
  - provider: gemini
    model: gemini-2.0-flash
  - provider: openrouter
    model: liquid/lfm-2.5-1.2b-instruct:free

custom_providers:
  - api_key: YOUR_API_KEY-aicodee-key
    api_mode: chat_completions
    base_url: https://v2.aicodee.com/v1
    default_model: MiniMax-M2.7-highspeed
    name: aicodee

  - api_key: YOUR-GEMINI-KEY
    api_mode: chat_completions
    base_url: https://generativelanguage.googleapis.com/v1beta
    default_model: gemini-2.0-flash
    name: gemini

  - api_key: YOUR-OPENROUTER-KEY
    api_mode: chat_completions
    base_url: https://openrouter.ai/api/v1
    default_model: liquid/lfm-2.5-1.2b-instruct:free
    name: openrouter
```

## Critical Pitfalls

### fallback_providers Format (MUST be dict list, NOT string list)

**WRONG** — silent failure, automatic failover won't work:
```yaml
fallback_providers:
  - gemini        # strings — WRONG
  - openrouter
```

**CORRECT** — dict with `provider` and `model` required for each:
```yaml
fallback_providers:
  - provider: gemini
    model: gemini-2.0-flash
  - provider: openrouter
    model: liquid/lfm-2.5-1.2b-instruct:free
```

When format is wrong, Hermes silently ignores fallback — no error, no switching, just failures accumulate.

### Gemini API Key Format
Google Gemini API keys start with `AIza`. If you get `\"API key not valid\"`, the key is wrong or the service account has no quota.

Free tier: Limited requests/minute. 429 quota exceeded errors mean limit hit.

### OpenRouter API Base URL
Correct: `https://openrouter.ai/api/v1`  
Wrong: `https://openrouter.ai/v1` (missing `/api`)

### OpenRouter Free Model Availability
Free models are rate-limited upstream. If you get 429 \"Provider returned error\", try another free model — they rotate independently. `liquid/lfm-2.5-1.2b-instruct:free` was reliably available while larger models were rate-limited.

### Model Discovery Best Practice
When users ask about available models, always test connectivity rather than just reading configuration. Use:
1. `curl -s https://openrouter.ai/api/v1/models` to get fresh list
2. Filter for `pricing.prompt == 0` (free models)
3. Optionally test a sample request to verify actual availability

## Recommended Fallback Config for Free Model Auto-Switch
When using OpenRouter free models, configure `fallback_providers` with multiple free models to auto-switch on rate limits (429 errors). Example config applied in session 2026-05-02:

```yaml
fallback_providers:
  - provider: openrouter
    model: liquid/lfm-2.5-1.2b-instruct:free
  - provider: openrouter
    model: meta-llama/llama-3.3-70b-instruct:free
  - provider: openrouter
    model: minimax/minimax-m2.5:free
  - provider: openrouter
    model: google/gemma-3-27b-it:free
```

This config will automatically try the next model in the list if the current one returns a 429 rate limit error. Make sure to restart Hermes (CLI: `/quit` then `hermes`; Gateway: `hermes gateway restart`) after applying changes.
