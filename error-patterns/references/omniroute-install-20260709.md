# OmniRoute 3.8.46 安装调试记录（2026-07-09）

来源：本 session OmniRoute 3.8.46 npm 全局安装 + 启动调试全过程。

## 启动命令是 `serve` 不是 `start`
- `omniroute start` → error: too many arguments for 'serve'. Expected 0 arguments but got 1: start
- 正确：`omniroute serve`（或直接 `omniroute`，serve 是 default command）
- `--daemon` 后台守护：`omniroute serve --daemon`

## Node.js native module 版本不匹配（最常见卡点）
症状：启动时打印
```
Native binary dlopen failed: ... NODE_MODULE_VERSION 137 ... requires ... 147
```
根因：npm 全局包安装时 better-sqlite3 等 native 模块预编译 binary 的 Node 版本与当前系统 Node 版本不一致。

修法（按顺序试）：
1. `cd /path/to/package/dist && npm rebuild better-sqlite3`
2. `omniroute runtime repair`（官方修复，在 ~/.omniroute/runtime/ 重建兼容版本）
3. 如果 runtime repair 后的版本仍不生效，手动替换：
   ```bash
   cp -r ~/.omniroute/runtime/node_modules/better-sqlite3 \
     /Users/aimac/.local/lib/node_modules/omniroute/dist/node_modules/better-sqlite3
   ```
   然后验证：`node -e "require('/path/to/dist/node_modules/better-sqlite3'); console.log('OK')"`

## OmniRoute 500 错误的根因：空数据库 + 未初始化

**判断顺序：**
1. `curl /` → 返回 HTML = Next.js 服务在跑
2. `curl /api/monitoring/health` → 返回 500 = 数据库未初始化
3. `sqlite3 ~/.omniroute/storage.sqlite "SELECT * FROM db_meta"` → 只有 `schema_version=1` = 全新空库
4. `omniroute doctor` → 显示 "Server reachable (health endpoint returned 500, likely requires MANAGEMENT_TOKEN)" = 数据库空，需要初始化

**表现：** 所有 `/api/*` 路由 500，但 HTML dashboard 正常。

**解决：** 必须通过 Desktop app 完成首次引导（设置密码、添加 provider key），或 CLI `omniroute setup --add-provider` 添加真实 credentials。

## 健康检查端点区分
- `curl /health` → dashboard 引导阶段正常返回（Next.js 服务在跑）
- `curl /api/monitoring/health` → 需要 MANAGEMENT_TOKEN，未配置时返回 500
- `omniroute status` 和 `simulate` 命令内部调用 `/api/monitoring/health`，数据库未初始化时这些命令会报"Server is offline"
- `omniroute doctor` 直接读 SQLite 不走 API，所以能正常显示 server reachable

## Desktop app 和 npm 全局包是两套独立运行时（OmniRoute 独享端口 20128）
- Desktop app (OmniRoute.app) 内置 Electron + Node（测试机上是 v16），监听 20128
- npm 全局包用系统 Node（如 v24），也需要 20128 端口
- 两者同时跑会端口冲突。先杀掉一个再启动另一个。
- 查看端口占用：`lsof -i :20128`
- 杀掉 Desktop app 的 node 进程：`pkill -9 -f "OmniRoute" 2>/dev/null; pkill -9 -f "omniroute" 2>/dev/null`

## /v1/models 超时但 dashboard HTML 正常
- 说明 Next.js 服务在跑，但 API 路由层未完成初始化
- 通常是首次启动未完成 dashboard 引导配置
- 解决：用 Desktop app 完成首次引导初始化，或 CLI `omniroute setup --add-provider` 添加 credentials

## .env 配置位置
- npm 全局包读取：`~/.local/lib/node_modules/omniroute/.env`（模板，含所有变量说明）
- 用户数据目录：`~/.omniroute/`（运行时数据、SQLite DB、server.env）
- Desktop app 数据：`~/Library/Application Support/omniroute-desktop/`

## 关键进程信息
- CLI 版本路径：`~/.local/lib/node_modules/omniroute/bin/omniroute.mjs`
- runtime 目录：`~/.omniroute/runtime/`（包含与 Node 147 兼容的 better-sqlite3）
- 端口：20128
- 健康检查：`curl http://localhost:20128/`（返回 HTML 则服务在跑）
