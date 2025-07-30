# Docker 构建指南

## 🚨 问题解决

你遇到的 GPG 签名错误已经被修复了！现在有两种构建选项可用。

## 🛠️ 构建选项

### 1. 标准构建（推荐）
使用修复后的 Debian 基础镜像：
```bash
./docker-build.sh
```

### 2. Alpine 构建（备用方案）
如果标准构建仍有问题，使用 Alpine Linux：
```bash
./docker-build.sh --alpine
```

### 3. 清理缓存构建
如果遇到缓存相关问题：
```bash
./docker-build.sh --no-cache
```

## 🔧 修复的问题

### GPG 签名错误
**原问题**: `At least one invalid signature was encountered`

**解决方案**:
- 添加了 `--allow-releaseinfo-change` 参数
- 安装了必要的 GPG 验证包
- 添加了更好的缓存清理

### 优化改进
- ✅ 更好的错误处理
- ✅ 多种基础镜像选择
- ✅ 智能依赖文件选择
- ✅ 详细的构建日志
- ✅ 自动镜像导出和压缩

## 📦 构建产物

成功构建后，你将得到：

1. **Docker 镜像**:
   - `patient-infos-realtime-v0.1.0` (Debian版)
   - `patient-infos-realtime-v0.1.0-alpine` (Alpine版)

2. **压缩包** (自动保存到 `/Users/fabivs/myfile/yunlan/images/`):
   - `patient-infos-realtime-v0.1.0_YYYYMMDD_HHMMSS.tar.gz`
   - `patient-infos-realtime-v0.1.0-alpine_YYYYMMDD_HHMMSS.tar.gz`

## 🆘 故障排除

### 常见问题

#### 1. Docker 未运行
```
❌ 错误: Docker 未运行，请启动 Docker
```
**解决**: 启动 Docker Desktop

#### 2. 网络问题
如果仍遇到网络问题，尝试：
```bash
# 清理 Docker 系统
docker system prune -f

# 使用备用构建方案
./docker-build.sh --alpine
```

#### 3. 依赖安装失败
```bash
# 使用清理缓存构建
./docker-build.sh --no-cache
```

#### 4. 权限问题
```bash
# 确保脚本有执行权限
chmod +x docker-build.sh
```

### 高级故障排除

#### 手动构建（调试用）
```bash
# 使用 Debian 版本
docker build --platform linux/amd64 -t patient-infos-realtime-debug -f Dockerfile .

# 使用 Alpine 版本
docker build --platform linux/amd64 -t patient-infos-realtime-debug -f Dockerfile.alpine .
```

#### 交互式调试
```bash
# 进入容器调试
docker run -it --entrypoint /bin/bash patient-infos-realtime-v0.1.0

# Alpine 版本使用 sh
docker run -it --entrypoint /bin/sh patient-infos-realtime-v0.1.0-alpine
```

## 📊 性能对比

| 特性 | Debian (标准) | Alpine (备用) |
|------|---------------|---------------|
| 镜像大小 | ~500MB | ~200MB |
| 构建时间 | 中等 | 较快 |
| 兼容性 | 最佳 | 良好 |
| 推荐场景 | 生产环境 | 资源受限环境 |

## 🎯 下一步

构建成功后：

1. **测试镜像**:
```bash
docker run -d -p 7700:7700 patient-infos-realtime-v0.1.0
curl http://localhost:7700/health
```

2. **部署使用**:
```bash
# 加载镜像（在其他机器上）
docker load < patient-infos-realtime-v0.1.0_YYYYMMDD_HHMMSS.tar.gz
```

3. **更新依赖** (可选):
```bash
# 如果需要使用最新依赖
cp requirements_updated.txt requirements.txt
./docker-build.sh
```

## 📞 技术支持

如果问题持续存在：
1. 检查 Docker 版本: `docker --version`
2. 检查系统资源是否充足
3. 尝试重启 Docker
4. 查看详细错误日志

---
**更新时间**: 2024年12月  
**维护者**: 开发团队 