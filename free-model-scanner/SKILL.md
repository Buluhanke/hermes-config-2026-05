---
name: free-model-scanner
description: 自动扫描所有配置的API提供商，找出免费可用模型并汇报
triggers:
  - 扫描免费模型
  - 模型探测
  - 可用模型检查
  - provider扫描
---

# 免费模型扫描器

## 脚本
`~/.hermes/scripts/scan_free_models.py`

## 扫描范围
- **OpenRouter**: 查找 `:free` 标签模型，逐个实测
- **Nous Portal**: 查找免费模型
- **DeepSeek 直连**: 列出可用模型

## 手动运行
```bash
python3 ~/.hermes/scripts/scan_free_models.py
```

## 关联技能
- **provider-connectivity-diagnostics** — 父级技能，覆盖完整的提供商诊断和切换流程
- 引用数据: `hermes-config/provider-connectivity-diagnostics/references/free-model-scan-results.md`
