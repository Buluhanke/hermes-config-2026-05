---
name: terminal-backend-guide
description: "terminal后端 docker与local行为边界装包差异。Use when terminal装不上包行为异常"
triggers:
  - terminal.backend
  - colima
  - 工具找不到
---

# Terminal Backend 行为边界

## 两种 Backend

| Backend | 执行位置 | macOS 文件系统 |
|---------|---------|--------------|
| `local` | macOS 宿主机 | ✅ 可见 |
| `docker` | Colima Linux VM | ❌ 隔离 |

当前配置 `terminal.backend: docker`（~/.hermes/config.yaml）。

## 关键边界

**docker backend ≠ macOS**：
- macOS 文件 `/Users/aimac/` 不可直接访问
- Homebrew 不可用
- 在 Colima 里装的工具对用户 Terminal.app 不可见

**能用 docker backend 做**：
- Docker pull/run/build（Colima = Docker runtime）
- Linux 二进制工具（pandoc、yq）
- 容器内隔离测试

## 给 macOS 装工具

用 `computer_use` 在 Terminal.app 里执行 curl 命令。需 macOS 审批权限。

## Colima 自启动

Mac 重启后需重跑：
```
colima start --runtime docker --cpu 2 --memory 4
```
加入 crontab `@reboot` 或 macOS Login Items。

## 自检：确认当前 terminal 在哪个环境

当你怀疑 terminal 在 Docker 还是 Mac 本地时，立即执行：

```bash
uname -a && echo "---" && hostname && echo "---" && ls ~/.hermes/config.yaml 2>&1
```

**如果 hostname 是容器ID（如 `96657494a0bb`）且 `~/.hermes/config.yaml` 不存在** → `terminal` 活在 Docker 里，碰不到 Mac 文件。

**如果 hostname 是 `Mac-mini` 或 `aimac` 且 config 存在** → `terminal` 在 Mac 本地，所有文件可见。

---

## Docker Hub 国内镜像

```bash
mkdir -p ~/.colima/default
cat > ~/.colima/default/docker.json << 'EOF'
{"registry-mirrors": ["https://docker.mirrors.ustc.edu.cn"]}
EOF
colima stop && colima start --runtime docker
```
验证：`docker run --rm hello-world`

## pandoc / yq 安装（Colima VM）

```bash
# pandoc
curl -L "https://github.com/jgm/pandoc/releases/download/3.10.2/pandoc-3.10.2-linux-arm64.tar.gz" -o /tmp/pandoc.tar.gz
tar xzf /tmp/pandoc.tar.gz -C /tmp
cp /tmp/pandoc-3.10.2/bin/pandoc /usr/local/bin/
cp /tmp/pandoc-3.10.2/bin/pandoc-server /usr/local/bin/

# yq
curl -sL "https://github.com/mikefarah/yq/releases/download/v4.53.3/yq_linux_arm64.tar.gz" -o /tmp/yq.tar.gz
tar xzf /tmp/yq.tar.gz -C /tmp
mv /tmp/yq_linux_arm64 /usr/local/bin/yq
```
