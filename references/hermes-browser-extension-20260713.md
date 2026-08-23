# Hermes Browser Extension — 研究记录 (2026-07-13)

## 源
- GitHub: `abundantbeing/hermes-browser-extension` (Jon Komet @abundantbeing)
- 最新版本: v0.1.11 (public alpha)
- 安装方式: Load unpacked，Chrome/Edge/Chromium 114+

## 构建步骤
```bash
cd /tmp
git clone --depth=1 https://github.com/abundantbeing/hermes-browser-extension.git
cd hermes-browser-extension
npm install
npm run build
# 输出: dist/ 目录
```

## Hermes API Server 配置（已就绪）
- Hermes API Server 运行中: `http://127.0.0.1:8642` ✅
- Key: `hermes-webui-secret-key`
- 验证: `curl -H "Authorization: Bearer hermes-webui-secret-key" http://127.0.0.1:8642/health`
- `.env` 中已有: `API_SERVER_ENABLED=true, API_SERVER_PORT=8642`

## 安装步骤（手动）
1. Chrome 打开 `chrome://extensions/`
2. 右上角开【开发者模式】
3. 点击【加载解压的扩展程序】
4. 选择 `/tmp/hermes-browser-extension/dist/`
5. `Alt+H` 打开侧边栏
6. 手动设置 → Local gateway → `http://127.0.0.1:8642` → 密钥填 `hermes-webui-secret-key`

## 核心功能
- Chrome 侧边栏，直接对话 Hermes
- 页面上下文自动捕获（标题/URL/选中文字/页面可读文本）
- 只读模式，不控制浏览器
- 支持 Local / Hermes Cloud / Remote 三种连接模式
- 快捷命令: /summarize /explain /rewrite /tabs /action-items

## 对 Hermes 的增益评估
**中等**。Hermes 已有能力:
- CDP 浏览器控制 (`browser_navigate/click/type`)
- API Server (`http://127.0.0.1:8642`)
- computer_use (CUA 全系统控制)

这个扩展解决的是「浏览网页时随手问 Hermes」的场景，已有能力可覆盖大部分。

## 关键限制
- 安装需要手动点选（chrome:// 页面 CDP/browser_navigate 均被 block）
- Firefox/Safari 不支持（需 browser API）
