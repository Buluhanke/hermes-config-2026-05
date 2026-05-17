---
name: midjourney
description: Midjourney AI图像生成工具用法指南
version: 1.0.0
---

# Midjourney AI 图像生成

## When to Use
- 需要高质量艺术风格图像时
- Logo、海报、插画等设计需求
- 快速原型概念可视化
- 追求多样化风格和创意输出

## Core Features

**核心指令：**
- `/describe` — 图生文：上传图片获取4条提示词
- `/imagine` — 文字生图：核心生成指令
- `/vary` — 变化：基于已生成图像做变体（Subtle/Strong/Zoom/Region）
- `/blend` — 图片混合：2-5张图合成新图
- `/reroll` — 重新生成
- `/ upscale` — 放大：Light/Sharp/Creative三种模式

**参数详解：**
- `--ar 16:9` — 画幅比例
- `--sref` — 风格参考代码（如 `--sref 1234`）
- `--sw` — 风格强度（0-1000）
- `--niji` — Niji模式，动漫/二次元风格
- `--style raw` — 原始模式，减少默认美化
- `--v 6` — 版本号（v5.2/v6）
- `--s 250` — 风格化程度

**付费对比：**
| 套餐 | 价格 | 快速时间 | 慢速时间 |
|------|------|----------|----------|
| Free | 免费 | 0 | 25次/月 |
| Basic | $10/月 | 3.3小时 | 200分钟 |
| Standard | $30/月 | 15小时 | 无限 |
| Pro | $60/月 | 30小时 | 无限 |
| Mega | $120/月 | 60小时 | 无限 |

## Quick Start
```
/imagine prompt: a futuristic city at sunset, cyberpunk style, highly detailed --ar 16:9 --v 6 --s 250
```
1. 在Discord或网页版发送 `/imagine`
2. 输入英文提示词
3. 添加参数（可选）
4. 等待生成（快速模式需订阅）

## Pitfalls
- **英文提示词**：必须用英文，中文支持差
- **宽高比参数**：默认1:1，需手动指定 `--ar`
- **版权风险**：人脸、名人类图像可能被模糊处理
- **快速时间耗尽**：免费/低价套餐容易遇阻
- **niji模式偏动漫**：写实风格需用 `--style raw`
- **变体次数限制**：非订阅用户变体次数有限
