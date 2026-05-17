---
name: fine-tuning-with-trl
description: TRL训练全家桶 — SFT/DPO/PPO/GRPO/LoRA/QLoRA微调实战。触发：模型微调、RLHF训练、LoRA配置、量化微调、本地部署推理。
triggers:
  - 模型微调
  - 训练模型
  - SFT
  - DPO训练
  - PPO训练
  - GRPO训练
  - LoRA
  - QLoRA
  - 量化
  - 本地部署
  - TRL训练
  - RLHF
  - 推理优化
---

# TRL Fine-Tuning 全栈指南

## 概述

TRL（Transformer Reinforcement Learning）是 Hugging Face 提供的 RLHF 训练库，完整覆盖从 SFT 到 RLHF 的全流程。本技能涵盖：

| 模块 | 工具 | 场景 |
|------|------|------|
| SFT | `SFTTrainer` | 监督微调，基础能力对齐 |
| DPO | `DPOTrainer` | 直接偏好优化，无需 Reward Model |
| PPO | `PPOTrainer` | 完整 RLHF，需要 Reward + Critic |
| GRPO | `GRPOTrainer` | DeepSeek式分组相对偏好优化 |
| LoRA/QLoRA | `peft` + `bitsandbytes` | 高效参数微调 + 量化结合 |
| 推理 | `vLLM` / `llama.cpp` | 本地高速推理 |

---

## 1. 环境安装

```bash
pip install trl[peft] bitsandbytes transformers datasets accelerate vllm
# 可选：flash-attn（需从源码编译，显著加速）
pip install flash-attn --no-build-isolation
```

验证安装：
```python
import trl
print(trl.__version__)  # 应 >= 0.14.0
```

---

## 2. 训练数据准备格式

### 2.1 SFT 数据格式（ChatML / OpenAI 格式）

```python
# 格式1：对话数组（推荐，TRL SFTTrainer 原生支持）
dataset = [
    {
        "messages": [
            {"role": "system", "content": "你是一个有帮助的助手。"},
            {"role": "user", "content": "解释什么是大语言模型。"},
            {"role": "assistant", "content": "大语言模型（LLM）是..."}
        ]
    },
    {
        "messages": [
            {"role": "user", "content": "写一首关于春天的诗。"},
            {"role": "assistant", "content": "春风拂面百花开，..."}
        ]
    }
]

# 格式2：单轮 prompt-response
dataset = [
    {"prompt": "解释量子计算：", "response": "量子计算是一种利用量子力学原理..."},
    {"prompt": "如何学习Python？", "response": "学习Python可以从..."}
]
```

### 2.2 DPO 数据格式（偏好对）

```python
# 必须字段：chosen（偏好）/ rejected（拒绝）
dataset = [
    {
        "prompt": "解释什么是机器学习：",
        "chosen": "机器学习是人工智能的一个分支，它使系统能够从数据中自动学习和改进。",
        "rejected": "机器学习就是AI。"
    },
    {
        "prompt": "写一个Python快速排序：",
        "chosen": "def quicksort(arr):\n    if len(arr) <= 1: return arr\n    pivot = arr[len(arr)//2]\n    left = [x for x in arr if x < pivot]\n    mid = [x for x in arr if x == pivot]\n    right = [x for x in arr if x > pivot]\n    return quicksort(left) + mid + quicksort(right)",
        "rejected": "用sort()就行。"
    }
]
```

### 2.3 PPO/GRPO 数据格式

```python
# PPO 需要 query（问题）和 reward（奖励信号）
dataset = [
    {"query": "1+1等于几？", "reward": 1.0},   # 正确答案 reward 高
    {"query": "2+2等于几？", "reward": 1.0},
    {"query": "100-1等于几？", "reward": 1.0},
]

# GRPO 格式：同一问题生成多个答案，用相对偏好
dataset = [
    {
        "prompt": "解释量子纠缠：",
        "responses": [
            "量子纠缠是...",
            "两个粒子...",
            "量子纠缠是一种量子力学现象..."
        ]
    }
]
```

### 2.4 数据加载与预处理

