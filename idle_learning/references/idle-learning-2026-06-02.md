# 2026-06-02 空闲学习产出

## 记忆系统评估

**Hindsight 数据丢失**：
- Docker 删除后 Hindsight 不可用（ghcr.io 访问被拒）
- ChromaDB 本地测试通过（零外部依赖）
- mem0ai 依赖 OpenAI + qdrant，不够轻量
- **当前方案**：fact_store + session_search + MEMORY.md 三层架构

**内存优化**：
- Colima 停止，释放 6GB 内存
- 当前内存：15G used / 8.5G free

**下一步学习方向**：
- ChromaDB embedding 方案（sentence-transformers 或 API-based）
- fact_store 与 ChromaDB 整合可能性
