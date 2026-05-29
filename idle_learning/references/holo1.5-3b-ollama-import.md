# Holo1.5-3B GGUF Import to Ollama — 实测记录（2026-05-30）

## 结论
Holo1.5-3B 在 Ollama 官方库中**不存在**，无法直接 `ollama pull holo1.5-3b`。

必须走 GGUF 手动导入路径。

## 实测结果
```
$ ollama pull holo1.5-3b
→ pull model manifest: file does not exist (status code: 500)
```

## 正确导入路径

### Step 1：检查 HuggingFace 是否有 GGUF 格式
访问：`https://huggingface.co/Hcompany/Holo1.5-3B`
搜索是否有 `.gguf` 文件（目前未确认是否有 GGUF 发布）

### Step 2：如果有 GGUF
```bash
# 下载 GGUF 文件（用 hf-mirror.com 绕过 huggingface.co 阻塞）
curl -L "https://hf-mirror.com/Hcompany/Holo1.5-3B/resolve/main/model.gguf" -o holo1.5-3b.gguf

# 创建 Modelfile
cat > Modelfile << 'EOF'
FROM ./holo1.5-3b.gguf
# 设置视觉参数（如果需要）
PARAMETER mmproj ./mmproj.bin
EOF

# 导入 Ollama
ollama create holo1.5-3b -f Modelfile
```

### Step 3：如果只有 Safetensors（无 GGUF）
需要用 `llama.cpp` 转换：
```bash
# 先确认 llama.cpp 已安装
brew install llama.cpp

# 下载 safetensors from HuggingFace
git clone https://hf-mirror.com/Hcompany/Holo1.5-3B

# 转换（需要了解模型结构才能正确分离 mmproj）
```

## 参考资料
- Ollama GGUF 导入指南：`https://markaicode.com/import-gguf-models-ollama-guide/`
- HuggingFace：`https://huggingface.co/Hcompany/Holo1.5-3B`
- 模型描述：Holo1.5 adds 10%+ accuracy vs Holo1，3B/7B/72B sizes，Apache-2.0 for 7B

## 状态
- ❌ 直接 pull：失败
- 🔄 GGUF 下载：未测试（需确认 HF 是否有 gguf 文件）
- 🔄 Safetensors 转换：未测试