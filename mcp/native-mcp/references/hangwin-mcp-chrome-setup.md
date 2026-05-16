# hangwin/mcp-chrome 集成到 Hermes 的安装指南

> 最新更新：2026-05-15 — 确认 stdio 方案（mcp-chrome-stdio）工作正常，31 tools 已注册。
> 原始记录：2026-05-11 — HTTP bridge (port 12306) 方案因 MV3 SW 阻塞未打通。

## 快速上手（已知工作的方案）

**方案 B — Stdio 模式（已验证，生产可用）**

前提：Chrome 已通过 launchd 加载扩展（`--load-extension`），且 `mcp-chrome-bridge` npm 包已全局安装。

```bash
npm install -g mcp-chrome-bridge   # 如果还没装
```

在 `~/.hermes/config.yaml` 配置：

```yaml
mcp_servers:
  chrome:
    command: "mcp-chrome-stdio"
    timeout: 120
    connect_timeout: 60
```

重启 Hermes 即可（`hermes gateway restart`）。工具名前缀 `mcp_chrome_*`，共 31 个。

**要点：**
- `mcp-chrome-stdio` 与 `mcp-chrome-bridge` HTTP server 同属一个 npm 包
- 不走 HTTP bridge（无需 port 12306），绕过了 MV3 Service Worker 阻塞问题
- Chrome launchd plist 必须携带 `--load-extension=/Users/aimac/.hermes/mcp-chrome-extension`
- `mcp-chrome-stdio` 进程由 Hermes 的 MCP client 自动管理（spawn + lifecycle）
- server name 配 `chrome`（不要 `mcp_chrome` 或 `chrome-mcp`）

**验证：**

```bash
grep "MCP server 'chrome'" ~/.hermes/logs/agent.log
# 应看到：MCP server 'chrome' (stdio): registered 31 tool(s)
```

---

## 下方为历史记录：HTTP bridge (port 12306) 方案（2026-05-11 尝试，未打通）

> ⚠️ 以下内容作为历史诊断参考保留。实际生产使用上方的 stdio 方案即可。

Hermes CDP Chrome (port 9333) + MCP Chrome扩展的混合架构。

## 项目信息

- 仓库：https://github.com/hangwin/mcp-chrome (11.6k⭐, v1.0.0, 2025-12-29)
- 原理：Chrome扩展 + MCP桥接服务，暴露Chrome浏览器给MCP客户端
- 推荐连接方式：Streamable HTTP (port 12306)
- 工具量：20+（标签管理、截图、网络监控、语义搜索、内容分析、交互操作）

## 预检

### 检查环境

```bash
# 检查 Node.js 版本（需要 >= 20.0.0）
node --version

# 检查 npm/pnpm
npm --version
pnpm --version

# 检查我们的 Chrome 是否正常运行（非 headless，port 9333）
lsof -i :9333
curl -s http://127.0.0.1:9333/json/version | python3 -m json.tool
```

### 确认架构兼容性

**我们的 Chrome 配置**：非 headless 模式（无 `--headless` 参数），普通 Chrome 进程 + `--remote-debugging-port=9333`，独立 profile `~/.hermes/chrome-debug`。

**兼容性**：✅ hangwin/mcp-chrome 是 Chrome 扩展，基于 extensions API 工作，与 CDP 端口无关。它不需要 CDP，而是通过扩展与桥接服务通信。可以同时运行。

**潜在冲突**：
- MCP 工具和 Hermes CDP 工具可能同时操作同一 Chrome → 不同时使用即可
- 扩展加载后，Chrome 会多一个扩展进程（`--extension-process`），这是正常的

## 安装步骤

### 步骤 1：下载扩展

```bash
# 下载最新 release 的扩展 zip
cd /tmp
curl -L -o chrome-mcp-server-1.0.0.zip \
  "https://github.com/hangwin/mcp-chrome/releases/download/v1.0.0/chrome-mcp-server-1.0.0.zip"

# 解压到持久化位置
mkdir -p ~/.hermes/mcp-chrome-extension
unzip -o chrome-mcp-server-1.0.0.zip -d ~/.hermes/mcp-chrome-extension/
```

### 步骤 2：加载扩展到 CDP Chrome

**方式 A（推荐，重启Chrome后持久化）**：
给 launchd 的 Chrome 添加 `--load-extension` 参数，重启后扩展自动加载。

