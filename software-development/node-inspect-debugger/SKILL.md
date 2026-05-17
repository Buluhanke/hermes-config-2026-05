---
name: node-inspect-debugger
description: "Debug Node.js via --inspect + Chrome DevTools Protocol CLI."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [debugging, nodejs, node-inspect, cdp, breakpoints, ui-tui]
    related_skills: [systematic-debugging, python-debugpy, debugging-hermes-tui-commands]
---

# Node.js Inspect Debugger

## Overview

When `console.log` isn't enough, drive Node's built-in V8 inspector programmatically from the terminal. You get real breakpoints, step in/over/out, call-stack walking, local/closure scope dumps, and arbitrary expression evaluation in the paused frame.

Two tools, pick one:

- **`node inspect`** — built-in, zero install, CLI REPL. Best for quick poking.
- **`ndb` / CDP via `chrome-remote-interface`** — scriptable from Node/Python; best when you want to automate many breakpoints, collect state across runs, or debug non-interactively from an agent loop.

**Prefer `node inspect` first.** It's always available and the REPL is fast.

## When to Use

- A Node test fails and you need to see intermediate state
- ui-tui crashes or behaves wrong and you want to inspect React/Ink state pre-render
- tui_gateway child processes (`_SlashWorker`, PTY bridge workers) misbehave
- You need to inspect a value in a closure that `console.log` can't reach without patching
- Perf: attach to a running process to capture a CPU profile or heap snapshot

**Don't use for:** things `console.log` solves in under a minute. Breakpoint-driven debugging is heavier; use it when the payoff is real.

## Quick Reference: `node inspect` REPL

Launch paused on first line:

```bash
node inspect path/to/script.js
# or with tsx
node --inspect-brk $(which tsx) path/to/script.ts
```

The `debug>` prompt accepts:

| Command | Action |
|---|---|
| `c` or `cont` | continue |
| `n` or `next` | step over |
| `s` or `step` | step into |
| `o` or `out` | step out |
| `pause` | pause running code |
| `sb('file.js', 42)` | set breakpoint at file.js line 42 |
| `sb(42)` | set breakpoint at line 42 of current file |
| `sb('functionName')` | break when function is called |
| `cb('file.js', 42)` | clear breakpoint |
| `breakpoints` | list all breakpoints |
| `bt` | backtrace (call stack) |
| `list(5)` | show 5 lines of source around current position |
| `watch('expr')` | evaluate expr on every pause |
| `watchers` | show watched expressions |
| `repl` | drop into REPL in current scope (Ctrl+C to exit REPL) |
| `exec expr` | evaluate expression once |
| `restart` | restart script |
| `kill` | kill the script |
| `.exit` | quit debugger |

**In the `repl` sub-mode:** type any JS expression, including access to locals/closure variables. `Ctrl+C` exits back to `debug>`.

## Attaching to a Running Process

When the process is already running (e.g. a long-lived dev server or the TUI gateway):

```bash
# 1. Send SIGUSR1 to enable the inspector on an existing process
kill -SIGUSR1 <pid>
# Node prints: Debugger listening on ws://127.0.0.1:9229/<uuid>

# 2. Attach the debugger CLI
node inspect -p <pid>
# or by URL
node inspect ws://127.0.0.1:9229/<uuid>
```

To start a process with the inspector from the beginning:

```bash
node --inspect script.js           # listen on 127.0.0.1:9229, keep running
node --inspect-brk script.js       # listen AND pause on first line
node --inspect=0.0.0.0:9230 script.js   # custom host:port
```

For TypeScript via tsx:

```bash
node --inspect-brk --import tsx script.ts
# or older tsx
node --inspect-brk -r tsx/cjs script.ts
```

## Programmatic CDP (scripting from terminal)

When you want to automate — set many breakpoints, capture scope state, script a repro — use `chrome-remote-interface`:

