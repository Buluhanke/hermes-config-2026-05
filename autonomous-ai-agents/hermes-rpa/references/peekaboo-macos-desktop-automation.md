# Peekaboo macOS 桌面自动化工具 (2026-05-12)

## 概述

**项目**：Peekaboo - macOS 语音/视觉/触控 UI Agent
**来源**：[@steipete/peekaboo](https://github.com/steipete/Peekaboo) (npm)
**安装方式**：`npm install -g @steipete/peekaboo`
**当前版本**：v3.1.2
**许可证**：MIT

## 核心能力

| 命令 | 功能 | 备注 |
|------|------|------|
| `peekaboo see` | 截图 + 分析屏幕 | 走 macOS 截图 API |
| `peekaboo click <x> <y>` | 点击指定坐标 | 模拟鼠标点击 |
| `peekaboo type <文本>` | 键盘输入 | 支持中文 |
| `peekaboo agent <描述>` | AI Agent 自主执行 | 用 LLM 理解屏幕并操作 |
| `peekaboo image <提示>` | 截取屏幕区域 | 基于视觉元素定位 |
| `peekaboo permissions status` | 检查权限状态 | macOS 隐私权限 |

## 权限要求

1. **屏幕录制** (Screen Recording) - System Settings > Privacy & Security > Screen Recording
2. **辅助功能** (Accessibility) - System Settings > Privacy & Security > Accessibility
3. **事件合成** (Event Synthesizing) - 触控板/键盘模拟

验证：`peekaboo permissions status`
预期输出（2026-05-12 在 Mac mini macOS 26.4.1 上验证）：
```
Screen Recording ... Granted
Accessibility ..... Granted
Event Synthesizing . Granted
```

## 安装方式

### 方式A：npm 全局安装（推荐，已验证通过）
```bash
npm install -g @steipete/peekaboo
```
**优点**：快速稳定（1 package added in 243ms），不依赖 Homebrew，首选方式。

### 方式B：Homebrew（不推荐）
```bash
# 已反复超时，不推荐使用
brew install steipete/tap/peekaboo
```
**问题**：`brew install` 命令在本机（Mac mini, macOS 26.4.1）上**持续超时**（exit 124, timeout 180s+），即便加了 `HOMEBREW_NO_AUTO_UPDATE=1` 也无效。原因可能为网络代理环境导致 Homebrew 资源下载缓慢。**不要再尝试 Homebrew 方式。**

## 与 hermes-rpa 对比

| 维度 | Peekaboo | Hermes RPA (AXUI + cliclick) |
|------|----------|------------------------------|
| 视觉能力 | ✅ 内置 AI vision（可理解屏幕内容） | ❌ 仅 OCR 文字识别 |
| 自主执行 | ✅ `peekaboo agent` 自带 Agent 循环 | ❌ 需 Hermes LLM 自己做决策 |
| macOS 原生 | ✅ Swift 原生，API 调用级 | ⚠️ Python + AppleScript |
| MCP 集成 | ✅ 支持 MCP server 模式 | ❌ 无内置 MCP 支持 |
| 权限需求 | 屏幕录制 + 辅助功能 + 事件合成 | 辅助功能 + 屏幕录制 |
| 稳定性 | ⚠️ 新项目，未充分验证 | ✅ 已稳定运行 |
| 输入方式 | 坐标 (x,y) | 坐标 (x,y) |

## 潜在价值

1. **`peekaboo see` 替代 OCR**：用 AI vision 直接理解屏幕内容，比 Baidu OCR 更智能（能识别按钮、图标、区域布局）
2. **`peekaboo agent` 简化复杂操作**：一句"点击搜索框输入纸箱"即可执行，不需要手动算坐标
3. **MCP server 模式**：可通过 MCP 协议供 Hermes 调用，与现有架构集成

## 已验证成功的 morning-watch 流程（2026-05-15）

**目标**：早上8:30自动截屏 → 检测通知/弹窗 → 汇报老板

```bash
# Step 1: 截屏（用 peekaboo image）
peekaboo image --mode screen --path /tmp/morning-watch.jpg --format jpg
# → /tmp/morning-watch.jpg (1920x1080, ~500KB)

# Step 2: 用 execute_code + Python urllib 调用 Baidu OCR 分析
# （不要用 vision_analyze / browser_vision — MiniMax 模型不支持 image_url）
python3 -c "
import urllib.request, urllib.parse, base64, json, os
with open(os.path.expanduser('~/.hermes/.env')) as f:
    for l in f:
        if '=' in l and not l.startswith('#'):
            k,v = l.strip().split('=',1); os.environ[k]=v
token_url = f'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={os.environ[\"BAIDU_API_KEY\"]}&client_secret={os.environ[\"BAIDU_SECRET_KEY\"]}'
with urllib.request.urlopen(token_url) as r:
    at = json.loads(r.read())['access_token']
with open('/tmp/morning-watch.jpg','rb') as f:
    b64 = base64.b64encode(f.read()).decode()
data = urllib.parse.urlencode({'image': b64}).encode()
req = urllib.request.Request(f'https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic?access_token={at}', data=data, method='POST')
req.add_header('Content-Type','application/x-www-form-urlencoded')
with urllib.request.urlopen(req) as r:
    result = json.loads(r.read())
    print(f'检测到文字数: {result.get(\"words_result_num\",0)}')
    for w in result.get('words_result',[])[:20]:
        print(w['words'])
"

# Step 3: 判断
# - words_result_num == 0 → 屏幕干净，报告"一切正常"
# - 有文字内容 → 分析是否需要处理
```

**已知限制**：`vision_analyze` 和 `browser_vision` 都报错 `unknown variant 'image_url'`（MiniMax 模型问题），不要尝试这两个工具分析截图。Baidu OCR 是目前唯一可靠的截图文字分析方式。

## 关键命令速查

```bash
# 安装
npm install -g @steipete/peekaboo

# 权限检查
peekaboo permissions status

# 截图看屏幕
peekaboo see

# AI Agent 模式
peekaboo agent "在 Chrome 搜索框中输入 '纸箱'"

# 点击坐标
peekaboo click 500 300

# 输入文字
peekaboo type "纸箱 45x25x8cm"

# 查看版本
peekaboo --version
```
