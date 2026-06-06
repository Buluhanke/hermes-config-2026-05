# macOS tar 实战坑（vs GNU tar）

macOS 默认 `tar` 是 BSD 变体（libarchive），跟 GNU tar 行为差异巨大。**写跨平台备份脚本前必看**。

## 坑 1：BSD tar 不支持 `--transform`

**症状**：
```bash
tar --transform 's|^\.hermes|hermes-home|' -czf out.tar.gz .hermes
# → tar: Option --transform is not supported
```

**GNU tar 的常用套路**：用 `--transform` 重写路径前缀，让包内路径不暴露真实目录名。

**macOS 修法**：放弃 `--transform`，打包时**用相对路径**，还原时 `--strip-components=N` 去掉前缀。

```bash
# 打包
cd $HOME
tar -czf out.tar.gz .hermes
# 包内路径: .hermes/state.db, .hermes/.env, ...

# 还原
tar --strip-components=1 -xzf out.tar.gz -C $HOME
# 解到: $HOME/state.db, $HOME/.env, ...
```

## 坑 2：BSD tar 对通配 exclude 支持弱

**症状**：
```bash
tar --exclude='*.log.*' --exclude='*.bak.*' --exclude='*/__pycache__/*' \
    -czf out.tar.gz .hermes
# → tar: dump: Error opening archive: No such file or directory
# 或 → tar: 只匹配了 0 个文件
```

**真相**：BSD tar 的 `--exclude` 是**字面前缀匹配**（类似 `^pattern`），不支持通配。

**修法**：用纯目录名 / 完整路径前缀，不要带通配：
```bash
tar \
    --exclude=.hermes/hermes-agent \
    --exclude=.hermes/lsp \
    --exclude=.hermes/bin \
    --exclude=.hermes/cache \
    --exclude=.hermes/.cache \
    --exclude=.hermes/screenshots \
    --exclude=.hermes/mcp-chrome-extension \
    --exclude=.hermes/.backups \
    --exclude=.hermes/.git \
    --exclude=.hermes/skills/.git \
    --exclude=.hermes/skills/.hub \
    --exclude=.hermes/skills/.curator_backups \
    --exclude=.hermes/.state \
    --exclude=.hermes/.update_check \
    --exclude=.hermes/logs \
    --exclude=.hermes/models_dev_cache.json \
    -czf out.tar.gz .hermes
```

**注**：`*.log.*` 这种"按扩展名排除"的诉求在 BSD tar 里**做不到**——只能把整个 .hermes/logs 目录排除。要更精细过滤用 `find + tar`：

```bash
# 想要排除 *.log.* 但保留 logs/ 目录本身
find .hermes -type f -not -name '*.log.*' -print0 | \
    tar --null --files-from=- -czf out.tar.gz
```

## 坑 3：BSD `paste` 命令 `-s` / `-d` 参数顺序与 GNU 相反

**症状**：
```bash
vm_stat | awk '...' | paste -sd+ | bc
# → usage: paste [-s] [-d delimiters] file ...
# → 计算结果 0
```

**修法**：别用 BSD paste，直接 python：
```python
import subprocess
o = subprocess.run(['vm_stat'], capture_output=True, text=True).stdout
def parse(key):
    for l in o.splitlines():
        if l.startswith(key):
            return int(l.split(':')[1].strip().rstrip('.'))
    return 0
free_mb = (parse('Pages free') * 16384) // (1024 * 1024)
```

完整 macOS 内存公式见 `macos-process-lifecycle/references/macos-vmstat-formulas.md`。

## 坑 4：BSD `ps` 不支持 `--sort`

**症状**：
```bash
ps aux --sort=-rss | head
# → ps: illegal option -- -
# 或 → ps: Unrecognized option
```

**修法**：外接 sort：
```bash
ps -A -o pid,rss,user,command | sort -k2 -nr | head -10
```

详见 `macos-process-lifecycle/SKILL.md` 的 "Bash 实战坑" 章节。

## 坑 5：`sed -i ''` 在 macOS 不报错也不真改

**症状**：
```bash
sed -i '' 's/foo/bar/' file.txt
# 无输出、无错, 但 file.txt 没改
```

**真相**：BSD sed 的 `-i` 需要空参数作为备份后缀（`''` = 不留备份），但**有时**操作不生效也不报错。

**修法**：
- ✅ 简单替换用 `sed -i '' 's/foo/bar/' file.txt` 仍可（多数情况生效）
- ✅ 复杂替换用 Python 一次性读+改+写：
```python
from pathlib import Path
p = Path('file.txt')
p.write_text(p.read_text().replace('foo', 'bar'))
```

详细案例见 `verification-before-reporting` 记忆条目 "BSD sed 假成功坑"。

## 坑 6：`date +%s` 输出格式差异

**GNU date**：`date +%s` → `1717670400`（秒）
**BSD date (macOS)**：`date +%s` → `1717670400`（兼容）

**GNU date**：`date -d "2024-01-01" +%s` → 可以
**BSD date**：`date -j -f "%Y-%m-%d" "2024-01-01" +%s` → 复杂

**通用修法**：用 python 的 `datetime`：
```python
from datetime import datetime
ts = int(datetime.now().timestamp())
# 或
ts = int(datetime.strptime('2024-01-01', '%Y-%m-%d').timestamp())
```

## 坑 7：`realpath` 不存在

**GNU realpath**：`realpath /some/path` → 绝对路径
**macOS realpath**：不存在（默认没装 coreutils）

**修法**：
```bash
# GNU 写法（Linux + 装了 coreutils 的 Mac）
realpath file.txt

# macOS 通用写法
cd "$(dirname file.txt)" && pwd && cd - > /dev/null
# 或
python3 -c "import os; print(os.path.abspath('file.txt'))"
```

## 跨平台备份脚本模板

**优先用 Python 而不是 bash** 写复杂的备份逻辑。bash 只做"调度"（调用 tar / gpg / rclone），核心判断（哪些文件、哪些 exclude、要不要 checkpoint）用 Python：

```python
# 优势：
# 1. 跨 macOS + Linux 行为一致
# 2. SQLite 库自带, 不需要 CLI 调用
# 3. file size / mtime 跨平台 API 一致
# 4. 测试容易, 不需要 bash 解释器
```

模板见 `scripts/hermes_backup.py`（如果写了的话）或参考 `tools/` 下的 hermes 内部工具。