```bash
npm i -g chrome-remote-interface        # or project-local
# Start your target:
node --inspect-brk=9229 target.js &
```

Driver script (save as `/tmp/cdp-debug.js`):

```javascript
const CDP = require('chrome-remote-interface');

(async () => {
  const client = await CDP({ port: 9229 });
  const { Debugger, Runtime } = client;

  Debugger.paused(async ({ callFrames, reason }) => {
    const top = callFrames[0];
    console.log(`PAUSED: ${reason} @ ${top.url}:${top.location.lineNumber + 1}`);

    // Walk scopes for locals
    for (const scope of top.scopeChain) {
      if (scope.type === 'local' || scope.type === 'closure') {
        const { result } = await Runtime.getProperties({
          objectId: scope.object.objectId,
          ownProperties: true,
        });
        for (const p of result) {
          console.log(`  ${scope.type}.${p.name} =`, p.value?.value ?? p.value?.description);
        }
      }
    }

    // Evaluate an expression in the paused frame
    const { result } = await Debugger.evaluateOnCallFrame({
      callFrameId: top.callFrameId,
      expression: 'typeof state !== "undefined" ? JSON.stringify(state) : "n/a"',
    });
    console.log('state =', result.value ?? result.description);

    await Debugger.resume();
  });

  await Runtime.enable();
  await Debugger.enable();

  // Set a breakpoint by URL regex + line
  await Debugger.setBreakpointByUrl({
    urlRegex: '.*app\\.tsx$',
    lineNumber: 119,       // 0-indexed
    columnNumber: 0,
  });

  await Runtime.runIfWaitingForDebugger();
})();
```

Run it:

```bash
node /tmp/cdp-debug.js
```

Hermes-specific note: `chrome-remote-interface` is NOT in `ui-tui/package.json`. Install it to a throwaway location if you don't want to dirty the project:

```bash
mkdir -p /tmp/cdp-tools && cd /tmp/cdp-tools && npm i chrome-remote-interface
NODE_PATH=/tmp/cdp-tools/node_modules node /tmp/cdp-debug.js
```

## Debugging Hermes ui-tui

The TUI is built Ink + tsx. Two common scenarios:

### Debugging a single Ink component under dev

`ui-tui/package.json` has `npm run dev` (tsx --watch). Add `--inspect-brk` by running tsx directly:

```bash
cd /home/bb/hermes-agent/ui-tui
npm run build    # produce dist/ once so transpile isn't needed on first load
node --inspect-brk dist/entry.js
# In another terminal:
node inspect -p <node pid>
```

Then inside `debug>`:

```
sb('dist/app.js', 220)     # or wherever the suspect render is
cont
```

When it pauses, `repl` → inspect `props`, state refs, `useInput` handler values, etc.

### Debugging a running `hermes --tui`

The TUI spawns Node from the Python CLI. Easiest path:

```bash
# 1. Launch TUI
hermes --tui &
TUI_PID=$(pgrep -f 'ui-tui/dist/entry' | head -1)

# 2. Enable inspector on that Node PID
kill -SIGUSR1 "$TUI_PID"

# 3. Find the WS URL
curl -s http://127.0.0.1:9229/json/list | jq -r '.[0].webSocketDebuggerUrl'

# 4. Attach
node inspect ws://127.0.0.1:9229/<uuid>
```

Interacting with the TUI (typing in its window) continues to advance execution; your debugger can pause it on a breakpoint at any `sb(...)`.

### Debugging `_SlashWorker` / PTY child processes

Those are Python, not Node — use the `python-debugpy` skill for them. Only Node portions (Ink UI, tui_gateway client, tsx-run tests under `ui-tui/`) use this skill.

## Running Vitest Tests Under the Debugger

```bash
cd /home/bb/hermes-agent/ui-tui
# Run a single test file paused on entry
node --inspect-brk ./node_modules/vitest/vitest.mjs run --no-file-parallelism src/app/foo.test.tsx
```