```bash
# 修改 launchd plist
launchctl unload ~/Library/LaunchAgents/com.aimac.hermes-chrome-debug.plist

# 编辑 plist，在 ProgramArguments 里添加：
# <string>--load-extension=/Users/aimac/.hermes/mcp-chrome-extension</string>

# 重新加载
launchctl load ~/Library/LaunchAgents/com.aimac.hermes-chrome-debug.plist
```

⚠️ 重启 Chrome 会丢失当前标签页，但 profile 中的 1688 登录态不丢。重启后自动恢复。

**方式 B（临时，不重启Chrome）**：
通过 CDP 连接到 9333，用 `chrome://extensions/` 手动加载：
```bash
# 在 CDP 浏览器中导航到扩展页
browser_navigate("chrome://extensions/")
# 开启"开发者模式" → "加载已解压的扩展" → 选择 ~/.hermes/mcp-chrome-extension
```
扩展加载后在当前会话生效，Chrome 重启后可能丢失（取决于 Chrome 版本行为）。

### 步骤 3：安装 mcp-chrome-bridge

```bash
# 全局安装桥接服务
npm install -g mcp-chrome-bridge

# 验证安装
# 约 2 分钟后可手动启动验证（如果 Chrome 扩展已加载）
# mcp-chrome-bridge 启动后会在 port 12306 监听
```

### 步骤 4：配置 Hermes MCP

编辑 `~/.hermes/config.yaml`，添加：

```yaml
mcp_servers:
  chrome-mcp:
    url: "http://127.0.0.1:12306/mcp"
    timeout: 120
    connect_timeout: 60
```

### 步骤 5：启动桥接服务

```bash
# 启动 mcp-chrome-bridge （手动，后续考虑加入 launchd）
mcp-chrome-bridge &

# 验证端口
sleep 3 && lsof -i :12306
```

### 步骤 6：重启 Hermes

```bash
hermes gateway restart
```

启动后 Hermes 会自动连接 MCP 服务器并发现工具。工具命名前缀为 `mcp_chrome_mcp_*`。

## 验证

### 验证扩展已加载

```bash
# 在 CDP Chrome 中检查扩展
curl -s http://127.0.0.1:9333/json | python3 -c "
import json, sys
data = json.load(sys.stdin)
for tab in data:
    if 'extension' in tab.get('title', '').lower() or 'mcp' in tab.get('url', ''):
        print(f'Found MCP extension tab: {tab[\"title\"]}')
"
```

### 验证桥接服务运行

