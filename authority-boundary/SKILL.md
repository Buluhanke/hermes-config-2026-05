---
name: authority-boundary
description: 权责边界 — 什么操作必须用户授权，什么可自主执行
version: 1.0.0
source: hermes-export engineering
triggers:
- Use when authority boundary
trigger_type: general
---

# 10.4 权责边界

> 什么操作必须用户授权，什么是 Agent 可自主执行。

## 已定义（USER.md v2.2/v2.8）
- ✅ 必须授权：rm -rf ~/ / 格式化 / 改生产配置 / 密码输入 / 支付
- ✅ 自主执行：安装软件 / 清理缓存 / 改配置 / 读写文件 / 跑脚本

## 默认规则（2026-06-23 v3.0）
- 用户在场 + 非破坏性 = 直接干
- 不可逆操作 = 单人确认
- 24GB 硬件红线不破