```python
from datasets import load_dataset, Dataset

# 从本地 JSONL 加载
dataset = load_dataset("json", data_files="train.jsonl", split="train")

# 过滤无效样本
dataset = dataset.filter(
    lambda x: x["prompt"] and x["response"] and len(x["response"]) > 10
)

# 截断超长序列（根据模型上下文长度）
MAX_LENGTH = 2048
dataset = dataset.map(
    lambda x: {
        "prompt": x["prompt"][:MAX_LENGTH],
        "response": x["response"][:MAX_LENGTH]
    }
)

print(f"数据集大小: {len(dataset)}")
print(dataset[0])
```

### 2.5 ChatML 格式化函数

```python
def format_for_sft(example, system_prompt="你是一个有帮助的助手。"):
    """
    将 {prompt, response} 转为 ChatML 格式
    """
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": example["prompt"]})
    messages.append({"role": "assistant", "content": example["response"]})

    # 手工拼接 ChatML 格式（不需要 tokenizer.apply_chat_template）
    text = "<|im_start|>system\n" + messages[0]["content"] + "<|im_end|>\n"
    text += "<|im_start|>user\n" + messages[1]["content"] + "<|im_end|>\n"
    text += "<|im_start|>assistant\n" + messages[2]["content"] + "<|im_end|>\n"
    return {"text": text}

formatted = dataset.map(format_for_sft)
```

---

## 3. SFT 监督微调

### 3.1 基础 SFT

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from trl import SFTTrainer
from datasets import load_dataset

MODEL_NAME = "meta-llama/Llama-3.2-1B"  # 或本地路径
dataset = load_dataset("json", data_files="train.jsonl", split="train")

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    device_map="auto",
    torch_dtype="auto",
)
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
tokenizer.pad_token = tokenizer.eos_token

training_args = TrainingArguments(
    output_dir="./sft_output",
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,     # 有效 batch = 4*4=16
    learning_rate=2e-4,
    num_train_epochs=3,
    logging_steps=10,
    save_steps=500,
    save_total_limit=2,
    report_to="none",
    fp16=True,                         # A100/H100 用 bf16=True
    warmup_ratio=0.03,
    lr_scheduler_type="cosine",
    optim="adamw_torch",
)

trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    tokenizer=tokenizer,
    max_seq_length=2048,
    dataset_text_field="text",         # 或 "messages"
)

trainer.train()
trainer.save_model("./sft_final")
```

### 3.2 SFT + LoRA（推荐配置）

```python
from peft import LoraConfig, get_peft_model

lora_config = LoraConfig(
    r=16,                              # rank，越大越强但越慢
    lora_alpha=32,                     # 缩放因子，通常 alpha=2*r
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)

model = AutoModelForCausalLM.from_pretrained(...)
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
# 输出: "trainable params: 4M || all params: 1.2B || 0.33%"

trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    tokenizer=tokenizer,
    max_seq_length=2048,
)
trainer.train()
```

---

## 4. DPO 直接偏好优化

```python
from trl import DPOTrainer
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

dpo_config = {
    "output_dir": "./dpo_output",
    "beta": 0.1,                      # KL散度系数，0.1~0.3 常用
    "per_device_train_batch_size": 2,
    "gradient_accumulation_steps": 8,
    "learning_rate": 1e-5,            # DPO 学习率通常比 SFT 低 10x
    "num_train_epochs": 3,
    "fp16": True,
}

dpo_trainer = DPOTrainer(
    model=model,
    ref_model=None,                   # 设为 None 则用 4-bit 量化 ref
    args=TrainingArguments(**dpo_config),
    train_dataset=dataset,            # 必须包含 prompt/chosen/rejected
    tokenizer=tokenizer,
)
dpo_trainer.train()
```

---

## 5. PPO 完整 RLHF

```python
from trl import PPOConfig, PPOTrainer
from trl.models import AutoModelForCausalLMWithValueHead

ppo_config = PPOConfig(
    model_name=MODEL_NAME,
    learning_rate=1e-5,
    mini_batch_size=4,
    batch_size=16,
    gradient_accumulation_steps=4,
    early_stopping=True,
)

# 模型需包装 ValueHead（用于估计 advantage）
model = AutoModelForCausalLMWithValueHead.from_pretrained(MODEL_NAME)

ppotrainer = PPOTrainer(
    config=ppo_config,
    model=model,
    ref_model=None,
    tokenizer=tokenizer,
)