```bash
# 检查端口
lsof -i :12306

# 尝试 MCP 协议连接（检查工具列表）
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | \
  curl -s -X POST http://127.0.0.1:12306/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

### 验证 Hermes 连接

重启后，检查 Hermes 日志是否有 MCP 连接成功的信息：
```bash
tail -50 ~/.hermes/logs/hermes.log | grep -i mcp
```

应看到类似 `"Connected to MCP server 'chrome-mcp'"` 和 `"Registered N tools from chrome-mcp"`。

## 可用工具列表

连接成功后 Hermes 可用的 MCP 工具（完整列表见上游文档 `docs/TOOLS.md`）：

| 类别 | 工具 | 用途 |
|------|------|------|
| 浏览器管理 | `get_windows_and_tabs` | 列出所有窗口和标签 |
| | `chrome_navigate` | 导航到URL |
| | `chrome_switch_tab` | 切换标签 |
| | `chrome_close_tabs` | 关闭标签 |
| 截图 | `chrome_screenshot` | 截图（支持元素定位、全页） |
| 内容分析 | `search_tabs_content` | **语义搜索**（向量数据库） |
| | `chrome_get_web_content` | 提取页面HTML/文本 |
| | `chrome_get_interactive_elements` | 查找可交互元素 |
| 交互 | `chrome_click_element` | 点击元素 |
| | `chrome_fill_or_select` | 填表/选择 |
| | `chrome_keyboard` | 键盘输入 |
| 网络 | `chrome_network_capture_start/stop` | 网络抓包 |
| | `chrome_network_request` | 发送HTTP请求 |
| 数据 | `chrome_history` | 浏览历史 |
| | `chrome_bookmark_search/add/delete` | 书签管理 |

## Pitfalls

1. **桥接服务需要先于 Hermes 启动** — Hermes 启动时连接 MCP 服务器，如果 bridge 没在运行，连接会失败。考虑加入 launchd 让 bridge 自启。
2. **扩展和 bridge 是一对一的** — 扩展连接 bridge，bridge 暴露 MCP。缺任何一环都不行。
3. **CDP 和 MCP 共享同一个 Chrome 实例** — 两个 Hermes 功能同时操作浏览器可能会冲突。使用上要区分：CDP 用于 1688 深度工作，MCP 用于其他站点探索。
4. **扩展在无头模式下可能不工作** — 我们的 Chrome 不是 headless（无 `--headless` 参数），所以没问题。但如果未来改成 headless，扩展可能无法加载。
5. **Chrome 重启后扩展状态** — 通过 `--load-extension` 加载的扩展在重启后自动恢复。手动加载的（方式B）可能丢失。
6. **mcp-chrome-bridge 安装后 postinstall 脚本** — pnpm v7+ 默认禁用 postinstall 脚本。用 npm 安装更简单，或用 pnpm 加 `pnpm config set enable-pre-post-scripts true`。

## 关键阻碍：MV3 Service Worker 不自动运行（2026-05-11 实测）

**这是最大的问题，实测未能解决。**

### ⚠️ 诊断陷阱：chrome://serviceworker-internals/ 看到的ID不一定是目标扩展

2026-05-11 实测发现：在 chrome://serviceworker-internals/ 中看到一个 SW 状态为 `STARTING`，ID 为 `fignfifoniblkonapihmkfakmlgkbkcf`，**这个扩展不是 mcp-chrome-server**，而是 Chrome 内置的"Google Network Speech" TTS 扩展！

这个发现浪费了大量时间追查错误的 ID。

**正确诊断流程：**
1. **第一步**：`chrome://extensions/` → 确认扩展是否出现在已启用列表（看名称和图标，不要只看ID）
2. **第二步**：`chrome://extensions-internals/` → 列出所有已加载扩展（包括内置的），看目标扩展是否在其中
3. **第三步**：`chrome://serviceworker-internals/` → 只在确定扩展已加载后，才看它的 SW 状态
4. **`chrome://version/`** → 检查命令行的 `--load-extension` 参数是否出现在页面中（确认传递成功）

**关键教训**：serviceworker-internals 页面可能显示 Chrome 内置扩展的 SW 而非目标扩展的 SW。始终先用 extensions 或 extensions-internals 确认扩展**已经被 Chrome 识别并加载**，再查 SW 状态。

### ⚠️ 扩展在 chrome://extensions-internals/ 中不可见

2026-05-11 实测：即使 `chrome://version/` 显示 `--load-extension=/Users/aimac/.hermes/mcp-chrome-extension` 参数已生效，**目标扩展也未出现在 chrome://extensions-internals/ 的已加载扩展列表中**。

可能原因：
- 扩展的 `manifest.json` 解析失败（语法问题或版本不兼容）
- 扩展依赖的 `minimum_chrome_version` 高于当前 Chrome 版本
- 扩展的 `key` 字段计算的 ID 与 Chrome 内部验证方式不匹配
- 扩展解压目录不完整（缺少关键文件如 `background.js`）

**诊断验证**：用 CDP 发请求检查扩展详情（如果没加载，`chrome.management.getAll()` 里不会有它）：

```bash
curl -s http://127.0.0.1:9333/json/version | python3 -c "import json,sys; d=json.load(sys.stdin); print('--load-extension' in d.get('command',''))"
# 返回 True 不代表扩展真的加载了
```

### chrome://version/ 与 chrome://extensions-internals/ 不一致

常见现象：`chrome://version/` 的命令行参数中确实有 `--load-extension=/path/to/ext`，但目标扩展并未出现在扩展管理列表中。

可能原因：
1. **路径不正确**：Chrome 期望的路径格式与当前路径不同（例如有 `../` 等相对路径组件）
2. **manifest.json 错误**：扩展未通过 Chrome 的 manifest 校验（如缺失 `minimum_chrome_version` 或 `key` 格式错误）
3. **冲突**：已加载的扩展版本和 `--load-extension` 指定的版本冲突

修复尝试：
- 确认 manifest.json 可用 `python3 -c "import json; json.load(open('manifest.json'))"` 解析
- 路径使用绝对路径，不要用 `~` 或 `..`
- 尝试通过 chrome://extensions/ → 开发者模式 → "加载已解压的扩展" 手动加载，看是否有错误提示

### 现象

