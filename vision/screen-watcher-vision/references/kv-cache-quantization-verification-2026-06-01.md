# KV Cache 量化验证记录（2026-06-01）

## 验证结论

`OLLAMA_KV_CACHE_TYPE=q8_0` 已在系统环境中**生效**（非默认值 f16），qwen3-vl:2b 运行时内存 2.7GB（Context 4096）。无需额外操作。

## 验证步骤

```bash
# 1. 检查环境变量
echo "${OLLAMA_KV_CACHE_TYPE:-not set}"
# → q8_0

# 2. 检查 Ollama runner 进程（看 args 中有无 KV cache 参数）
ps aux | grep ollama | grep runner

# 3. 检查模型加载后的内存占用
ollama ps
# NAME           SIZE      PROCESSOR    CONTEXT    UNTIL
# qwen3-vl:2b    2.7 GB    100% GPU     4096       4 minutes from now
```

## 背景

Ollama 默认使用 `f16` KV cache（全精度）。对小模型+大上下文场景影响显著（qwen3-vl:2b 全量 256K 上下文导致 20GB 内存占用）。num_ctx 显式设置为 4096 后，q8_0 量化进一步减少 KV cache 内存。

## 配置方式

通过环境变量启用（launchctl 或 shell）：

```bash
export OLLAMA_KV_CACHE_TYPE=q8_0   # 或 q4_0 更激进
# Ollama 重启后生效
```

## 参考

- Mitja Martini: https://mitjamartini.com/posts/ollama-kv-cache-quantization/
- Ollama FAQ: How can I set the quantization type for the K/V cache?
- lmdeploy K/V cache quantization accuracy test results
