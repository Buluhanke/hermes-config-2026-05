#!/bin/bash
# M4 Mac 内存清理脚本
# 停止 Docker Desktop Linux VM + Ollama，释放 ~6.5GB 内存

set -e

echo "=== 停止 Ollama ==="
pkill -f 'ollama' 2>/dev/null && echo "Ollama 已停" || echo "Ollama 未运行"

echo "=== 停止所有 Docker 容器 ==="
docker stop $(docker ps -q) 2>/dev/null && echo "容器已停止" || echo "无运行中容器"

echo "=== 退出 Docker Desktop ==="
osascript -e 'quit app "Docker Desktop"' 2>/dev/null && echo "Docker Desktop 已退出" || echo "Docker Desktop 未运行"

sleep 2

echo "=== 验证内存 ==="
top -l 1 | grep PhysMem
