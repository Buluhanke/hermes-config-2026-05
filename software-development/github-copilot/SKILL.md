---
name: github-copilot
description: GitHub Copilot用法与效率技巧
version: 1.0.0
---

# GitHub Copilot — AI编程辅助

## When to Use
- 日常编码中快速补全重复/模式化代码
- 探索新API时获取即时示例
- 需要多行代码一次性生成时

## Core Features
- **幽灵文本（Ghost Text）**：实时预测补全，按Tab接受
- **Tab完整**：多种建议切换，Ctrl+Tab选下一个
- **MultiCursor编辑**：Alt+Click多光标，Shift+Alt+↑/↓列选择
- **Chat侧边栏**：选中代码后Ask Copilot解释/修改
- **Inline Chat**：Cmd+I内联对话，直接注入代码

## Quick Start
```bash
# 基础补全
# 打完函数签名 → Tab接受建议

# 多光标操作
Alt+Click        # 多光标定位
Shift+Alt+↓     # 列模式向下添加
Ctrl+Alt+Enter  # 一次性补全多行

# 快捷键
Cmd+I           # Inline Chat
Cmd+Shift+P → "Copilot"  # 命令面板
```

## Pitfalls
- 过度依赖导致代码同质化
- 安全漏洞/硬编码密钥未被检测
- 上下文窗口有限，长对话效果下降
- 不理解业务逻辑，可能生成语义错误的代码
- 补全内容与实际需求不符时要及时否定
