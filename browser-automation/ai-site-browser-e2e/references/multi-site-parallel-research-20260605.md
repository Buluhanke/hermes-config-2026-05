# Multi-Site Parallel Research Pattern
# Session: 2026-06-05 — "ollama 8b mac mini m4" cross-validation across 5 AI sites

## Pattern: Send First, Read Later

When researching a single question across multiple AI sites simultaneously:

1. **Send to all sites in sequence** (don't wait for replies)
2. **Read responses** from sites that persist conversation history in sidebar
3. **Read in-page** from sites that don't persist history

### Site State Persistence Taxonomy (verified 2026-06-05)

| Site | Persists in sidebar after send? | Read strategy |
|------|--------------------------------|--------------|
| **DeepSeek** chat.deepseek.com | ✅ YES — "Mac mini本地运行8B模型配置" appears in sidebar immediately | Navigate back later, click sidebar entry |
| **Doubao** doubao.com | ✅ YES — "Mac mini M4 Ollama 8B配置方案" in sidebar | Navigate back later, click sidebar entry |
| **Grok** grok.com | ✅ YES — "Mac Mini M4 Ollama 8B Q4KM Memory Optimization" in sidebar | Navigate back, click sidebar entry |
| **Claude** claude.ai | ✅ (assumed, has chat history) | Click sidebar history entry |
| **ChatGLM** chatglm.cn | ✅ (assumed, has chat history) | Click sidebar history entry |
| **Perplexity** perplexity.ai | ✅ (assumed, has history) | Click sidebar entry |
| **Kimi** kimi.moonshot.cn | ✅ (assumed, has history) | Click sidebar entry |
| **Tongyi** tongyi.com | ✅ (assumed, has history) | Click sidebar entry |
| **Poe** poe.com | ✅ (assumed, has chat history) | Click sidebar entry |
| **Gemini** gemini.google.com | ❌ NO — conversation does NOT appear in sidebar (temp chat mode) | Read response IN-PAGE immediately after sending, before navigating away |
| **ChatGPT** chatgpt.com | ❌ NO — new conversation does NOT appear in sidebar | Read response IN-PAGE immediately after sending |
| **Copilot** copilot.microsoft.com | ❌ (likely NO) | Read in-page immediately |

### Efficient Read Order

1. First: read DeepSeek + Grok + Doubao (sidebar persistence → can navigate away and back)
2. Then: read Gemini + ChatGPT immediately (no sidebar persistence → must read before navigating)

### The Key Insight

Sites with sidebar persistence are safe to navigate away from — their conversation titles appear in the sidebar within seconds of sending, and the full response is available even after navigating to other tabs.

Sites without sidebar persistence: read the response in the current tab **immediately after streaming completes**, before navigating away. If you navigate away without reading, the conversation may not reappear.

### Cloudflare Behavior

- Perplexity and Poe trigger Cloudflare on FIRST navigation (shows "正在进行安全验证" with CAPTCHA iframe). Waiting 5s + re-navigating resolves it. Not a login failure.
- Copilot triggers Cloudflare via CDP (site is aggressive against automated clients). Local Chrome CDP works fine once the user is logged in.

### Sending to All Sites: 12-site question broadcast

```python
# Step 1: Broadcast question to all 12 sites (parallel-friendly)
sites = [
    "https://chat.deepseek.com/",
    "https://gemini.google.com/app",
    "https://chatgpt.com/",
    "https://grok.com/",
    "https://www.doubao.com/chat",
    "https://chatglm.cn/main/alltoolsdetail",
    "https://www.perplexity.ai/",
    "https://kimi.moonshot.cn",
    "https://tongyi.com",
    "https://copilot.microsoft.com",
    "https://poe.com",
    "https://claude.ai",
]
for url in sites:
    browser_navigate(url)  # sends in sequence; responses stream in background

# Step 2: Read sidebar-persistent sites (can navigate away safely)
# DeepSeek → Grok → Doubao → Kimi → Tongyi → ChatGLM → Perplexity → Poe → Claude
# Navigate to each, click sidebar entry, read via browser_console(document.body.innerText)

# Step 3: Read non-persistent sites immediately (before navigating away)
# Gemini → ChatGPT → Copilot
# Read via browser_console or browser_snapshot right after streaming completes
```

## What NOT to Do

- Don't assume ChatGPT or Gemini will show the conversation in sidebar — they often don't
- Don't navigate away from Gemini/ChatGPT before reading — the conversation may disappear
- Don't wait for ALL sites to finish before reading ANY — read sidebar-persistent sites first while the others are still streaming
