#!/bin/bash

# 医疗报告分析API启动脚本

echo "=================================="
echo "医疗报告分析API启动脚本"
echo "=================================="

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "错误: Docker未安装，请先安装Docker"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "错误: Docker Compose未安装，请先安装Docker Compose"
    exit 1
fi

# 创建日志目录
mkdir -p logs

# 设置权限
chmod +x start.sh

echo "正在启动医疗报告分析API..."

# 构建并启动服务
docker-compose up -d

# 等待服务启动
echo "等待服务启动..."
sleep 10

# 检查服务状态
if docker-compose ps | grep -q "Up"; then
    echo "✅ 医疗报告分析API启动成功!"
    echo ""
    echo "服务信息:"
    echo "- API地址: http://localhost:7700"
    echo "- 健康检查: http://localhost:7700/health"
    echo "- API文档: http://localhost:7700/docs"
    echo "- 数据库: PostgreSQL (localhost:5432)"
    echo ""
    echo "查看日志: docker-compose logs -f medical-report-api"
    echo "停止服务: docker-compose down"
else
    echo "❌ 服务启动失败，请检查日志:"
    docker-compose logs
    exit 1
fi 