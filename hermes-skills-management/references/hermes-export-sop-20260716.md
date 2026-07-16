# Hermes 全量导出 SOP — 2026-07-16

## 何时用

将本机 Hermes 的技能库、自研脚本、工程模块、记忆系统完整迁移到另一台 Hermes 机器。

## 导出前必读：数据库路径澄清

| 数据库 | 路径 | 用途 |
|--------|------|------|
| `fact_store.db` | `~/.hermes/fact_store.db` | **这是活跃知识库**（3.8MB，133条facts） |
| `memory_store.db` | `~/.hermes/memory_store.db` | self_evolution.sh 内部使用 |
| `perception_memory.db` | `~/.hermes/perception_memory.db` | 感知记忆系统 |
| `state.db` | `~/.hermes/state.db` | 运行数据（689MB，含 sessions） |
| `self_model.json` | `~/.hermes/state/` | 能力画像+14天失败模式 |

**常见错误：把 `memory_store.db` 当成知识库导出 — 它是 self_evolution.sh 的工作文件，不是 fact_store。**

## 标准导出流程

### 1. 创建导出目录

```bash
mkdir -p ~/Desktop/hermes-export/{skills,scripts,cron,memories,engineering}
```

### 2. 脱敏 config.yaml

```python
# Python regex scrub，比 sed 更可靠
import re

with open('~/.hermes/config.yaml') as f:
    content = f.read()

patterns = [
    (r'api_key:\s*["\'][^"\']{8,}["\']', 'api_key: ""'),
    (r'key_env:\s*["\'][^"\']{8,}["\']', 'key_env: "YOUR_KEY_ENV"'),
    (r'password_hash:\s*["\'][^"\']{8,}["\']', 'password_hash: ""'),
]
for pat, repl in patterns:
    content = re.sub(pat, repl, content)
```

### 3. 模板 .env

```bash
# 只复制键名，不复制值
cat ~/.hermes/.env | sed 's/=.*/=YOUR_VALUE/' > ~/Desktop/hermes-export/.env
```

### 4. 批量 scrub 脚本（最关键）

```python
import re, os

def scrub_file(path):
    with open(path, 'r') as f:
        content = f.read()
    original = content

    patterns = [
        (r'sk-[a-zA-Z0-9]{20,}', 'sk-YOUR_KEY'),
        (r'ghp_[a-zA-Z0-9]{20,}', 'ghp_YOUR_TOKEN'),
        (r'nvapi-[a-zA-Z0-9_-]{20,}', 'nvapi-YOUR_KEY'),
        (r'fc-[a-zA-Z0-9]{20,}', 'fc-YOUR_KEY'),
        (r'OPENROUTER_API_KEY\s*=\s*["\'][^"\']{8,}["\']', 'OPENROUTER_API_KEY="YOUR_KEY"'),
        (r'GEMINI_API_KEY\s*=\s*["\'][^"\']{8,}["\']', 'GEMINI_API_KEY="YOUR_KEY"'),
        # ... 其他常见 API key 模式
    ]
    for pat, repl in patterns:
        content = re.sub(pat, repl, content)

    if content != original:
        with open(path, 'w') as f:
            f.write(content)
        return True
    return False
```

### 5. 复制内容

```bash
# 配置文件
cp ~/.hermes/config.yaml ~/Desktop/hermes-export/
cp ~/.hermes/.env ~/Desktop/hermes-export/.env

# 记忆文件
cp ~/.hermes/memories/MEMORY.md ~/Desktop/hermes-export/
cp ~/.hermes/memories/USER.md ~/Desktop/hermes-export/

# 能力画像
cp ~/.hermes/state/self_model.json ~/Desktop/hermes-export/

# 技能库（排除归档）
cp -r ~/.hermes/skills/* ~/Desktop/hermes-export/skills/

# 自研脚本
cp -r ~/.hermes/scripts/* ~/Desktop/hermes-export/scripts/

# cron 任务
cp ~/.hermes/cron/*.yaml ~/Desktop/hermes-export/cron/

# 工程模块
cp -r ~/.hermes/engineering/* ~/Desktop/hermes-export/engineering/

# 技能索引
cp ~/.hermes/skills/_skill_index.md ~/Desktop/hermes-export/
```

### 6. 清理

```bash
# 删除空目录和缓存
find ~/Desktop/hermes-export -type d -name "__pycache__" -exec rm -rf {} +
find ~/Desktop/hermes-export -name ".DS_Store" -delete

# 清理 anysearch 的 .env（复制过来的 key）
find ~/Desktop/hermes-export/skills/anysearch -name ".env" -exec truncate -s 0 {} +

# 验证无敏感信息残留
grep -rE "sk-[a-zA-Z0-9]{20,}|ghp_[a-zA-Z0-9]{20,}|nvapi-[a-zA-Z0-9_-]{20,}" ~/Desktop/hermes-export/ | grep -v "YOUR\|placeholder\|xx\.\.\." | wc -l
# 结果为 0 才算通过
```

### 7. 打包

```bash
cd ~/Desktop
tar -cvf hermes-export.tar hermes-export/
gzip hermes-export.tar
# 生成 hermes-export.tar.gz（约 1.4MB）
```

## 包结构

```
hermes-export/
├── README.md              # 安装说明（必须手写）
├── config.yaml            # 脱敏配置
├── .env                   # 环境变量模板
├── self_model.json        # 能力画像
├── MEMORY.md             # 长期记忆
├── USER.md               # 用户画像
├── _skill_index.md       # 技能索引
├── AGENTS.md             # Hermes 开发指南
├── skills/               # 72个技能
├── scripts/              # ~150个自研脚本
├── engineering/           # 40+工程模块
├── cron/                 # 3个定时任务
└── memories/             # 概念存储
```

## 导入另一台机器

```bash
# 1. 解压
tar -xzf hermes-export.tar.gz -C ~/

# 2. 安装技能
cp -r hermes-export/skills/* ~/.hermes/skills/

# 3. 安装脚本
cp -r hermes-export/scripts/* ~/.hermes/scripts/

# 4. 配置（手动填入 API keys）
cp hermes-export/.env ~/.hermes/.env
# 编辑 ~/.hermes/.env，填入真实 keys

# 5. cron
cp hermes-export/cron/*.yaml ~/.hermes/cron/

# 6. 工程模块
cp -r hermes-export/engineering/* ~/.hermes/engineering/
```

## 导出清单（本次 2026-07-16）

- 技能：53个（活跃 depth-1）
- 脚本：204个（含 deprecated-2026-07-04）
- 工程模块：39个目录
- cron：3个任务
- 记忆：MEMORY.md + USER.md + concept_store.md
- 包大小：5.3MB（压缩后 1.4MB）
- 敏感信息：0条残留
