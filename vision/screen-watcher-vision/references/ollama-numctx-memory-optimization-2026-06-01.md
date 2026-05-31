# Ollama num_ctx 内存优化 — qwen3-vl:2b 20GB → 2.7GB

## 发现背景

2026-06-01 01:26 cron idle_learning 巡检系统时发现：

指标                     | 值                  | 正常范围
------------------------|---------------------|------------
系统空闲内存             | 218 MB              | >4 GB
Ollama runner RSS       | 17.4 GB             | <8 GB
Ollama 峰值物理内存     | **23.2 GB**         | <15 GB
swapins                 | 587K                | <10K
swapouts                | 978K                | <10K
Load Average            | 4.42                | <2.0

## 根因定位

`ollama ps` 显示：
```
NAME           ID              SIZE     PROCESSOR          CONTEXT    UNTIL
qwen3-vl:2b    0635d9d857d4    20 GB    15%/85% CPU/GPU    262144     4 min
```

- **CONTEXT=262144**: 使用 Qwen3-VL 全量 256K 上下文
- **SIZE=20GB**: 256K KV cache 撑爆内存（模型权重仅 1.76GB）
- **15% CPU / 85% GPU**: GPU 不够，部分 KV cache 溢出到 CPU（显存不足）
- **原因**: screen_trigger_handler 的 Ollama API 调用只设了 `temperature: 0.0`，未指定 `num_ctx`，Ollama 默认使用模型的全量上下文

## 修复

screen_trigger_handler.py 两处 options 添加 num_ctx：

```python
# get_scene_type() — 场景分类（仅需单字输出）
"options": {"temperature": 0.0, "num_ctx": 1024}

# ask_screen() — 屏幕内容分析（需适当上下文）
"options": {"temperature": 0.0, "num_ctx": 4096}
```

**修复后效果**：

| 指标 | 修复前 | 修复后 | 改善 |
|------|--------|--------|------|
| Ollama 运行时内存 | 20 GB | 2.7 GB | -86% |
| Context | 262144 | 4096 | -98% |
| 系统空闲内存 | 218 MB | 13.4 GB | +62x |
| 场景分类耗时 | 35-47s | 9-12s | -74% |
| GPU 利用率 | 85% | 100% | +18% |
| swap | 持续增长 | 停止 | — |

## 诊断命令

```bash
# 检查当前加载模型的 context 大小和内存
ollama ps

# 检查 ollama runner 进程内存
ps aux | grep "ollama runner" | awk '{print "PID:", $2, "MEM:", $6/1024/1024 "GB", "CPU:", $3 "%"}'

# 检查系统内存压力
memory_pressure | head -3
vm_stat | head -15
# 计算空闲内存：pages_free × page_size / 1024^3
python3 -c "print(f'Free: {856976 * 16384 / 1024**3:.1f} GB')"
```

## 卸载旧模型实例

```bash
ollama stop qwen3-vl:2b   # 卸载当前加载的模型
pkill -f screen_watcher   # 停 watcher
# 等待 → 自动重启（cron 拉起）或手动启动
python3 ~/.hermes/scripts/screen_watcher.py  # 后台启动
```

## 扩展：KV Cache Quantization

Ollama 0.24.0+ 内置 KV cache 量化（q8_0 / q4_0），可在 Modelfile 或 API options 中启用，进一步减少 50-75% 上下文内存。本次修复仅靠缩小 num_ctx 已解决核心问题，KV cache 量化可作为下一步优化。

## 影响

- screen_watcher handler 响应时间从 70-84s 降至 20-30s
- 防止系统在长时间运行时 OOM
- 降低了 4 个 CPU 核心的负载（从 Load Avg 4.42 降至 ~1.0）
- 消除了 swap 压力
