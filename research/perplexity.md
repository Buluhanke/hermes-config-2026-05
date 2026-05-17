---
name: perplexity
description: Perplexity用法：Pages功能、Citations追踪、API
version: 1.0.0
category: research
---

# Perplexity

## When to Use
需要实时网络搜索+溯源的研究任务；生成可引用的研究报告；需要将研究结果整理为可分享页面。

## Core Features
- **实时搜索**：基于最新网络结果回答问题
- **Citations追踪**：每个答案标注来源链接，可直接溯源
- **Pages功能**：将研究结果生成为可分享的在线页面
- **API访问**：提供PPLX-API，支持程序化调用
- **Focus模式**：可限定搜索范围（学术、YouTube、Reddit等）
- **线程管理**：每个对话为一个线程，可回顾历史

## Quick Start
1. 访问perplexity.ai，免费注册
2. 输入问题，Perplexity返回带Citations的答案
3. 回答中点击"Create Page"可将结果发布为公开页
4. API用户：申请API Key后用curl调用PPLX-API

## Pitfalls
- 免费版有每日查询限额
- 答案有时会"幻觉"引用不存在的链接
- Pages生成的页面公开可访问，注意隐私
- API按token计费，成本需监控