In another terminal: `node inspect -p <pid>`, then `sb('src/app/foo.tsx', 42)`, `cont`.

Use `--no-file-parallelism` (vitest) or `--runInBand` (jest) so only one worker exists — debugging a pool is painful.

## Heap Snapshots & CPU Profiles (Non-interactive)

From the CDP driver above, swap Debugger for `HeapProfiler` / `Profiler`:

```javascript
// CPU profile for 5 seconds
await client.Profiler.enable();
await client.Profiler.start();
await new Promise(r => setTimeout(r, 5000));
const { profile } = await client.Profiler.stop();
require('fs').writeFileSync('/tmp/cpu.cpuprofile', JSON.stringify(profile));
// Open /tmp/cpu.cpuprofile in Chrome DevTools → Performance tab
```

```javascript
// Heap snapshot
await client.HeapProfiler.enable();
const chunks = [];
client.HeapProfiler.addHeapSnapshotChunk(({ chunk }) => chunks.push(chunk));
await client.HeapProfiler.takeHeapSnapshot({ reportProgress: false });
require('fs').writeFileSync('/tmp/heap.heapsnapshot', chunks.join(''));
```

## Common Pitfalls

1. **Wrong line numbers in TS source.** Breakpoints hit the emitted JS, not the `.ts`. Either (a) break in the built `dist/*.js`, or (b) enable sourcemaps (`node --enable-source-maps`) and use `sb('src/app.tsx', N)` — but only with CDP clients that follow sourcemaps. `node inspect` CLI does not.

2. **`--inspect` vs `--inspect-brk`.** `--inspect` starts the inspector but doesn't pause; your script races past your first breakpoint if you attach too late. Use `--inspect-brk` when you need to set breakpoints before any code runs.

3. **Port collisions.** Default is `9229`. If multiple Node processes are inspecting, pass `--inspect=0` (random port) and read the actual URL from `/json/list`:
   ```bash
   curl -s http://127.0.0.1:9229/json/list   # lists all inspectable targets on the host
   ```

4. **Child processes.** `--inspect` on a parent does NOT inspect its children. Use `NODE_OPTIONS='--inspect-brk' node parent.js` to propagate to every child; be aware they all need unique ports (Node auto-increments when `NODE_OPTIONS='--inspect'` is inherited).

5. **Background kills.** If you `Ctrl+C` out of `node inspect` while the target is paused, the target stays paused. Either `cont` first, or `kill` the target explicitly.

6. **Running `node inspect` through an agent terminal.** It's a PTY-friendly REPL. In Hermes, launch it with `terminal(pty=true)` or `background=true` + `process(action='submit', data='...')`. Non-PTY foreground mode will work for one-shot commands but not for interactive stepping.

7. **Security.** `--inspect=0.0.0.0:9229` exposes arbitrary code execution. Always bind to `127.0.0.1` (the default) unless you have an isolated network.

## One-Shot Recipes

**"Why is this variable undefined at line X?"**
```bash
node --inspect-brk script.js &
node inspect -p $!
# debug>
sb('script.js', X)
cont
# paused. Now:
repl
> myVariable
> Object.keys(this)
```

**"What's the call path into this function?"**
```
debug> sb('suspectFn')
debug> cont
# paused on entry
debug> bt
```

**"This async chain hangs — where?"**
```
# Start with --inspect (no -brk), let it run to the hang, then:
debug> pause
debug> bt
# Now you see the stuck frame
```

---

## 1. 完整调试配置 (Complete Debug Configuration)

### 环境变量

| 变量 | 作用 | 示例 |
|---|---|---|
| `NODE_OPTIONS` | 为所有Node进程注入inspect参数 | `NODE_OPTIONS='--inspect-brk'` |
| `NODE_INSPECTOR_PORT` | 覆盖默认9229端口 | `NODE_INSPECTOR_PORT=9230` |
| `NODE_INSPECT_WAIT_FOR_DEBUGGER` | 启动时等待 debugger attach | `--inspect-wait-for-debugger` |

