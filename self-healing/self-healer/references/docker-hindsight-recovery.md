# Hindsight Docker 恢复流程（已废弃）

> ⚠️ **2026-06-02 永久记录**：Hindsight Docker 镜像无法恢复，此文档仅作历史参考。

## 当前状态

| 项目 | 状态 |
|------|------|
| ghcr.io/nousresearch/hindsight | ❌ Access Denied |
| docker.io/nousresearch/hindsight | ❌ i/o timeout |
| 本地 .tar 备份 | 无 |

Hindsight 积累的所有叙事化经验（观察记录、银行信息等）**永久丢失**。

## 网络诊断（历史记录）

```bash
# ghcr.io — Access Denied
curl -s --max-time 10 https://ghcr.io/v2/ -o /dev/null && echo "ok" || echo "denied"

# docker.io — 超时
curl -s --max-time 10 https://registry-1.docker.io/v2/ -o /dev/null && echo "ok" || echo "timeout"
```

## 当前记忆系统（替代方案）

三层架构完全不依赖 Docker，正常运转：

| 组件 | 状态 | 数据位置 |
|------|------|---------|
| MEMORY.md | ✅ | ~/.hermes/memories/MEMORY.md |
| fact_store (holographic) | ✅ 9条facts | ~/.hermes/memory_store.db |
| session_search (FTS5) | ✅ 9.8万条 | ~/.hermes/state.db |

## 如果未来要重建 Hindsight

1. 需要可访问 ghcr.io 的网络环境
2. 或者找到 nousresearch/hindsight 的其他镜像源
3. 当前三层架构已足够，不需要重建 Hindsight

## 关联文档

- `references/mac-mini-ram-management.md` — Colima 内存管理
- `references/api-key-centralization.md` — API Key 状态总表
