# GitHub项目快速安装模式

用户给一个GitHub项目名或链接，要求"安装"，遵循此流程：

## 标准流程

1. **克隆到~/.hermes/**
   ```python
   subprocess.run(["git", "clone", url, target_dir])
   # 例：target_dir = f"{hermes}/mirofish"
   ```

2. **读README识安装方式**
   先读前100行，识别：包管理器（npm/pip/uv/cargo）、语言（Node/Python/Rust）、启动命令

3. **按技术栈安装**

### Node.js项目
```bash
# npm workspaces项目
git clone url ~/.hermes/<project>
cd ~/.hermes/<project>
npm install                           # 根依赖
cd frontend && npm install && cd ..  # 前端单独装
npm run dev                          # 启动
```

### Python项目（uv）
```bash
git clone url ~/.hermes/<project>
cd ~/.hermes/<project>
uv sync                              # 自动创建.venv
uv run python run.py                 # 启动
# 如遇Python 3.13问题：uv sync --python python3.12
```

### Homebrew项目
```bash
brew install <pkg>                   # 后台跑，超时用Popen轮询
which <pkg>                         # 验证
<pkg> --version                     # 验证
```

### Rust项目
```bash
cargo install --git <url>
# 或 curl -fsSL <install.sh> | sh
```

## 后台启动模式

需要后台长期运行的服务（web服务等）：
```python
import subprocess, os, time

proc = subprocess.Popen(
    ["npm", "run", "dev"],  # 或 ["python", "run.py"]
    cwd=project_dir,
    stdout=open(log_path, "w"),
    stderr=subprocess.STDOUT,
    start_new_session=True
)
time.sleep(8)
# 验证进程存活 + 端口监听
```

**检查清单**：
- [x] 进程存活（`ps -p PID`）
- [x] 端口监听（`lsof -i :PORT`）
- [x] 日志无ERROR
- [x] 能curl通 localhost:PORT

## 项目信息记录

安装后把项目信息写入memory：
- 项目名、GitHub地址、star数、用途
- 安装位置、启动命令、端口
- 遇到的问题和解决

```python
memory({"action":"add", "content": "MiroFish: ~/$ her...（已记录）", "target":"memory"})
```