### 启动方式汇总

```bash
# 基本监听（不暂停）
node --inspect script.js

# 暂停在入口（推荐，保留时间设断点）
node --inspect-brk script.js

# 绑定到任意Host:Port
node --inspect=0.0.0.0:9230 script.js        # 允许远程调试（仅限可信网络）
node --inspect=127.0.0.1:9229 script.js    # 仅本地（默认行为）

# 等待 debugger 连接后再执行
node --inspect-wait script.js

# 开启WARNING/错误堆栈的source-map支持
node --enable-source-maps --inspect-brk script.ts

# 传递自定义 debugger 端口给子进程
NODE_OPTIONS='--inspect=0.0.0.0:9229' node cluster.js
```

### TypeScript/tsx 配置

```bash
# tsx 自动支持 source-map，通常断点直接打在 .ts 上
node --inspect-brk --import tsx script.ts

# 旧版 tsx
node --inspect-brk -r tsx/cjs script.ts

# ts-node
node --inspect-brk -r ts-node/register script.ts
```

### 调试集群/子进程

Worker threads 和 child processes 默认不继承 `--inspect`。推荐通过 `cluster.setupMaster()` 或环境变量统一启用：

```javascript
// cluster-debug.js
const cluster = require('cluster');

if (cluster.isMaster) {
  // 用 NODE_OPTIONS='--inspect' 启动 master
  // master 再 fork workers 时，workers 会继承 NODE_OPTIONS
  cluster.fork();
} else {
  // worker: your actual work
}
```

```bash
NODE_OPTIONS='--inspect=0.0.0.0:9229' node cluster-debug.js
```

### Docker / 容器内调试

容器内 Node 绑定到 `0.0.0.0` 并通过 `-p 9229:9229` 端口映射：

```bash
# Dockerfile
ENV NODE_OPTIONS='--inspect=0.0.0.0:9229'
EXPOSE 9229
```

```bash
docker run --env NODE_OPTIONS='--inspect=0.0.0.0:9229' -p 9229:9229 my-node-app
```

> ⚠️ **安全警告**: 永远不要在生产环境开放 0.0.0.0:9229。使用 VPN 或 SSH tunnel 访问。

### Nodemon + Inspect

```bash
# nodemon.json
{
  "watch": ["src"],
  "ext": "ts,js",
  "exec": "node --inspect-brk",
  "args": ["--import", "tsx", "src/server.ts"]
}
```

```bash
npx nodemon
```

### pm2 调试

```bash
# 启动时开启 inspector
pm2 start app.js --node-args="--inspect-brk"

# attach 到运行中的进程
pm2 attach <pid> -- --inspect
```

---

## 2. Chrome DevTools 集成 (Chrome DevTools Integration)

### 基础连接

启动带 `--inspect` 的 Node 进程后：

1. Chrome 打开 `chrome://inspect`
2. 点击 **Open dedicated DevTools for Node**
3. 在 Targets 面板找到你的进程并点击 **inspect**

或直接访问: `chrome://inspect/#devices` → Remote Target → 点击对应进程。

### URL 自动发现

```bash
# 列出所有可用的 inspectable targets
curl -s http://127.0.0.1:9229/json/list | jq -r '.[].webSocketDebuggerUrl'
```

### 手动 WebSocket 连接

当 Chrome DevTools 无法自动发现时（如非默认端口、不同主机），手动添加：

1. Chrome DevTools → **...** 菜单 → **Settings** → **Devices**
2. 点击 **Add device**
3. **Network** 标签页: 输入 `ws://<host>:<port>/<uuid>`（从 `/json/list` 获取）
4. 保存后设备出现在列表中

### Chrome DevTools 常用功能

