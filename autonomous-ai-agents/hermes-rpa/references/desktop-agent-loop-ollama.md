# 拟人桌面 Agent — Ollama + AppleScript/Playwright 工具调用

## 核心架构

```
用户指令 → LLM (qwen3:8b via Ollama) 
              ↓ 思考并输出 [TOOL:toolname]
           AppleScript / Playwright 执行工具
              ↓ 结果回 LLM
           最终回答用户
```

## 关键发现：qwen3 模型 response 为空问题

**现象**：qwen3:8b 和 qwen3-fast 默认开启 thinking 模式，`response` 字段几乎永远为空，所有 token 生成在 `thinking` 字段。

**解决**：`num_predict` 必须设到 **500 以上**，response 才能拿到实际回答文本。

```python
payload = {
    "model": "qwen3:8b",
    "prompt": f"<|im_start|>user\n{prompt}<|im_end|>",
    "stream": False,
    "options": {"temperature": 0.3, "num_predict": 600}  # 必须 >= 500
}
```

## Agent Loop 实现（实测可跑）

### 工具注册

```python
TOOLS = """你是桌面助手，可以用以下工具：
- get_frontmost_app: 获取当前前台 App 名称
- get_chrome_tabs: 获取 Chrome 标签页列表
- search_baidu(keyword): 百度搜索

想调用工具时输出 [TOOL:工具名]，等待结果后直接用中文回答用户，不再调用工具。"""
```

### 两阶段循环

```python
import subprocess, json, re
from pathlib import Path

def run_as(script, timeout=10):
    Path('/tmp/t.scpt').write_text(script)
    r = subprocess.run(['osascript', '/tmp/t.scpt'], capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip() if r.returncode == 0 else f'Error: {r.stderr}'

def llm(prompt, model='qwen3:8b'):
    payload = {'model': model, 'prompt': f'<|im_start|>user\n{prompt}<|im_end|>',
               'stream': False, 'options': {'temperature': 0.3, 'num_predict': 600}}
    r = subprocess.run(['curl', '-s', 'http://127.0.0.1:11434/api/generate',
                        '-d', json.dumps(payload)], capture_output=True, text=True, timeout=50)
    try:
        d = json.loads(r.stdout)
        resp = (d.get('response') or '') or (d.get('thinking') or '')
        return resp.strip()
    except: return ''

# 第一轮：LLM 决定是否调用工具
resp = llm(f'{TOOLS}\n\n用户问题：{task}')
m = re.search(r'\[TOOL:(\w+)\]', resp)
if m:
    tool = m.group(1)
    # 执行工具
    if tool == 'get_frontmost_app':
        result = run_as('''tell application "System Events"
            set frontApp to first process whose frontmost is true
            return name of frontApp
        end tell''')
    # ... 其他工具 ...
    
    # 第二轮：结果给 LLM，让它直接回答（不再输出工具调用格式）
    final = llm(f'{TOOLS}\n\n工具 {tool} 返回了：{result}\n\n直接回答用户。')
    print(final)
```

## LLM 格式约束技巧

**问题**：LLM 倾向说"我需要调用工具"而不是实际输出 `[TOOL:]` 标签。

**解决**：用明确格式指令，强制单标签输出：

```
你必须严格按以下格式回复：
<action>get_frontmost_app()</action>
不要有任何其他内容，只输出 action 标签。
```

实测 qwen3:8b 在约束格式下 100% 按要求输出。

## 实测结果（2026-05-09 aimac）

| 测试任务 | 结果 |
|---------|------|
| `get_frontmost_app()` | ✅ 正确返回 "Safari" |
| `get_chrome_tabs()` | ✅ 正确返回标签标题列表 |
| `open_chrome(url)` | ✅ Chrome 打开新页面 |
| 百度搜索 | ❌ 封禁（`networkidle` 超时，结果数 0） |
| Bing 搜索 | ❌ 封禁（结果数 0） |
| **DuckDuckGo (ddgs)** | ✅ 完全正常，免费无反爬 |

