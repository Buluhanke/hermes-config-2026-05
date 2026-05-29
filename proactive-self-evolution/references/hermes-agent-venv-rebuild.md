# hermes-agent venv 重建与维护（2026-05-29）

## 何时需要重建venv

- `~/.hermes/hermes-agent/venv/bin/hermes` 不存在
- Python版本升级后venv不兼容
- paddlepaddle等依赖安装失败

## 标准重建流程

```bash
cd /Users/aimac/.hermes/hermes-agent

# 1. 删除损坏的venv
rm -rf venv

# 2. 创建新venv（用系统Python3.11）
python3.11 -m venv venv

# 3. 从源码安装（注意是 -e . 不是 pip install hermesai）
./venv/bin/pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple

# 4. 验证
./venv/bin/hermes skills list
```

## 关键要点

1. **包名不存在**：`pip install hermesai` 会失败，必须用 `-e .` 从源码装
2. **Python版本**：用 `python3.11`（3.14不兼容paddlepaddle）
3. **清华镜像**：显著加速，URL=`https://pypi.tuna.tsinghua.edu.cn/simple`
4. **重建很快**：hermes-agent核心包<1分钟，全量<5分钟

## 已知兼容性问题

| Python版本 | 状态 |
|------------|------|
| 3.11 | ✅ 推荐 |
| 3.12 | 待确认 |
| 3.14 | ❌ paddlepaddle无预编译wheel，Mac ARM64不兼容 |

## 验证skills列表正常

```bash
./venv/bin/hermes skills list
# 应显示：X hub-installed, Y builtin, Z local — N enabled, 0 disabled
```

## venv内Python路径速查

- hermes-agent核心：`/Users/aimac/.hermes/hermes-agent/venv/bin/python`
- Homebrew Python（含Vision）：`/opt/homebrew/bin/python3`
- 系统Python（无pyobjc）：`/usr/bin/python3`

**Apple Vision OCR必须用Homebrew Python**，hermes-agent venv和系统Python都没有pyobjc-framework-Vision。