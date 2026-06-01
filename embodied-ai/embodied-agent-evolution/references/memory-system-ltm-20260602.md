# Hermes 长期记忆系统现状（2026-06-02 实测，最终版）

## 三层记忆架构

| 层级 | 工具 | 状态 | 说明 |
|------|------|------|------|
| 结构化记忆 | fact_store (holographic) | ✅ 在用 | SQLite+FTS5, entity resolution, trust scoring |
| 文档记忆 | MEMORY.md | ✅ 在用 | ~15KB, 系统配置+经验教训 |
| 对话记忆 | session_search | ✅ 在用 | 9.8万条消息, FTS5检索 |
| **长期记忆** | **GBrain** | **✅ 主力** | **PGLite本地，keyword搜索正常，数据完整** |

## GBrain 实测确认（2026-06-02，当前主力）

**GBrain = 正确的长期记忆方案**：
- **无需 Docker**：PGLite（本地 SQLite + 向量扩展），纯本地
- **已安装**：`~/gbrain/`，`/Users/aimac/.bun/bin/gbrain`，v0.37.0.0
- **健康分**：50/100（嵌入未生成，但不影响 keyword 搜索）
- **keyword 搜索 ✅ 正常**：`gbrain search "罗元"` 可用
- **向量搜索 ⚠️ 需 ZEROENTROPY_API_KEY**：`gbrain query` 报错 "ZeroEntropy embedding requires ZEROENTROPY_API_KEY"
- **已有数据**（2026-06-02 全部验证完整）：用户-罗元、公司/迅龙贸易（联系人/手机/邮箱）、供应商库（气泡膜/珍珠棉/纸箱/胶带）、1688询价流程、老板偏好、AI研究笔记

**GBrain 命令速查**：
```bash
~/.bun/bin/gbrain put <slug> << 'EOF'   # 存储
~/.bun/bin/gbrain get 用户-罗元         # 读取
~/.bun/bin/gbrain search "关键词"        # keyword搜索（无需API key）✅
~/.bun/bin/gbrain query "语义问题"      # 向量搜索（需ZEROENTROPY_API_KEY）⚠️
~/.bun/bin/gbrain list                  # 列出所有pages
~/.bun/bin/gbrain doctor                # 健康检查
```

**数据路径**：`~/.gbrain/brain.pglite`

## Hindsight 结论

**Docker删除后 Hindsight 数据不可恢复**：
- 镜像来源：ghcr.io/nousresearch/hindsight（访问被拒绝）
- docker.io 拉取超时（网络问题）
- 之前积累的"观察记录"、叙事化经验全部丢失

**教训**：重要数据不能只依赖 Docker 容器卷存储。

## 轻量替代方案测试（2026-06-02）

| 方案 | 结果 | 说明 |
|------|------|------|
| **GBrain** | **✅ 主力** | 数据已存在，keyword搜索正常 |
| ChromaDB | ✅ 可用 | 纯本地，hermes venv 已装（备用） |
| mem0ai | ❌ | 依赖 OpenAI API Key + qdrant |

## Colima 状态

- Colima 已停止（6GB VM 待机太浪费）
- 搜索已降级到 ddgs/anysearch，不需要 Docker
- 如需重启：`colima start --arch aarch64 --runtime docker --vm-type vz --memory 2`

## 建议

1. **GBrain 为主**：keyword 搜索已够用，向量搜索可申请 ZEROENTROPY_API_KEY
2. **ChromaDB 备用**：如需语义搜索增强，可接入
3. **不要重装 Docker/Hindsight**：资源消耗大，替代方案已够用
