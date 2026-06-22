#!/bin/bash
set -e

echo "==================================="
echo "🚀 开始部署 Audio Hub"
echo "==================================="

# 0. 清理悬空的无用镜像和停止的容器 (保留缓存，加快下次构建速度)
echo "🧹 正在清理无用镜像和缓存..."
docker container prune -f
docker image prune -f
# 如果真的遇到空间不足，再手动执行 docker system prune -a -f --volumes

# 1. 拉取最新代码
echo "📦 正在从 GitHub 拉取最新代码..."
git pull origin main

# 2. 重新构建并启动 Docker 容器
echo "🐳 正在重新构建并启动容器..."
docker compose up -d --build

echo "==================================="
echo "✅ 部署完成！"
echo "👉 前端访问: http://106.54.14.120:8502"
echo "👉 后端访问: http://106.54.14.120:8002/docs"
echo "==================================="
