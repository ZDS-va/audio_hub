#!/bin/bash
set -e

echo "==================================="
echo "🚀 开始部署 Audio Hub"
echo "==================================="

# 0. 深度清理系统空间 (防止 Docker 空间不足)
echo "🧹 正在深度清理 Docker 缓存以释放磁盘空间..."
docker system prune -a -f --volumes
# 可选：如果你确定之前的 builder 缓存没用，可以开启下面这句
# docker builder prune -a -f

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
