#!/bin/bash

# Docker 镜像构建脚本 - 包含错误处理和多种构建选项
set -e  # 遇到错误时退出

echo "🐳 开始构建 Docker 镜像..."

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ 错误: Docker 未运行，请启动 Docker"
    exit 1
fi

# 可选：使用更新的依赖文件
if [ -f "requirements_updated.txt" ]; then
    echo "📦 检测到更新的依赖文件，将使用 requirements_updated.txt"
    cp requirements_updated.txt requirements.txt
fi

# 清理旧的构建缓存（可选）
if [ "$1" = "--no-cache" ]; then
    echo "🧹 清理构建缓存..."
    CACHE_FLAG="--no-cache"
else
    CACHE_FLAG=""
fi

# 选择 Dockerfile
if [ "$1" = "--alpine" ]; then
    echo "🏔️ 使用 Alpine Linux 版本构建..."
    DOCKERFILE="Dockerfile.alpine"
    IMAGE_TAG="patient-infos-realtime-v0.1.0-alpine"
else
    echo "🐧 使用 Debian 版本构建..."
    DOCKERFILE="Dockerfile"
    IMAGE_TAG="patient-infos-realtime-v0.1.0"
fi

echo "📋 构建参数:"
echo "  - 架构: linux/amd64"
echo "  - Dockerfile: $DOCKERFILE"
echo "  - 镜像标签: $IMAGE_TAG"
echo "  - 缓存选项: $CACHE_FLAG"

# 开始构建
echo ""
echo "🔨 开始构建镜像..."
docker build \
    --platform linux/amd64 \
    -f "$DOCKERFILE" \
    -t "$IMAGE_TAG" \
    $CACHE_FLAG \
    .

# 检查构建是否成功
if [ $? -eq 0 ]; then
    echo "Docker 镜像构建成功!"
    
    # 设置目标目录
    TARGET_DIR="/Users/fabivs/myfile/yunlan/images"
    
    # 创建目标目录（如果不存在）
    mkdir -p "$TARGET_DIR"
    
    # 生成时间戳
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    
    # 设置压缩包文件名（使用实际的镜像标签）
    TAR_FILE="$TARGET_DIR/${IMAGE_TAG}_${TIMESTAMP}.tar.gz"
    
    echo "正在导出 Docker 镜像到: $TAR_FILE"
    
    # 导出 Docker 镜像并压缩
    docker save "$IMAGE_TAG" | gzip > "$TAR_FILE"
    
    # 检查导出是否成功
    if [ $? -eq 0 ]; then
        echo "镜像已成功导出到: $TAR_FILE"
        echo "文件大小: $(du -h "$TAR_FILE" | cut -f1)"
    else
        echo "镜像导出失败!"
        exit 1
    fi
else
    echo "Docker 镜像构建失败!"
    exit 1
fi
