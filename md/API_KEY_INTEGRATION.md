# API Key 集成说明

## 概述

本文档说明了医疗报告分析API中大模型API key的配置和使用方法。系统支持多种大模型API提供商，包括OpenAI、本地Ollama以及其他兼容的API服务。

## 环境变量配置

### 必需的环境变量

```bash
# 大模型API配置
OPENAI_API_BASE=https://api.openai.com/v1/chat/completions  # API端点
OPENAI_MODEL=gpt-3.5-turbo                                  # 模型名称
OPENAI_API_KEY=sk-your-actual-api-key-here                 # API密钥
```

### 支持的配置示例

#### 1. OpenAI官方API
```bash
OPENAI_API_BASE=https://api.openai.com/v1/chat/completions
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_API_KEY=sk-your-openai-api-key
```

#### 2. 本地Ollama服务
```bash
OPENAI_API_BASE=http://localhost:11434/api/generate
OPENAI_MODEL=llama3.1
OPENAI_API_KEY=sk-proj-1234567890  # 默认占位符，不会添加到请求头
```

#### 3. 其他兼容API服务
```bash
OPENAI_API_BASE=https://your-api-provider.com/v1/chat/completions
OPENAI_MODEL=your-model-name
OPENAI_API_KEY=your-api-key
```

## API Key 处理逻辑

### 1. 智能API Key检测
系统会自动检测API key的配置状态：

```python
# 如果API key存在且不是默认占位符，则添加到请求头
if LLM_API_KEY and LLM_API_KEY != "sk-proj-1234567890":
    headers["Authorization"] = f"Bearer {LLM_API_KEY}"
```

### 2. 三种配置状态

| 状态 | 描述 | 行为 |
|------|------|------|
| `configured` | 设置了真实的API key | 添加Authorization头 |
| `default_placeholder` | 使用默认占位符 | 不添加Authorization头 |
| `not_configured` | 未设置API key | 不添加Authorization头 |

## 安全性考虑

### 1. API Key保护
- API key在日志中会被遮蔽显示
- 健康检查API不会完整显示API key
- 环境变量应使用`.env`文件管理

### 2. 最佳实践
```bash
# .env 文件示例
OPENAI_API_KEY=sk-your-secret-key-here

# 确保 .env 文件不被提交到版本控制
echo ".env" >> .gitignore
```

## 健康检查

### 健康检查端点返回示例
```json
{
    "status": "healthy",
    "database": "connected",
    "llm_api": "connected",
    "api_key": "configured",
    "langchain_analyzer": "initialized",
    "llm_model": "gpt-3.5-turbo",
    "llm_url": "https://api.openai.com/v1/chat/completions",
    "timestamp": "2025-01-XX..."
}
```

### API Key状态解释
- `configured`: API key已正确配置
- `default_placeholder`: 使用默认测试key
- `not_configured`: 未配置API key

## 测试验证

### 运行测试脚本
```bash
cd patient_infos_realtime
python test_api_key_integration.py
```

### 测试内容
1. **环境变量检查**: 验证API key配置
2. **请求头测试**: 确认Authorization头正确添加
3. **健康检查**: 验证API状态显示
4. **模拟调用**: 测试完整的API调用流程

## 故障排除

### 常见问题

#### 1. API调用失败
```bash
# 检查API key是否正确设置
echo $OPENAI_API_KEY

# 测试API连接
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     -H "Content-Type: application/json" \
     $OPENAI_API_BASE
```

#### 2. 无法添加Authorization头
- 确认API key不是默认占位符 `sk-proj-1234567890`
- 检查环境变量是否正确设置
- 重启应用服务

#### 3. 权限或额度问题
- 验证API key是否有效
- 检查API额度是否充足
- 确认模型访问权限

## 开发注意事项

### 1. 不同API提供商的适配
```python
# 根据API提供商调整请求格式
if "openai.com" in LLM_API_URL:
    # OpenAI格式
    payload = {"model": model, "messages": [...]}
elif "localhost:11434" in LLM_API_URL:
    # Ollama格式  
    payload = {"model": model, "prompt": "..."}
```

### 2. 错误处理
- 401: API key无效或过期
- 403: 权限不足或额度不足
- 429: 请求频率限制
- 500: 服务器错误

### 3. 日志记录
系统会记录：
- API key配置状态（不包含实际key值）
- 请求成功/失败状态
- 错误信息和调试信息

## 配置文件示例

创建 `.env` 文件：
```bash
cp env_example_with_api_key.txt .env
# 编辑 .env 文件，设置真实的API key
```

## 总结

API key集成提供了灵活的大模型API访问方式，支持多种服务提供商，并包含完善的安全机制和错误处理。通过合理配置环境变量，可以轻松切换不同的API服务。 