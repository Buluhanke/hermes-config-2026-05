---
name: ocr-fallback
description: OCR兜底能力 — DOM/AX树失效时的最后防线
version: 1.0.0
source: hermes-export engineering
triggers:
- Use when ocr fallback
trigger_type: general
---

# 5.5 OCR 兜底能力

> 当 DOM/AX 树读不到文字时（Canvas/WebGL/图片内文字/CAPTCHA），OCR 是最后防线。

## 触发条件
- DOM query 返回空但页面明显有内容
- Canvas/WebGL 渲染的内容
- 图片内的文字（验证码/截图）

## OCR 工具
- marker-pdf（文档类）
- 浏览器截图 + vision 分析（UI类）