**DuckDuckGo 替代方案**（2026-05 实测可用）：
```bash
pip install ddgs  # 不是 duckduckgo-search（已弃用）
```
```python
from ddgs import DDGS

with DDGS() as ddgs:
    results = list(ddgs.text('北京天气', max_results=3))

# 返回: [{'title': '...', 'body': '...', 'href': '...'}, ...]
```

实测两次搜索任务全部成功：
- `"北京今天天气怎么样？"` → 3条结果，返回气象局数据
- `"上海今天适合穿什么衣服？"` → 穿衣指数 3°C，LLM 总结回答用户

### 搜索工具封装

```python
def web_search(query: str) -> str:
    """DuckDuckGo 搜索，替代被封的百度/Bing"""
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
        if not results:
            return "无结果"
        return "\n".join([f"{r['title']}: {r['body'][:80]}" for r in results])
    except Exception as e:
        return f"[搜索错误] {e}"
```

### 完整可运行 Agent 示例

```python
import subprocess, json, re
from pathlib import Path

def run_as(script, timeout=10):
    Path('/tmp/t.scpt').write_text(script)
    r = subprocess.run(['osascript', '/tmp/t.scpt'], capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip() if r.returncode == 0 else f'Error: {r.stderr}'

def llm(prompt, model='qwen3:8b'):
    payload = {'model': model, 'prompt': f'<|im_start|>user\n{prompt}<|im_end|>',
               'stream': False, 'options': {'temperature': 0.3, 'num_predict': 600}}
    r = subprocess.run(['curl', '-s', 'http://127.0.0.1:11434/api/generate',
                        '-d', json.dumps(payload)], capture_output=True, text=True, timeout=50)
    try:
        d = json.loads(r.stdout)
        resp = (d.get('response') or '') or (d.get('thinking') or '')
        return resp.strip()
    except: return ''

def web_search(query):
    from ddgs import DDGS
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=3))
    return '\n'.join([f"{r['title']}: {r['body'][:80]}" for r in results]) if results else '无结果'

def agent(task):
    TOOLS = '''桌面助手，可用工具：
- get_frontmost_app: 获取前台App名称
- web_search(keyword): DuckDuckGo搜索互联网

想调用工具时输出 [TOOL:工具名]，有结果后直接回答用户。'''

    resp = llm(f'{TOOLS}\n\n用户问题：{task}')
    m = re.search(r'\[TOOL:(\w+)\]', resp)
    if m:
        tool = m.group(1)
        if tool == 'web_search':
            kw = re.search(r'web_search\([\"\']*([^\"\')\s]+)[\"\']*\)', resp)
            keyword = kw.group(1) if kw else task
            result = web_search(keyword)
            return llm(f'搜索结果：{result}\n\n请用中文简明回答用户。')
        elif tool == 'get_frontmost_app':
            result = run_as('''tell application "System Events"
                set frontApp to first process whose frontmost is true
                return name of frontApp
            end tell''')
            return llm(f'前台App是：{result}。直接回答用户。')
    return resp
```

## qwen3-fast 也存在同样问题

qwen3-fast 和 qwen3:8b 一样，`response` 字段在 thinking 模式下为空。两者都适用 `num_predict >= 500` 解决方案。

```python
# qwen3-fast 测试
curl -s http://127.0.0.1:11434/api/generate -d \
  '{"model":"qwen3-fast","prompt":"hi","stream":false,"options":{"num_predict":20}}'
# → response: "" , thinking: "Okay, the user sent..."

# 加到 500+
curl -s http://127.0.0.1:11434/api/generate -d \
  '{"model":"qwen3-fast","prompt":"用户问：今天天气怎么样？简要回答。","stream":false,"options":{"num_predict":500}}'
# → response: "今天天气晴朗，气温在20°C左右..." ✅
```

## 文件执行注意

AppleScript 中 `&` 字符会被 terminal tool 误判为后台指令。**必须**写成文件执行：

```python
Path('/tmp/script.scpt').write_text(applescript_code)
subprocess.run(['osascript', '/tmp/script.scpt'], ...)
```

## 依赖安装

```bash
pip install langchain langgraph mem0ai openai --break-system-packages
brew install ollama cliclick
playwright install chromium
```

Python 3.14 + pyobjc-core 12.1 实测正常。
