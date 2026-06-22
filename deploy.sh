#!/bin/bash
set -e

echo "==================================="
echo "🚀 开始部署 Audio Hub"
echo "==================================="

# 1. 拉取最新代码 (前提是你已经 clone 过并配置好 git)
echo "📦 正在从 GitHub 拉取最新代码..."
git pull origin main

# 2. 重新构建并启动 Docker 容器
echo "🐳 正在重新构建并启动容器..."
docker compose up -d --build

# 3. 清理无用的镜像 (可选，防止服务器磁盘爆满)
echo "🧹 正在清理悬空镜像..."
docker image prune -f

echo "==================================="
echo "✅ 部署完成！"
echo "👉 前端访问: http://<你的服务器IP>:8501"
echo "👉 后端访问: http://<你的服务器IP>:8000/docs"
echo "==================================="
