---
name: comfyui-manager
description: ComfyUI-Manager 节点自动安装与工作流市场
version: 1.0.0
---

# ComfyUI-Manager 使用指南

## When to Use
- 使用ComfyUI，需要简化节点安装
- 不确定需要哪些依赖节点
- 想复用社区工作流
- 想要一键更新所有节点

## Core Features

**安装ComfyUI-Manager：**
```bash
# 在ComfyUI/custom_nodes/下
git clone https://github.com/ltdrdata/comfyui-manager.git
```
重启ComfyUI后，在界面左侧看到"Manager"面板。

**节点自动安装：**
- 搜索节点名称，一键安装
- 自动处理依赖关系
- 显示节点版本和更新状态
- 安装失败时显示具体错误

**工作流市场（Custom Nodes / Workflows）：**
- Browse（浏览）— 查看社区分享的工作流
- 搜索关键词（LoRA、ControlNet、放大等）
- 一键安装工作流所需的所有节点和模型
- 工作流以JSON格式导入

**模型管理：**
- 管理已安装的模型（Checkpoint、LoRA、VAE等）
- 一键下载缺失模型
- 模型版本控制
- 模型存放路径引导

**其他功能：**
- **Extension Update**：一键更新所有节点扩展
- **ComfyUI Update**：更新ComfyUI本身
- **Requirement Conflict Manager**：解决Python依赖冲突

## Quick Start
1. 安装ComfyUI-Manager
2. 打开ComfyUI，进入Manager面板
3. 点击"Install Custom Nodes"搜索安装节点
4. 或点击"Install Missing Nodes"自动补全当前工作流所需节点
5. 工作流市场下载现成工作流

## Pitfalls
- **网络问题**：从GitHub下载节点可能失败（国内）
- **依赖冲突**：部分节点依赖版本冲突，需手动解决
- **模型下载**：Manager不自动下载大模型文件
- **Windows路径**：路径中有中文可能导致问题
- **更新风险**：更新节点可能破坏现有工作流
