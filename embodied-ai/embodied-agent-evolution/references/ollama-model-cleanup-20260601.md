# Ollama 模型清理记录（2026-06-01）

## 事件背景

M4 Mac mini 24GB 突然变卡，内存从 22GB used / 123MB free → 清理后 5GB used / 18GB free。

## 根本原因

**不是 Docker Linux VM**（实际只占 ~600MB），而是 **Ollama qwen3-vl:latest (6.1GB) 模型在内存中运行**，加上模型加载后的显存占用，实际压了 ~15GB。

内存消耗链条：
```
macOS + 系统服务          ~8GB (wired)
Ollama qwen3-vl:latest    ~15GB (模型 + VRAM)
Docker (Linux VM)         ~600MB (实际)
────────────────────────────────────
总计                      ~24GB → 爆了
```

## 清理操作

```bash
# 彻底停止 Ollama（防止自动重启）
pkill -9 -f 'Ollama'
pkill -9 -f 'ollama'

# 删除不常用的本地模型
ollama rm nomic-embed-text:latest   # 274MB
ollama rm ahmadwaqar/smolvlm2-agentic-gui:latest  # 2.0GB
```

## 清理后状态

剩余3个模型，约9GB：
```
qwen3-vl:latest    6.1 GB  (31分钟前)  ← ⚠️ 还在，如果要完全清空就删这个
qwen2.5:1.5b        986 MB  (23小时前)
qwen3-vl:2b         1.9 GB  (41小时前)
```

## 关键教训

1. **Ollama 模型不是\"空闲\"的** — qwen3-vl:latest 6.1GB 模型即使不推理也占用大量内存（M4统一内存）
2. **M4 24GB 配置不建议跑 >3GB 的VLM** — qwen3-vl:2b (1.9GB) 是更安全的上限
3. **Docker Linux VM 占用比想象的小** — 只有 ~600MB，不是之前以为的 9GB
4. **Ollama 有自动重启机制** — 有个 shell 脚本会拉起它，单纯 pkill 可能不够

## Hermes 中的实际使用情况

当前 config.yaml 里 `vision.provider: auto`，实际走的是 Apple Vision OCR + cua-driver，**这三个模型 Hermes 目前都没有在用**。

如果完全不需本地 VLM，可以安全删除：
```bash
ollama rm qwen3-vl:latest
ollama rm qwen2.5:1.5b
ollama rm qwen3-vl:2b
```

## 验证命令

```bash
# 查看内存状态
top -l 1 | grep PhysMem

# 查看 Ollama 模型
ollama list

# 确认无 Ollama 进程
ps aux | grep -i ollama | grep -v grep
```