| 功能 | 用途 |
|---|---|
| **Sources面板** | 查看源码、设断点（支持条件断点、日志点） |
| **Call Stack** | 查看调用链路，点击任意帧跳转 |
| **Scope Variables** | 查看 local/closure/script 作用域变量 |
| **Watch** | 表达式持续监控 |
| **Console** | 在当前断点作用域执行代码 |
| **Network** | 抓取 HTTP 请求（Node 18+ 内置） |
| **Profiler** | CPU / Heap 性能分析 |
| **Memory** | Heap snapshot 对比、分配分析 |

### 条件断点 & 日志点

在 Sources 面板右键断点：

- **Condition**: `userId === 42 && order.status === 'pending'`
- **Logpoint** (日志点): `console.log('order status:', order.status)` — 不暂停，仅打印

### 使用 Chrome 抓取 Heap Snapshot

1. DevTools → **Memory** → 选择堆类型 → **Take Snapshot**
2. 点击快照 → 对比 / 搜索对象 / 分析 retainers

### 使用 Chrome 录制 CPU Profile

1. DevTools → **Performance** → **Record** (或 **Profiler** → **Start**)
2. 执行要分析的操作 → **Stop**
3. 查看火焰图，定位热点函数

### 远程调试 Web/Node 同一端口

Node 18+ 支持 `--inspect` 同时接受浏览器和 CDP 客户端：

```bash
node --inspect=0.0.0.0:9229 server.js
# Chrome DevTools (chrome://inspect) 和 node inspect 可同时连接
```

### Edge DevTools

Microsoft Edge (基于 Chromium) 同样支持 `edge://inspect`，连接方式与 Chrome 完全一致。

---

## 3. VS Code 调试配置 (VS Code Debugging Configuration)

### launch.json 基本模板

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "type": "node",
      "request": "launch",
      "name": "Launch Program",
      "runtimeExecutable": "node",
      "runtimeArgs": ["--inspect-brk", "${workspaceFolder}/path/to/script.js"],
      "skipFiles": ["<node_internals>/**"]
    },
    {
      "type": "node",
      "request": "attach",
      "name": "Attach to Process",
      "port": 9229,
      "restart": true,
      "skipFiles": ["<node_internals>/**"]
    }
  ]
}
```

### 完整示例（包含环境变量、参数、工作目录）

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "type": "node",
      "request": "launch",
      "name": "Debug Server",
      "runtimeExecutable": "node",
      "runtimeArgs": [
        "--inspect-brk",
        "--enable-source-maps",
        "--import", "tsx"
      ],
      "program": "${workspaceFolder}/src/server.ts",
      "env": {
        "NODE_ENV": "development",
        "DEBUG": "app:*"
      },
      "cwd": "${workspaceFolder}",
      "console": "integratedTerminal",
      "skipFiles": ["<node_internals>/**", "node_modules/tsx/**"]
    },
    {
      "type": "node",
      "request": "attach",
      "name": "Attach to Running",
      "port": 9229,
      "restart": true,
      "resolveSourceMapLocations": [
        "${workspaceFolder}/**",
        "!**/node_modules/**"
      ]
    }
  ]
}
```

### TypeScript (tsx) 调试配置

```json
{
  "type": "node",
  "request": "launch",
  "name": "Debug TSX",
  "runtimeExecutable": "node",
  "runtimeArgs": [
    "--inspect-brk",
    "--import", "tsx"
  ],
  "program": "${workspaceFolder}/src/app.tsx",
  "outFiles": ["${workspaceFolder}/dist/**/*.js"],
  "sourceMaps": true,
  "skipFiles": ["<node_internals>/**"]
}
```

### Vitest 测试调试

```json
{
  "type": "node",
  "request": "launch",
  "name": "Debug Vitest",
  "runtimeExecutable": "node",
  "runtimeArgs": [
    "--inspect-brk",
    "./node_modules/vitest/vitest.mjs",
    "run",
    "--no-file-parallelism",
    "${file}"
  ],
  "skipFiles": ["<node_internals>/**"],
  "console": "integratedTerminal"
}
```

