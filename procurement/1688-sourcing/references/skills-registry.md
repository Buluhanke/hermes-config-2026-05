# Hermes官方技能库 技能注册表

## 基础知识（2026-05-29）

### 安装命令语法

```bash
hermes skills install <identifier> --yes           # 安装
hermes skills install <identifier> --force --yes    # 强制安装（caution级别）
hermes skills list                                  # 列出已安装
hermes skills install --source <source> --yes       # 从指定源安装
hermes skills repair-official --restore --yes all   # 恢复官方optional技能
```

### 技能来源优先级

1. **built-in** — 官方内置，90个，全部自动安装，质量最可靠
2. **optional** — 官方可选，84个，需手动 `hermes skills install` 安装
3. **clawhub** — ClawHub社区，共6万+，质量参差不齐，有安全扫描

### 安全扫描 verdict 含义

- **SAFE** — 直接安装
- **CAUTION** — 可用 `--force` 强制安装，但代码审查需谨慎
- **DANGEROUS** — 即使 `--force` 也无法安装，通常是需要外部API密钥

### 常用 built-in 技能（已全部安装激活）

- `himalaya` — IMAP/SMTP邮件（终端）
- `ocr-and-documents` — PDF/扫描件文字提取
- `nano-pdf` — PDF编辑（自然语言）
- `powerpoint` — PPT创建/编辑
- `notion` — Notion API
- `writing-plans` — 实施计划撰写
- `apple-notes`、`apple-reminders`、`findmy`、`imessage` — Apple全家桶
- `macos-computer-use` — 后台桌面自动化
- `claude-code`、`codex`、`opencode` — 代码Agent委托
- `dogfood` — Web应用QA测试
- `yuanbao` — 元宝平台

### 常用 optional 技能

- `honcho` — 跨会话记忆/用户建模（memory provider）
- `agentmail` — 独立AI邮箱
- `scrapling` — Web抓取（stealth+Cloudflare绕过）
- `shopify` — Shopify管理

## 迅龙贸易相关技能

### 1688 ClawHub技能（已安装11个）

```
1688-sourcing-agent
1688-procurement-agent
1688-price-monitor
1688-source-suppliers        # --force安装
1688-shopkeeper             # --force安装
1688-shop-health-check      # --force安装
1688-item-select            # --force安装
1688-product-analysis       # --force安装
1688-finance-tax            # --force安装
1688-item-title-optimizer   # --force安装
1688-item-one-click         # --force安装
```

### 1688 ClawHub技能（需API Key，无法安装）

```
1688-product-search         # 需 ALI1688_APP_KEY/SECRET/TOKEN
1688-product-find           # 同上
1688-sourcing-inquiry       # 同上
1688-shop-operate           # 同上
```

## 技能库规模数据

| 来源 | 数量 |
|------|------|
| 总计 | 68,530 |
| built-in | 90 |
| optional | 84 |
| ClawHub | ~67,000 |

技能库URL：https://hermes-agent.nousresearch.com/docs/zh-Hans/skills
注册表JSON：https://hermes-agent.nousresearch.com/docs/api/skills.json
