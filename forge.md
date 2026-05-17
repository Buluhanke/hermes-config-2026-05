---
name: forge
description: Forge SD WebUI Fork SDXL优化与极速生成
version: 1.0.0
---

# Forge SD WebUI 分叉版指南

## When to Use
- 主要使用SDXL模型
- 需要比A1111更快的生成速度
- 对LoRA训练有需求
- 需要更好显存优化

## Core Features

**Forge是什么：**
- 基于A1111 WebUI的优化分叉
- 核心优化：SDXL速度提升、显存优化
- 由另一位开发者维护（非A1111团队）

**核心优势：**

**SDXL专项优化：**
- SDXL生成速度显著快于A1111
- 优化了SDXL的内存占用
- SDXL 1024px生成更流畅

**速度提升：**
- 通过优化底层计算提升速度
- 部分操作（特别是SDXL）明显更快
- 与A1111相同的界面，零学习成本切换

**LoRA训练：**
- 内置LoRA训练模块
- 支持SDXL LoRA训练
- 训练速度比A1111快
- 训练参数界面化，无需命令行

**显存优化：**
- 更好的显存分配策略
- 部分情况下可在6GB卡上运行SDXL
- 减少OOM崩溃

**与A1111兼容：**
- 扩展兼容性高
- 模型文件互通
- 工作流参数可迁移
- 可以直接替代A1111使用

## Quick Start
```bash
git clone https://github.com/lllyasviel/stable-diffusion-webui-forge.git
cd stable-diffusion-webui-forge
./webui.sh  # Linux
webui-user.bat  # Windows
```
1. 与A1111安装方式完全相同
2. 直接替换A1111目录使用
3. 模型放入同一目录

## Pitfalls
- **社区支持较少**：文档和教程不如A1111丰富
- **扩展兼容性**：少数A1111扩展可能有兼容问题
- **更新频率**：可能不如A1111更新及时
- **SD 1.5优化有限**：主要针对SDXL优化
- **国内下载**：GitHub下载可能较慢