### Nodemon 调试

```json
{
  "type": "node",
  "request": "launch",
  "name": "Debug with Nodemon",
  "runtimeExecutable": "npx",
  "runtimeArgs": ["nodemon", "--inspect-brk", "--exec", "node", "${workspaceFolder}/src/server.js"],
  "restart": true,
  "skipFiles": ["<node_internals>/**"]
}
```

### 条件断点配置

在 `.vscode/launch.json` 中使用 `condition`：

```json
{
  "type": "node",
  "request": "launch",
  "name": "Conditional Breakpoint",
  "runtimeExecutable": "node",
  "runtimeArgs": ["--inspect-brk", "${workspaceFolder}/script.js"],
  "breakpoints": [
    {
      "file": "${workspaceFolder}/src/app.js",
      "line": 42,
      "condition": "userId === 42 && typeof error !== 'undefined'"
    }
  ]
}
```

### 调试运行中的进程（通过进程 ID）

```json
{
  "type": "node",
  "request": "attach",
  "name": "Attach by PID",
  "processId": "${command:pickProcess}",
  "port": 9229
}
```

### 常用 VS Code Debug 快捷键

| 快捷键 | 作用 |
|---|---|
| `F5` | 开始调试 |
| `F9` | 切换断点 |
| `F10` | Step Over |
| `F11` | Step Into |
| `Shift+F11` | Step Out |
| `Shift+F5` | 停止调试 |
| `Ctrl+Shift+F5` | 重新开始 |

### 常见 launch.json 问题

- **断点变灰（unbound）**: 确认 `outFiles` 正确指向编译后的 JS，或启用 `sourceMaps`
- **Attach 失败**: 确认目标进程用 `--inspect` 启动，且端口未被防火墙拦截
- **TypeScript 断点不命中**: 使用 `runtimeArgs: ["--enable-source-maps"]` 并设置正确的 `outFiles`

---

## 4. 常见问题排查 (Troubleshooting Guide)

### Q1: 断点命中但行号不对（指向错误的行）

**原因**: Source map 未正确加载，或断点打在编译后的 JS 而非源 TS。

**排查步骤**:
```bash
# 确认 Node 正确处理 source-map
node --enable-source-maps --inspect-brk script.ts

# VS Code: 检查 outFiles 配置
# "outFiles": ["${workspaceFolder}/dist/**/*.js"]

# Chrome DevTools: 检查是否勾选 "Enable source maps"
```

**修复**:
```bash
# tsx 自带 source-map，通常无需额外配置
node --inspect-brk --import tsx script.ts

# ts-node 可能需要显式启用
node --inspect-brk -r ts-node/register --enable-source-maps script.ts
```

---

### Q2: Attach 成功但断点不命中

**可能原因**:
1. 断点设置在代码执行完之后才 attach
2. 子进程没有继承 `--inspect`
3. 断点所在代码路径未执行

**排查步骤**:
```bash
# 确认进程确实在监听
curl -s http://127.0.0.1:9229/json/list | jq '.[].title'

# 查看当前所有断点状态
# Chrome DevTools → Sources → 右键 → Breakpoints → 查看是否 enabled

# 确认断点所在函数是否被调用
# 在函数入口加一个日志: console.log('fn called')
```

**修复**:
```bash
# 使用 --inspect-brk 确保在首行暂停
node --inspect-brk script.js

# 如果是 child process
NODE_OPTIONS='--inspect-brk' node cluster.js
```

---

### Q3: 端口被占用 (EADDRINUSE)

```bash
# 查看哪个进程占用了 9229
lsof -i :9229        # macOS/Linux
netstat -ano | findstr :9229   # Windows

# 使用随机端口
node --inspect=0 script.js
# 然后从 /json/list 获取实际端口
curl -s http://127.0.0.1:9229/json/list | jq -r '.[0].webSocketDebuggerUrl'
```