# 生成 + 评分训练循环
for batch in dataloader:
    query_tensors = [tokenizer.encode(q, return_tensors="pt") for q in batch["query"]]
    response_tensors = ppotrainer.generate(query_tensors)
    rewards = [torch.tensor(r) for r in compute_rewards(batch)]
    stats = ppotrainer.step(query_tensors, response_tensors, rewards)
```

---

## 6. GRPO 分组相对偏好优化（DeepSeek 风格）

```python
from trl import GRPOTrainer, GRPOConfig

grpo_config = GRPOConfig(
    output_dir="./grpo_output",
    learning_rate=1e-5,
    num_generations=8,                # 每条 prompt 生成 8 个 response
    per_device_train_batch_size=1,
    gradient_accumulation_steps=8,
)

# dataset 需包含 prompt 和 responses 字段
trainer = GRPOTrainer(
    model=MODEL_NAME,
    args=grpo_config,
    train_dataset=dataset,
    reward_function=your_reward_fn,    # 自定义 reward 函数
)
trainer.train()
```

---

## 7. LoRA/QLoRA 配置详解

### 7.1 LoRA 核心参数

```python
from peft import LoraConfig, TaskType

LoraConfig(
    r=16,                              # ★ rank（核心参数）
    lora_alpha=32,                     # ★ 缩放系数，默认 alpha=2*r
    target_modules=[                   # ★ 目标模块（必须与模型实际层名匹配）
        "q_proj", "v_proj",           # 注意力
        "k_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",  # FFN（全量 LoRA）
    ],
    modules_to_save=["lm_head", "embed_tokens"],  # 不压缩的层
    lora_dropout=0.05,
    bias="none",                       # "none" | "lora_only" | "all"
    task_type=TaskType.CAUSAL_LM,
)

# rank 选择指南
# r=4~8:   轻量微调，内存占用小，适合小数据集
# r=16:    平衡配置（推荐起步）
# r=32~64: 强任务，大数据集，效果更好但显存需求增加
```

### 7.2 QLoRA 完整配置（4-bit 量化 + LoRA）

```python
import bitsandbytes as bnb
from transformers import BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

# ★★★ QLoRA 量化配置 ★★★
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,                # 4-bit 量化加载
    bnb_4bit_quant_type="nf4",       # "nf4"（Normalized FP4，推荐）
    bnb_4bit_compute_dtype="bfloat16", # 计算精度
    bnb_4bit_use_double_quant=True,   # 双重量化，进一步省显存 ~0.4 bit/param
)

# 加载量化模型
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    quantization_config=quantization_config,
    device_map="auto",
    trust_remote_code=True,
)

# ★ 关键：量化后必须调用此函数
model = prepare_model_for_kbit_training(model)

# ★ LoRA 配置
lora_config = LoraConfig(
    r=64,                             # QLoRA 建议用更大 rank
    lora_alpha=128,
    target_modules=[                   # 必须精确匹配模型层
        "q_proj", "v_proj", "k_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ],
    lora_dropout=0.05,
    bias="none",
    task_type=TaskType.CAUSAL_LM,
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
```

### 7.3 8-bit 量化（介于全精度和 4-bit 之间）

```python
quantization_config = BitsAndBytesConfig(
    load_in_8bit=True,
    8bit_quant_type="llm_int8",       # 或 "fp8"（H100/H200）
    8bit_compute_dtype="bfloat16",
)

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    quantization_config=quantization_config,
    device_map="auto",
)
model = prepare_model_for_kbit_training(model)
```

### 7.4 不同量化级别显存对比（近似值）

| 配置 | 7B 模型 | 13B 模型 | 70B 模型 |
|------|---------|----------|----------|
| 全精度 FP16 | ~14GB | ~26GB | ~140GB |
| 8-bit 量化 | ~7GB | ~14GB | ~70GB |
| 4-bit QLoRA | ~5GB | ~10GB | ~40GB |
| 4-bit QLoRA + LoRA(r=64) | ~6GB | ~12GB | ~48GB |

---

## 8. 本地模型微调完整流程

### 8.1 Step by Step

```bash
# Step 1: 创建项目目录
mkdir -p ~/trl_finetune/{data,output,scripts}
cd ~/trl_finetune

# Step 2: 准备数据（JSONL 格式）
# 保存为 data/train.jsonl
```

```python
# Step 3: 数据预处理脚本 prepare_data.py
from datasets import load_dataset

ds = load_dataset("json", data_files="data/train.jsonl", split="train")
ds = ds.filter(lambda x: x["response"] and len(x["response"]) > 20)

def add_system(example):
    example["text"] = (
        "<|im_start|>system\n你是一个有帮助的助手。<|im_end|>\n"
        f"<|im_start|>user\n{example['prompt']}<|im_end|>\n"
        f"<|im_start|>assistant\n{example['response']}<|im_end|>\n"
    )
    return example

ds = ds.map(add_system)
ds.to_json("data/train_formatted.jsonl", orient="records", lines=True)
print(f"处理完成: {len(ds)} 条样本")
```

```bash
# Step 4: 运行训练脚本
python scripts/train_sft.py 2>&1 | tee logs/train.log
```

### 8.2 完整训练脚本（SFT + QLoRA）

```python
#!/usr/bin/env python3
# scripts/train_sft_qlora.py

import os
import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM, AutoTokenizer,
    BitsAndBytesConfig, TrainingArguments
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer

# ===== 配置 =====
MODEL_NAME = os.environ.get("MODEL", "meta-llama/Llama-3.2-1B")
DATA_PATH = "data/train_formatted.jsonl"
OUTPUT_DIR = "output/llama-sft-qlora"

# ===== 量化 =====
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype="bfloat16",
    bnb_4bit_use_double_quant=True,
)

