# npm China Mirror (国内加速)

当 `npm install` 在 Hermes Dashboard (`web/`) 或其他 Node.js 项目上下载依赖太慢时，用淘宝镜像：

## 临时换源

```bash
npm install --registry=https://registry.npmmirror.com
```

## 永久换源

```bash
npm config set registry https://registry.npmmirror.com
# 验证
npm config get registry
# → https://registry.npmmirror.com
```

## 走本地代理（如果 Shadowrocket 或 Clash Verge 已开启）

```bash
npm config set proxy http://127.0.0.1:1082
npm config set https-proxy http://127.0.0.1:1082
```

清理代理：

```bash
npm config delete proxy
npm config delete https-proxy
```

## ⚠️ npm ci 慢的真正瓶颈：camoufox-js 浏览器二进制下载

即使换了快速镜像（npmmirror 0.1s），`npm ci` 仍然可能很慢，因为：

- `camoufox-js postinstall` 会下载 Chromium 浏览器二进制文件（~200MB+）
- 这是 `npm ci` 最耗时的阶段

诊断方法：
```bash
# 看进程：如果 npm ci 在跑但 registry 不是问题，检查是什么在下载
ps aux | grep -E "camoufox|playwright|chromium" | grep -v grep
```

**解决方法：使用 pnpm 代替 npm**

pnpm 比 npm ci 快得多（并行下载 + 全局内容寻址缓存，后续重装几乎秒杀）：

```bash
# 安装 pnpm（如果未安装）
npm install -g pnpm

# 在 Hermes Agent 项目中使用（删除旧的 node_modules + lockfile 再装）
cd ~/.hermes/hermes-agent
rm -rf node_modules package-lock.json
pnpm install

# 后续更新只需
pnpm install
```

## 什么时候用

- Hermes Dashboard 首次构建：`cd ~/.hermes/hermes-agent/web && npm install`（或 pnpm install）
- Hermes Agent 全量 Node.js 依赖（含 browser tools）：推荐用 pnpm
- 任何 Node.js 项目的依赖安装
- 在 Hermes 技能脚本中需要装 npm 包时
