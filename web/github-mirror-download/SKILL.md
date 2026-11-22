---
name: github-mirror-download
description: GitHub下载慢/0字节限速时多镜像加速。Use when 下release/源码/raw失败
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [GitHub, mirror, download, network]
    category: web
triggers:
  - GitHub下载慢
  - release下载失败
  - 0字节限速
  - 镜像加速
  - 下载github资源
  - github download
---

# GitHub 多镜像智能下载

从 Komi Store (github.com/komi-store/komi-store) 逆向提炼的镜像加速能力，做成零依赖 CLI。
**核心：GitHub 网络不稳定/0字节限速时，用它替代裸 curl 或单一 gh-proxy。**

## When to Use

下载任何 GitHub 大文件时默认就走它（尤其 release 资产、源码 tarball）；裸 curl 慢、卡 0 字节、报 network unreachable、单一 gh-proxy 失效时必用。找仓库/读 API 仍用 gh CLI。

## 工具

`~/.hermes/scripts/gh_download.py`（纯 stdlib，零 LLM，零 GUI，可 subprocess 直接调）

```bash
# 下载（自动选最快可用镜像 + 失败 fallback + 断点续传）
python3 ~/.hermes/scripts/gh_download.py <url> -o ~/Downloads/file.dmg

# 现场测速镜像（更准但慢，约10-20s）
python3 ~/.hermes/scripts/gh_download.py <url> -o out.bin --probe

# 只看当前镜像健康状态
python3 ~/.hermes/scripts/gh_download.py --list
```

## 策略（复刻 Komi 的 4 层逻辑）

1. **动态镜像目录**：`https://api.github-store.org/v1/mirrors/list` 拉 Komi 实时维护的镜像 status + latency。失败则用内置 7 个镜像兜底。
2. **按延迟排序 + 跳过 down**：目录里 status=down 的排最后，快的优先。
3. **镜像优先 + 直连 fallback**：每个镜像试 `--tries` 次（默认2），全失败退回直连。
4. **断点续传**：`curl -C -` 配合重试，对抗 objects.githubusercontent.com 的 0 字节限速。

## 镜像模板分类（关键）

- **release 资产**（github.com/*/releases/download/* 或 objects.githubusercontent.com）：走 `{url}` 模板 → ghfast.top / gh-proxy.com / moeyy.xyz / ghps.cc / 99988866。
- **raw 文件**（raw.githubusercontent.com）：额外支持 fastly.jsdelivr（48ms 最快，模板 `{owner}/{repo}@{ref}/{path}`），但**只对 raw 有效**，release 资产会被跳过。

## 实测记录（2026-11-22）

- Komi 目录实时状态：direct 101ms / fastly_jsdelivr 48ms / ghfast_top 1032ms 可用；moeyy / gh-proxy / ghps / 99988866 全 down。
- raw README 测试 → fastly_jsdelivr 一击命中，内容正确。
- release checksums.txt 测试 → ghfast_top 命中，1971 bytes / 21 行完整。
- **大文件对比（15MB tar.gz）**：裸 curl 直连 CDN 15 秒仅下 3MB（200KB/s，超时中断）；本工具走 ghfast_top **11.6 秒下完整个 15,050,573 bytes**，tar tzf 校验通过。提速约 6 倍且不超时。

## 何时用

- 下 GitHub release 资产（dmg/exe/zip/tar.gz）慢或卡 0 字节 → 用它。
- 下源码 tarball、raw 文件 → 用它。
- **注意**：找仓库/读文件仍用 `gh` CLI / `gh api`（api.github.com 稳定）；本工具只管**下载大文件**。
- GitHub API/搜索不需要镜像（gh api 走 api.github.com 一直稳定）。

## 边界

- Komi Store 本身是纯 GUI，无 CLI/API/MCP（本地 47632 端口拒所有外部请求），**无法被 agent 直接驱动**。本脚本是把它的加速逻辑抽出来复用，不依赖 Komi 运行。
- 镜像目录 API 若返回过期状态（显示 ok 但实际 404），靠 fallback 链兜底。
