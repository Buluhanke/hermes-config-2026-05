# Open Interpreter Setup

## 1. Open Interpreter 是什么

Open Interpreter 是一个供人类用户交互使用的命令行工具，允许用户通过自然语言让本地大模型执行代码（Python/JavaScript/等）。它提供交互式 REPL 界面，用户逐条输入指令，OII 实时执行并返回结果。

**关键区分：OII 是为人设计的交互界面，不是为 AI Agent 设计的。** Agent 应通过 subprocess 直接调用 Python 脚本，而非调用 OII 的交互界面。

---

## 2. Ollama 本地模型配置

### 安装

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh
```

### 启动服务

```bash
# 启动 ollama 服务（后台运行）
ollama serve

# 拉取模型
ollama pull llama3.2
ollama pull codellama
ollama pull mistral

# 常用模型
ollama list
```

### API 格式

Ollama 提供 REST API：

```bash
# 对话
curl -X POST http://localhost:11434/api/chat \
  -d '{"model": "llama3.2", "messages": [{"role": "user", "content": "Hello"}]}'

# 生成补全
curl -X POST http://localhost:11434/api/generate \
  -d '{"model": "llama3.2", "prompt": "Write a Python function"}'

# 模型列表
curl http://localhost:11434/api/tags
```

Python SDK：
```bash
pip install ollama
```

```python
import ollama

response = ollama.chat(model='llama3.2', messages=[
    {'role': 'user', 'content': 'Hello'}
])
print(response['message']['content'])
```

---

## 3. Hermes 正确集成方式

**原则：subprocess 直接调用 Python，不使用 Open Interpreter 交互界面。**

### 错误方式
- 不要用 `subprocess` 调用 `interpreter` 命令进入交互模式
- 不要期望 Agent 能"借用" OII 的 REPL 会话

### 正确方式

让 Agent 生成并执行独立的 Python 脚本：

```python
import subprocess

def run_code_with_llm(code: str, model: str = "llama3.2") -> str:
    """
    通过 Ollama + Python 执行代码，返回结果。
    Agent 应生成代码字符串，传入此函数执行。
    """
    script = f"""
import ollama
result = ollama.chat(model='{model}', messages=[
    {{'role': 'user', 'content': '''Execute the following Python code and return only the output:
```python
{code}
```'''}}
])
print(result['message']['content'])
"""
    result = subprocess.run(
        ['python3', '-c', script],
        capture_output=True,
        text=True,
        timeout=300
    )
    return result.stdout + result.stderr

# 示例
code = "print([x**2 for x in range(10)])"
print(run_code_with_llm(code))
```

### 进阶：代码执行 + 结果解释双步

```python
import subprocess

def execute_via_llm(prompt: str, model: str = "llama3.2") -> dict:
    """
    1. 用 LLM 生成代码
    2. 用 LLM 解释执行结果
    """
    # Step 1: 生成代码
    gen_script = f"""
import ollama
resp = ollama.chat(model='{model}', messages=[
    {{'role': 'user', 'content': '''Given this task: {prompt}
Write ONLY Python code (no markdown, no explanation). Output ONLY the code.'''}}
])
print(resp['message']['content'])
"""
    gen_result = subprocess.run(
        ['python3', '-c', gen_script],
        capture_output=True,
        text=True,
        timeout=120
    )
    code = gen_result.stdout.strip()
    
    # Step 2: 执行代码
    exec_result = subprocess.run(
        ['python3', '-c', code],
        capture_output=True,
        text=True,
        timeout=300
    )
    
    return {
        'generated_code': code,
        'execution_output': exec_result.stdout + exec_result.stderr
    }
```

---

## 4. 安全隔离方案

### 方案 A：venv（推荐，单进程简单场景）

```bash
python3 -m venv ~/.hermes/oi-venv
source ~/.hermes/oi-venv/bin/activate
pip install ollama open-interpreter  # 按需安装
```

调用时指定虚拟环境 Python：
```python
python = "~/.hermes/oi-venv/bin/python3"
subprocess.run([python, '-c', script], ...)
```

### 方案 B：Docker（推荐，敏感数据/网络隔离场景）

```dockerfile
FROM python:3.11-slim

RUN pip install ollama && apt-get update && apt-get install -y curl && \
    curl -fsSL https://ollama.com/install.sh | sh

