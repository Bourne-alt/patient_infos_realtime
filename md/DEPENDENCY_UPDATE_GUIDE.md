# 依赖包更新指南

## 📋 更新概览

本文档说明了 `patient_infos_realtime` 项目中依赖包的更新情况和迁移步骤。

## 🚨 重大变更警告

### LangChain v0.3 升级
- **重大版本升级**: 从 `0.1.x` 升级到 `0.3.x`
- **Pydantic 升级**: 内部从 Pydantic v1 升级到 Pydantic v2
- **潜在破坏性变更**: 需要代码审查和测试

## 📦 主要依赖更新

### Web 框架
- `fastapi`: 0.104.1 → 0.115.6
- `uvicorn`: 0.24.0 → 0.32.1
- `pydantic`: 2.4.2 → 2.10.4

### LangChain 生态系统
- `langchain`: 0.1.0 → 0.3.14
- `langchain-core`: 0.1.0 → 0.3.28
- `langchain-community`: 0.0.10 → 0.3.13
- `langchain-openai`: 0.0.5 → 0.2.14
- `langchain-experimental`: 0.0.49 → 0.3.7

### AI/ML 相关
- `openai`: 1.6.1 → 1.58.1
- `tiktoken`: 0.5.2 → 0.8.0

### 数据库
- `sqlalchemy`: 2.0.21 → 2.0.36
- `psycopg2-binary`: 2.9.7 → 2.9.10

## 🔄 迁移步骤

### 1. 备份当前代码
```bash
git add .
git commit -m "Backup before dependency updates"
git branch backup-before-deps-update
```

### 2. 更新依赖
```bash
# 使用更新后的 requirements 文件
cp requirements_updated.txt requirements.txt
pip install -r requirements.txt
```

### 3. LangChain v0.3 迁移要点

#### 3.1 Pydantic 导入更新
**旧版本:**
```python
from langchain_core.pydantic_v1 import BaseModel
from langchain.pydantic_v1 import validator
```

**新版本:**
```python
from pydantic import BaseModel, field_validator
```

#### 3.2 工具定义更新
**旧版本:**
```python
from langchain.tools import Tool
```

**新版本:**
```python
from langchain_core.tools import tool
```

#### 3.3 链式操作更新
**旧版本:**
```python
from langchain.chains import LLMChain
```

**新版本:**
```python
# 使用 LCEL (LangChain Expression Language)
from langchain_core.runnables import RunnablePassthrough
```

## 🛠️ Dockerfile 优化

### 新增功能
- **Python 版本**: 升级到 3.11-slim
- **安全性**: 添加非root用户
- **健康检查**: 添加容器健康监控
- **构建优化**: 改进缓存和编译选项

### 环境变量优化
- 添加 `PYTHONDONTWRITEBYTECODE=1` 防止.pyc文件
- 优化 uvicorn 启动参数

## 🧪 测试建议

### 1. 单元测试
```bash
python -m pytest tests/ -v
```

### 2. API 测试
```bash
# 启动服务
uvicorn api:app --host 0.0.0.0 --port 7700

# 测试健康检查
curl http://localhost:7700/health
```

### 3. LangChain 功能测试
- 测试所有 LangChain 相关的 API 端点
- 验证 OpenAI 集成
- 检查数据库连接

## ⚠️ 可能遇到的问题

### 1. Pydantic v2 兼容性
**问题**: `ValidationError` 格式变更
**解决**: 更新错误处理逻辑

### 2. LangChain 导入错误
**问题**: 模块路径变更
**解决**: 使用新的导入路径

### 3. 类型注解问题
**问题**: Pydantic v2 的类型检查更严格
**解决**: 更新类型注解

## 🔧 生产部署注意事项

### 1. 渐进式部署
- 在测试环境充分验证
- 考虑蓝绿部署策略
- 准备回滚方案

### 2. 监控指标
- API 响应时间
- 错误率
- 内存使用情况
- LangChain 调用延迟

### 3. 性能调优
```bash
# 推荐的 uvicorn 启动参数
uvicorn api:app \
  --host 0.0.0.0 \
  --port 7700 \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --access-log \
  --timeout-keep-alive 30
```

## 📚 参考资源

- [LangChain v0.3 迁移指南](https://python.langchain.com/docs/versions/v0_3/)
- [Pydantic v2 迁移指南](https://docs.pydantic.dev/2.0/migration/)
- [FastAPI 更新日志](https://fastapi.tiangolo.com/release-notes/)

## 🆘 故障排除

如果遇到问题，请：
1. 检查错误日志
2. 验证环境变量设置
3. 确认 API 密钥有效性
4. 检查数据库连接

---

**更新时间**: 2024年12月
**维护者**: 开发团队 