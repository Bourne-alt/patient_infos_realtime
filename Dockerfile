FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

# 修复GPG密钥问题并安装系统依赖
# RUN apt-get clean && \
#     rm -rf /var/lib/apt/lists/* && \
#     apt-get update --allow-releaseinfo-change --allow-unauthenticated && \
#     apt-get install -y --no-install-recommends --allow-unauthenticated \
#         build-essential \
#         libpq-dev \
#         curl \
#         ca-certificates && \
#     apt-get clean && \
#     rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# 升级pip并安装Python依赖管理工具
RUN pip install --upgrade pip setuptools wheel

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖（使用缓存优化）
RUN pip install --no-cache-dir --compile -r requirements.txt

# 复制应用代码
COPY . .

# 创建非root用户（安全最佳实践）
RUN adduser --disabled-password --gecos '' --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7700/health')" || exit 1

# 暴露端口
EXPOSE 7700

# 启动命令 - 使用优化的配置
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "7700", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--access-log"] 