---

### Q4: Windows 上 `node inspect` 无法连接

Windows 上 Node 的 `--inspect` 使用命名管道而非 TCP。`node inspect` 需要 Windows 10+ 且 Node 12+：

```powershell
# 确认 Node 版本
node --version  # 需要 >= 12

# 以管理员权限打开 PowerShell
```

**备选方案** — 使用 PowerShell远程端口转发：
```powershell
# 在本机建立端口转发到远程 Node
netsh interface portproxy add v4tov4 listenport=9229 connectport=9229 connectaddress=<远程IP>
```

---

### Q5: SIGUSR1 不生效

**可能原因**: 进程不是 Node，或 Node 编译时未包含 inspector。

**排查**:
```bash
# 确认是 Node 进程
ps aux | grep node

# 查看进程支持的信号
kill -l  # SIGUSR1 应该在列表中
```

**备选** — 重新启动带 `--inspect`：
```bash
# 找到 PID 后
kill <pid>
node --inspect-brk script.js &
```

---

### Q6: DevTools 能打开但无法看到源码

**原因**: DevTools 加载了错误的目标（多个 Node 进程）。

```bash
# 列出所有 targets，找到正确的那个
curl -s http://127.0.0.1:9229/json/list

# 点击 DevTools 中的正确 target，而非手动输入 URL
```

---

### Q7: `NODE_OPTIONS='--inspect'` 导致无限循环

当通过 `NODE_OPTIONS` 注入 inspect 到集群 master，再 fork workers 时，workers 可能各自尝试监听同一端口：

```bash
# 正确方式：只在 master 监听，子进程通过 IPC 通信
# cluster.js
if (cluster.isMaster) {
  cluster.fork();  // workers 不继承 inspect
}
```

如果确实需要调试 worker，用不同端口：
```bash
NODE_OPTIONS='--inspect=0.0.0.0:9229' node master.js
# workers 继承但自动递增端口
```

---

### Q8: Vitest 并行测试只跑一个 worker

调试时不希望 vitest 并行化：
```bash
npx vitest run --no-file-parallelism --reporter=verbose src/app.test.ts
```

---

### Q9: Node 18+ DevTools 自动关闭

某些 Docker 环境或 VS Code Remote 下 DevTools 连接不稳定：

```bash
# 增加超时
curl -s http://127.0.0.1:9229/json
# 如果返回为空，确认容器网络和端口映射
```

---

### Q10: 进程已退出，断点没命中

**原因**: attach 太晚，进程已执行完毕。

**修复**:
```bash
# 1. 使用 --inspect-brk 在首行暂停
node --inspect-brk script.js

# 2. 在入口加 setTimeout 等待 debugger attach
setTimeout(() => {
  debugger;  // 触发断点
  // your code
}, 5000);
```

---

### 快速诊断流程图

```
进程启动正常？
├── 否 → 检查 NODE_OPTIONS、环境变量、package.json scripts
└── 是 → curl http://127.0.0.1:9229/json/list 返回数据？
         ├── 否 → 进程未监听 inspect，检查 --inspect 是否传入
         └── 是 → DevTools / VS Code 连接成功？
                  ├── 否 → 端口/网络问题，确认防火墙/端口映射
                  └── 是 → 断点是否命中？
                           ├── 否 → 代码路径是否执行？是否在正确的文件/行？
                           │    └── 使用 console.log 确认函数被调用
                           └── 是 → 调试愉快！
```

## Verification Checklist

After setting up a debug session, verify:

- [ ] `curl -s http://127.0.0.1:9229/json/list` returns exactly the target you expect
- [ ] First breakpoint actually hits (if it doesn't, you likely missed `--inspect-brk` or attached after execution completed)
- [ ] Source listing at pause shows the right file (mismatch = sourcemap issue, see pitfall 1)
- [ ] `exec process.pid` in `repl` returns the PID you meant to attach to