即使：
- ✅ 扩展通过 `--load-extension` 正确加载（chrome://extensions/ 显示已启用）
- ✅ Native Messaging Host 配置文件路径正确、`allowed_origins` 的扩展ID与实际一致
- ✅ Chrome CDP (port 9333) 正常运行
- ✅ mcp-chrome-bridge npm 包已全局安装

扩展的 **Service Worker 状态始终为 STOPPED**。Chrome 不会自动启动 MV3 event-driven service worker，除非有触发事件（用户点击扩展图标、页面触发了 `chrome.runtime.connectNative` 等）。Service Worker 不启动，扩展就无法通过 Native Messaging 与 bridge 通信。

### 根因分析

1. **MV3 架构变更**：MV2 用 `background.html` 持续运行的 Background Page，MV3 改用 Service Worker，只在收到事件时启动，空闲时休眠。`--load-extension` 只是将扩展注册到 Chrome，但不会主动触发 Service Worker 启动。

2. **扩展 ID 不匹配（关键陷阱）**
   - `dist/constant/index.js` 中硬编码的扩展ID：`hbdgbgagpkpjffpklnamcljpakneikee`
   - 实际 Chrome 用 manifest `key` 字段生成的ID：`fignfifoniblkonapihmkfakmlgkbkcf`
   - **两者不同**。bridge 用硬编码 ID 连接 Native Messaging，而 Chrome 实际上注册了另一个 ID。
   - *原因解释*：manifest.json 的 `key` 是 PEM 公钥的 base64，Chrome 通过公钥计算扩展 ID。但 `algorithm` 参数（可选，默认 `RSASHA256`）影响计算结果。bridge 包里写死了假设值。
   - 虽然修正了 Native Messaging Host 的 `allowed_origins`（改为真实 ID），但 **bridge 进程内部的连接逻辑仍用旧 ID**，无法与扩展握手。

3. **bridge 进程依赖扩展 SW 存活**
   - bridge 启动后等待扩展连接 Native Messaging Host
   - 但扩展 SW 不启动 → 不会调用 `chrome.runtime.connectNative` → 不会触发 `ensureNativeConnected("sw_startup")`
   - bridge 一直在等扩展连接，而扩展也在等 bridge 连接——**死锁**

### 尝试过的修复（均无效）

| 方法 | 结果 |
|------|------|
| 通过 CDP 导航到 chrome://serviceworker-internals/，点 Start 按钮 | 按钮无效果，SW 仍 STOPPED |
| CDP eval `chrome.debugger.attach` | 扩展未加载到目标中 |
| 启动 bridge 再打开扩展 popup | bridge 端口无监听 |
| 重启 Chrome 多次（修正 Native Host JSON 后） | 同一问题，SW 不启动 |
| 修改 bridge 源码（dist/constant/index.js 中扩展ID） | 理论上可行但未验证（需要改源码重新安装） |

### 可尝试的解决方案（未来）

1. **修改 bridge 源码**：在 `dist/constant/index.js` 中将扩展ID改为实际值 `fignfifoniblkonapihmkfakmlgkbkcf`，重新安装 bridge
2. **模拟 SW 触发**：通过 CDP eval 直接调用 `chrome.runtime.connectNative` 强行建立连接
3. **弹出扩展 popup**：手动在 CDP 浏览器中点击扩展图标，触发 SW 启动
4. **回退到 MV2**：如果上游提供 MV2 版本或迁到其他支持 MV2 的浏览器

### 现状判断

截至 2026-05-11，**hangwin/mcp-chrome 在与 CDP `--load-extension` Chrome 实例的集成上存在实质障碍**。扩展本身可加载但 Service Worker 不自动运行，bridge 无法建立连接。原因可能是 MV3 Service Worker 生命周期 + 扩展ID硬编码的双重问题。

如果后续步骤是继续尝试打通，优先级最高的是**修改 bridge 源码中的硬编码扩展 ID**，使 bridge 用实际注册的 ID 发起 Native Messaging 连接。

## 恢复到 CDP-only（不需要 MCP 了）

```bash
# 1. 从 config.yaml 移除 chrome-mcp 条目
# 2. 从 launchd plist 移除 --load-extension
# 3. 重启 Chrome + Hermes
# 4. 可选：卸载 bridge
npm uninstall -g mcp-chrome-bridge
rm -rf ~/.hermes/mcp-chrome-extension
```
