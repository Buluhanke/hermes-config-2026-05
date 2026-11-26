# 废弃架构说明（仅作历史参考，禁止重建）

`model_health_daemon.py`（3 秒轮询）、`model_router.py`（自动选最佳模型）、`start_model_health.sh`（启动守护）与状态文件 `model_health_cache.json` 属于旧版「自动切换」架构。

用户铁律已否决该架构：**给什么模型就用什么模型，模型失效手动切换，不自动兜底、不建 fallback 链、不启动守护进程**。本文件仅为历史记录，禁止据此恢复任何自动轮替组件。

仍有效的诊断经验：

1. reason 模型探针 `max_tokens >= 200`，`content` / `reasoning_content` 任一非空即视为可用；HTTP 200 解析异常先打印原始响应。
2. `.env` 中 `sk-...87b6` 之类为遮罩值（`len < 30` 或含 `...`）——只打印长度和状态，绝不打印 key 本身。
3. 免费 slug 上架/下架频繁，判定可用性的唯一标准是实时 GET `/v1/models` 拉 `:free` slug 后逐个 POST 验证。
4. 网关健康端口是 `8642`（`curl -s --max-time 5 http://127.0.0.1:8642/health`），不是 `18789`。
