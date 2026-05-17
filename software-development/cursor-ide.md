---
name: cursor-ide
description: Cursor IDE用法：快捷键、Agent模式、Tab实现原理、阻止全文件续写技巧
version: 1.0.0
category: software-development
---

# Cursor IDE

## When to Use
需要AI辅助编程时；希望对AI生成代码有精细控制时；需要理解Cursor的Tab续写机制以优化编码体验。

## Core Features
- **Agent模式**：Cmd+K打开Composer，可对话生成/编辑代码，支持多文件操作
- **Tab智能续写**：基于项目上下文的大模型代码补全，按Tab接受
- **快捷键**：Cmd+K(Composer)、Cmd+L(Chat)、Cmd+/(Inline Chat)、Tab(接受续写)、Esc(拒绝)
- **阻止全文件续写**：设置中关闭"Enable completions"或使用`` @``精确引用文件
- **多文件编辑**：Composer中可同时打开多个文件，AI会追踪修改
- **Context感知**：自动读取光标周围代码作为上下文

## Quick Start
1. 下载安装Cursor后，打开项目文件夹
2. `Cmd+K`打开Composer，输入需求描述
3. `Tab`接受AI生成的代码续写
4. 若不希望AI续写整个文件：Settings → Editor → 关闭"Enable completions"

## Pitfalls
- Tab续写可能覆盖光标后的代码，接受前仔细核对
- Composer生成的代码默认会创建新文件而非修改现有文件，需手动整合
- 国内访问可能不稳定，配置代理