# ===== 加载模型 =====
print(f"加载模型: {MODEL_NAME}")
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True,
)
model = prepare_model_for_kbit_training(model)

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
tokenizer.pad_token = tokenizer.eos_token

# ===== LoRA =====
lora_cfg = LoraConfig(
    r=64, lora_alpha=128,
    target_modules=["q_proj","v_proj","k_proj","o_proj",
                    "gate_proj","up_proj","down_proj"],
    lora_dropout=0.05, bias="none", task_type="CAUSAL_LM",
)
model = get_peft_model(model, lora_cfg)
model.print_trainable_parameters()

# ===== 数据 =====
dataset = load_dataset("json", data_files=DATA_PATH, split="train")
dataset = dataset.filter(lambda x: x["text"] and len(x["text"]) > 50)
print(f"训练样本: {len(dataset)}")

# ===== 训练 =====
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    num_train_epochs=3,
    logging_steps=10,
    save_steps=500,
    save_total_limit=2,
    bf16=True,                        # A100/H100
    fp16=False,
    optim="paged_adamw_32bit",        # ★ 配合量化使用，防止显存峰值
    warmup_ratio=0.03,
    lr_scheduler_type="cosine",
    report_to="none",
)

trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    tokenizer=tokenizer,
    max_seq_length=2048,
    dataset_text_field="text",
)
trainer.train()
trainer.save_model(f"{OUTPUT_DIR}/final")
print("训练完成！")
```

### 8.3 常见问题排查

| 问题 | 原因 | 解决 |
|------|------|------|
| OOM（显存溢出） | batch过大 | 减小 `per_device_train_batch_size`，增大 `gradient_accumulation_steps` |
| loss=NaN | 学习率过高 / 梯度爆炸 | 降低 lr 到 1e-5~2e-5，开启 `gradient_clipping` |
| 量化后效果差 | 4bit过压缩 | 改用 8bit，或 `bnb_4bit_compute_dtype="float16"` |
| 训练不收敛 | 数据质量差/格式错误 | 检查数据，filter 掉太短的样本 |
| 保存的模型无法推理 | 只保存了 LoRA adapter | 需 merge 并重新保存：`model.merge_and_unload()` |

---

## 9. 量化配置详解

### 9.1 bitsandbytes 量化类型

```python
from transformers import BitsAndBytesConfig

# NF4（Normalized FP4）- 量化权重分布均匀的数据（LLM 权重）
bnb_nf4 = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype="bfloat16",
)

# Int8 - 兼容性更好，速度略慢于 NF4
bnb_int8 = BitsAndBytesConfig(
    load_in_8bit=True,
)

# FP8（仅 H100/H200/AMD MI300）- 最新格式，速度最快
bnb_fp8 = BitsAndBytesConfig(
    load_in_8bit=True,
    llm_int8_threshold=6.0,
    llm_int8_has_fp16_weight=False,
)
```

### 9.2 GGUF 格式（llama.cpp）

```bash
# 将 HF 模型转换为 GGUF
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
python convert.py /path/to/hf/model --outfile model.gguf --outtype q4_K_M

