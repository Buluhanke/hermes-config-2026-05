# Python环境与uv版本兼容

## Python 3.13 兼容性问题

部分AI工具的Python依赖尚未支持Python 3.13，常见报错：
- `KeyError: '__version__'` + Pillow相关
- `camel-oasis` / `pillow` 构建失败

**典型场景**：MiroFish后端（依赖camel-oasis→pillow）用Python 3.13无法安装。

**解法**：
```python
# 方案A：uv指定Python版本（推荐）
uv sync --python python3.12   # 不依赖系统Python有uv模块

# 方案B：检查可用Python版本
import subprocess
r = subprocess.run(["python3.12", "--version"], capture_output=True, text=True)
# python3.12存在时用方案A
```

**验证是否修复**：
```bash
cd backend && uv sync --python python3.12
# 观察输出是否出现 "Creating virtual environment at: .venv"
```

## uv sync 的 VIRTUAL_ENV 警告

报错：`warning: VIRTUAL_ENV=/Users/aimac/.hermes/hermes-agent/venv does not match the project environment path .venv`

原因：系统全局VIRTUAL_ENV变量指向其他项目，与当前`uv sync`项目冲突。

**解法**：在`uv sync`前unset VIRTUAL_ENV，或用`--python`指定独立环境。

## Homebrew 安装超时处理

`brew install` 在subprocess中有时会超时（网络慢、下载大包），但实际已成功。

**模式**：
```python
proc = subprocess.Popen(["brew", "install", "pkg"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
for i in range(24):  # 最多等2分钟
    time.sleep(5)
    r = subprocess.run(["ps", "-p", str(proc.pid)], capture_output=True, text=True)
    if r.returncode != 0:
        break
stdout, stderr = proc.communicate(timeout=10)
# 检查返回码和which确认是否成功
```

**关键点**：
- 返回码0 + `which pkg` 能找到 = 成功
- 即使之前超时报错，也要用此模式重试

## npm workspaces 项目安装顺序

典型项目结构（MiroFish）：
```
mirofish/
├── package.json          # root workspaces配置
├── frontend/
│   └── package.json
└── backend/
    └── package.json
```

**正确步骤**：
```bash
# 1. 根目录装根依赖
npm install

# 2. 如果 frontend 用 concurrently 跑 dev，先单独装 frontend 依赖
cd frontend && npm install && cd ..

# 3. 后端用 uv 处理Python依赖
cd backend && uv sync --python python3.12

# 4. 启动（根目录）
npm run dev
```

**常见错误**：
- `vite: command not found` → frontend依赖没装，先`npm install frontend/`
- `cd backend && uv sync` 失败 → 检查Python版本，降级到3.12
