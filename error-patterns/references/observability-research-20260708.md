# 2026-07-08 观测性工具调研记录

## 结论：所有主流 LLM 可观测性工具都不能纯 pip 落地

| 工具 | 落地方式 | 对 Hermes 可用性 |
|------|---------|----------------|
| Agenta | pip 可装 SDK | 云端依赖，自托管需 Docker |
| Langfuse | Docker Compose | ❌ Docker 禁止 |
| Arize Phoenix | pip 可装 | UI 需跑服务，traces 可本地存 |
| OpenLIT | pip 可装 | Controller 需 k8s/Docker |
| Braintrust | 云服务 | ❌ |
| Helicone | 云/proxy | ❌ |

## 唯一可用：Phoenix (arize-phoenix)

- **可 pip 安装**：`pip3 install arize-phoenix`
- **价值**：OpenTelemetry instrumentation + 评估器设计思路
- **局限**：本地 UI 仍需启动 web 服务，数据最终走 OTLP 导出
- **对 Hermes 借鉴**：用 `opentelemetry-sdk` 的 `SpanExporter` 接口做本地 SQLite writer

## 今日发现

- `browser_console` 对中文页面有 UnicodeEncodeError，换 `browser_console` 的 `expression` 参数读 `document.body.innerText`
- `pip3` vs `python3 -m pip`：两者等价，但某些环境（launchd/独立 venv）只有后者可用
- arize-phoenix 和 agenta 的 `opentelemetry-instrumentation` 版本冲突（agenta 锁 `<0.62`，arize-phoenix 装 `0.64b0`）
