# OmniRoute 安装踩坑全记录（2026-07-10）

## 环境
- macOS arm64 (Apple Silicon)
- Node v24.14.1（系统 node）
- npm 全局安装路径：~/.local/lib/node_modules/
- OmniRoute 版本：3.8.46

## 安装路径
- npm 包：`~/.local/lib/node_modules/omniroute/`
- CLI：`omniroute` 命令（npm 全局 bin）
- 配置：~/.omniroute/
- 日志：~/.omniroute/logs/
- 数据库：~/.omniroute/storage.sqlite（1.7MB，桌面板创建）

## 问题 1：asar 打包不完整（导致黑屏）
- **症状**：OmniRoute Desktop.app 打开黑屏，日志出现 `Failed to load external module ws-a972e7ffa40ff725`
- **根因**：DMG 里的 app.asar 打包不完整，缺少 14 个 native node_modules
- **检查**：`ls /Applications/OmniRoute.app/Contents/Resources/app/.build/next/node_modules/` 应该有 14+ 个包，实际只有 0 个
- **修复**：重新从 GitHub 下载完整 DMG（OmniRoute-3.8.46-arm64.dmg），安装后验证包数量：
  ```bash
  ls /Applications/OmniRoute.app/Contents/Resources/app/.build/next/node_modules/ | wc -l
  # 应该返回 14 或更多
  ls /Applications/OmniRoute.app/Contents/Resources/app/.build/next/node_modules/ | grep "ws-\|better-sqlite3-\|playwright-\|sqlite-vec-"
  ```

## 问题 2：better-sqlite3 ABI 不兼容（导致 serve 失败）
- **症状**：`omniroute serve` 报 `Native binary dlopen failed: NODE_MODULE_VERSION 137 vs 147`
- **根因**：两个 npm 包位置
  - `~/.local/lib/node_modules/omniroute/dist/node_modules/better-sqlite3/` — ABI 137（Node 23 编译）❌
  - `~/.local/lib/node_modules/omniroute/node_modules/better-sqlite3/` — 可能与 Node 24 兼容 ✅
- **修复**：`rm -rf ~/.local/lib/node_modules/omniroute/dist/node_modules/better-sqlite3`
- **验证**：`node -e "require('~/.local/lib/node_modules/omniroute/node_modules/better-sqlite3')"` 不报错则兼容
- **注意**：`npm rebuild` 报成功但 binary 日期不变（假成功），不要依赖 rebuild

## 问题 3：Desktop app 进程跑但不监听端口
- **症状**：`ps aux | grep OmniRoute` 有进程，但 `lsof -i :20128` 无监听
- **根因**：app 的 WebView 渲染失败，没有启动内置 server
- **修复**：不要依赖 Desktop app 的 server，用 CLI 启动：
  ```bash
  cd ~/.local/lib/node_modules/omniroute && node bin/omniroute.mjs serve
  ```

## 问题 4：storage.sqlite 空（导致所有 API 500）
- **症状**：`curl localhost:20128/api/monitoring/health` 返回 500
- **根因**：数据库没有任何 api_keys，需要完成 onboarding
- **验证**：`sqlite3 ~/.omniroute/storage.sqlite "SELECT COUNT(*) FROM api_keys"` 返回 0
- **修复**：
  ```bash
  omniroute setup --add-provider --provider openai --api-key YOUR_KEY --provider-name "OpenAI" --non-interactive
  ```

## 快速验证命令
```bash
# 1. 验证 CLI 正常
omniroute doctor

# 2. 验证 server 启动
curl localhost:20128/api/monitoring/health
# 500 = 数据库空的（正常），connection refused = server 没跑

# 3. 验证 desktop app 包完整性
ls /Applications/OmniRoute.app/Contents/Resources/app/.build/next/node_modules/ | wc -l
# 应该 >= 14
```

## CLI 命令
```bash
omniroute serve        # 启动 server（端口 20128）
omniroute doctor       # 诊断检查
omniroute setup        # 添加 provider
omniroute runtime repair  # 修复 native module
```
