# LLM 可观测性技术备注

## 为什么自己写而不是用现成工具

**Arize Phoenix**：需要启动 Web UI 服务（Phoenix app），实质是 OpenTelemetry + Web 可视化，数据默认上报到 Arize Cloud。自托管需要 Docker，不符合 Hermes 纯本地约束。

**Langfuse**：自托管需要 Docker + Postgres，架构重（前端+后端+DB），占用资源多。

**OpenLit**：纯 Python，但设计目标是收集+转发（OTLP exporter），还是需要后端接收服务。

**结论**：对于"纯本地、不过外网、查询方便"的场景，SQLite 是最轻量的方案。70 行 Python 覆盖核心需求（token 计数 + 延迟 + 错误记录 + 成本估算），无需任何外部依赖。

## canonical_usage vs raw usage

Hermes 的 `CanonicalUsage` dataclass（`usage_pricing.py`）已经做了跨 Provider 的 usage 标准化：
- `input_tokens`：纯输入 token
- `output_tokens`：纯输出 token  
- `cache_read_tokens`：缓存读取 token
- `cache_write_tokens`：缓存写入 token
- `reasoning_tokens`：推理 token

这个标准化是 tracing 写入的基础——不需要关心各个 Provider 返回的 raw usage 字段差异。

## Gateway 重启后 tracing 才生效

因为 `llm_trace.py` 是作为新模块被 `conversation_loop.py` import 的，所以：
- Gateway 重启前：旧代码未加载新模块，traces 不写入
- Gateway 重启后：新代码生效，每次 API 调用都写入

tracing 数据积累需要时间（至少一次完整会话），不能立刻看到结果。