# 可选量化类型：q4_0, q4_1, q5_0, q5_1, q8_0, f16, f32
# q4_K_M: 4-bit，中等质量，推荐
# q5_K_S: 5-bit，小体积，质量好
# q8_0:   8-bit，几乎无损，但体积大
```

### 9.3 AutoGPTQ 量化

```bash
pip install auto-gptq
```

```python
from auto_gptq import AutoGPTQForCausalLM
model = AutoGPTQForCausalLM.from_quantized(
    'model_path', model_basename='gptq_model-4bit',
    device='cuda:0', use_triton=False
)
```

---

## 10. 推理优化

### 10.1 vLLM（生产级高速推理）

```bash
pip install vllm
```

```python
from vllm import LLM, SamplingParams

# 加载模型（自动用 PagedAttention 优化）
llm = LLM(
    model="./sft_final",
    tensor_parallel_size=1,            # 多卡并行
    gpu_memory_utilization=0.85,       # 显存占用比例
    max_model_len=4096,                # 上下文长度
    dtype="bfloat16",
    trust_remote_code=True,
)

sampling_params = SamplingParams(
    temperature=0.7,
    top_p=0.95,
    max_tokens=512,
)

# 批量推理（高效）
outputs = llm.generate(
    ["解释量子纠缠：", "什么是机器学习？"],
    sampling_params
)

for output in outputs:
    print(output.outputs[0].text)
```

### 10.2 llama.cpp 量化推理（CPU/Mac 友好）

```bash
# Mac M1/M2/M3
brew install llama.cpp

# 或从源码编译
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp && mkdir build && cd build && cmake .. && make -j4
```

```bash
# 量化并推理
./quantize ../models/llama-2-7b/ggml-model-f16.gguf ../models/llama-2-7b/llama-2-7b-q4_K_M.gguf q4_K_M
./main -m ../models/llama-2-7b/llama-2-7b-q4_K_M.gguf -n 512 -t 8 --temp 0.7 -p '解释量子计算：'
```

### 10.3 多 LoRA 动态加载

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM

base_model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.2-1B",
    device_map="auto",
    torch_dtype="bfloat16",
)

# 加载多个 LoRA adapter
lora_paths = {
    "math": "./output/math_lora",
    "code": "./output/code_lora",
    "chat": "./output/chat_lora",
}

# 动态切换
def load_lora(lora_name):
    model = PeftModel.from_pretrained(base_model, lora_paths[lora_name])
    return model

math_model = load_lora("math")
```

### 10.4 推理加速技巧

| 技巧 | 效果 | 说明 |
|------|------|------|
| Flash Attention-2 | 2~4x 加速 | 需 A100/H100/MI300 |
| PagedAttention (vLLM) | 2~10x 吞吐 | 自动 KV cache 分页管理 |
| Batch 推理 | 5~20x 吞吐 | 尽量批量输入，不要单条 |
| 4-bit 量化推理 | 2x 显存降低 | 速度稍慢但省显存 |
| Speculative Decoding | 2~3x 加速 | 用小模型预测，大模型验证 |

---

## 11. 模型 merge 与导出

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM

base = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.2-1B")
model = PeftModel.from_pretrained(base, "output/lora_adapter")

# ★ 合并 LoRA 权重到 base model
merged_model = model.merge_and_unload()
merged_model.save_pretrained("output/merged_model")
print("合并完成")
```

---

## 12. 常见命令速查

```bash
# 查看模型层名（确定 LoRA target_modules）
python -c "
from transformers import AutoModel
m = AutoModel.from_pretrained('model_path', trust_remote_code=True)
for name, _ in m.named_modules():
    print(name)
" | grep -E "(q_proj|v_proj|k_proj|gate_proj)"

# 估算 LoRA 参数量
python -c "
r, l, alpha = 16, 4096, 32
params = 4 * l * r * 2
print(f'LoRA params: {params:,} (~{params/1e6:.1f}M)')
"
```

---

## 参考资源

- TRL 官方文档: https://huggingface.co/docs/trl
- PEFT 文档: https://huggingface.co/docs/peft
- bitsandbytes: https://github.com/TimDettmers/bitsandbytes
- vLLM: https://docs.vllm.ai/
- llama.cpp: https://github.com/ggerganov/llama.cpp