WORKDIR /workspace
CMD ["python3"]
```

构建并运行：
```bash
docker build -t oi-sandbox .
docker run --rm -v /tmp:/workspace oi-sandbox python3 -c "
import ollama
print(ollama.chat(model='llama3.2', messages=[
    {'role': 'user', 'content': 'print hello'}
]))
"
```

**注意**：Ollama 在容器内需要映射 socket 或在宿主机运行：
```bash
docker run --rm --network=host oi-sandbox
# 或通过环境变量指定 Ollama 端点
OLLAMA_HOST=http://host.docker.internal:11434
```

### 安全检查清单

- [ ] 敏感数据文件加 `.gitignore`，不要提交到仓库
- [ ] 网络访问需求用 `--network=none` 完全隔离（Docker）
- [ ] 执行超时：`timeout=300` 防止无限循环
- [ ] 输入清理：用户输入需经 `shlex.quote()` 转义后再拼接
- [ ] 资源限制：Docker `--memory=2g --cpus=1`

---

## 5. 适用场景

| 场景 | 说明 |
|------|------|
| 数据清洗 | CSV/JSON 批量处理、格式转换、去重、填充缺失值 |
| 图片处理 | 缩略图生成、格式转换（pillow）、EXIF 提取与修改 |
| 文件整理 | 按规则分类、移动、复制、重命名大量文件 |
| 日志分析 | 解析大日志文件、统计关键词、生成摘要 |
| 批量转换 | 文档格式转换（PDF→TXT）、编码转换 |
| Excel/CSV 操作 | 数据透视、公式计算、合并拆分 sheet |

**典型工作流**：Agent 生成 Python 脚本 → subprocess 执行 → 返回结果 → Agent 整理输出

---

## 6. 不适用场景

| 场景 | 原因 |
|------|------|
| 长期运行服务 | OII subprocess 是短时任务，不适合 daemon/常驻进程 |
| 图形界面交互 | 无法处理需要人工介入的 GUI 弹窗、验证码 |
| 调用网络 API（第三方） | 本地执行无法访问需要登录/OAuth 的外部服务 |
| 需要持久状态的场景 | 每次 subprocess 都是独立进程，无共享内存 |
| 实时性要求高的任务 | 每次调用都有进程启动开销 |
| 多步骤需要共享上下文 | 每次执行独立，无法保持变量状态 |

---

## 7. 实用代码模板

### 模板 1：Ollama 本地执行（最简）

```python
import subprocess

def ollama_run(prompt: str, model: str = "llama3.2") -> str:
    script = f"""
import ollama
resp = ollama.chat(model='{model}', messages=[
    {{'role': 'user', 'content': '''{prompt}'''}}
])
print(resp['message']['content'])
"""
    r = subprocess.run(['python3', '-c', script], capture_output=True, text=True, timeout=300)
    return r.stdout + r.stderr
```

### 模板 2：代码生成 + 执行 + 解释（三步）

```python
import subprocess, json

def code_agent(task: str, model: str = "llama3.2") -> dict:
    # Step 1: 生成代码
    gen = subprocess.run(['python3', '-c', f"""
import ollama
r = ollama.chat(model='{model}', messages=[{{
    'role': 'user',
    'content': f'Write ONLY Python code for: {{repr(task)}}. No explanation.'
}}])
print(r['message']['content'])
"""], capture_output=True, text=True, timeout=120)
    code = gen.stdout.strip()
    
    # Step 2: 执行
    exec_ = subprocess.run(['python3', '-c', code], capture_output=True, text=True, timeout=300)
    
    # Step 3: 解释结果
    explain = subprocess.run(['python3', '-c', f"""
import ollama
r = ollama.chat(model='{model}', messages=[{{
    'role': 'user',
    'content': f'Task: {{repr(task)}}\\nCode:\\n{{code}}\\nOutput: {{repr(exec_.stdout + exec_.stderr)}}\\nExplain the output.'
}}])
print(r['message']['content'])
"""], capture_output=True, text=True, timeout=120)
    
    return {'code': code, 'output': exec_.stdout + exec_.stderr, 'explanation': explain.stdout}
```

### 模板 3：安全沙箱执行（Docker + 超时）

```python
import subprocess, shlex

def safe_docker_exec(code: str, timeout: int = 300) -> str:
    # 清理输入
    safe_code = code.replace("'", "'\"'\"'")
    
    script = f"""
import ollama
r = ollama.chat(model='llama3.2', messages=[{{
    'role': 'user',
    'content': 'Execute and return output: ' + {repr(safe_code)}
}}])
print(r['message']['content'])
"""
    
    result = subprocess.run([
        'docker', 'run', '--rm',
        '--network=none',
        '--memory=2g',
        '--cpus=1',
        '-i', 'oi-sandbox',
        'python3', '-c', script
    ], capture_output=True, text=True, timeout=timeout + 30)
    
    return result.stdout + result.stderr
```

### 模板 4：批量文件处理

```python
import subprocess, glob

def batch_process_files(pattern: str, task: str, model: str = "llama3.2") -> dict:
    files = glob.glob(pattern)
    results = {}
    
    for f in files:
        with open(f) as fp:
            content = fp.read()
        
        script = f"""
import ollama
r = ollama.chat(model='{model}', messages=[{{
    'role': 'user',
    'content': f'File: {{repr(f)}}\\nContent: {{repr(content)}}\\nTask: {{repr(task)}}\\nReturn the modified content.'
}}])
print(r['message']['content'])
"""
        r = subprocess.run(['python3', '-c', script], capture_output=True, text=True, timeout=300)
        results[f] = r.stdout + r.stderr
    
    return results
```

---

## 快速参考

| 项目 | 命令/值 |
|------|---------|
| Ollama 端点 | `http://localhost:11434` |
| 常用模型 | `llama3.2`, `codellama`, `mistral`, `qwen2.5` |
| Python SDK | `pip install ollama` |
| venv 路径 | `~/.hermes/oi-venv/bin/python3` |
| Docker 镜像 | `oi-sandbox`（需提前 build）|
| 默认超时 | 300 秒 |