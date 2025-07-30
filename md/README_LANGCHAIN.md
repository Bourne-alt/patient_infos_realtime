# 医疗报告历史对比分析 - LangChain集成

## 概述

本系统集成了LangChain框架，提供基于人工智能的医疗报告历史对比分析功能。通过分析患者的历史报告数据，系统能够识别关键指标变化趋势、评估风险并提供个性化的医疗建议。

## 功能特性

### 1. 核心功能
- **历史对比分析**: 基于LangChain的智能对比分析，支持多种报告类型
- **趋势分析**: 识别关键指标的变化趋势（上升、下降、稳定）
- **风险评估**: 评估病情发展和潜在风险
- **个性化建议**: 提供针对性的医疗建议和随访计划

### 2. 支持的报告类型
- **常规检验报告** (`routine_lab`): 血常规、生化等检验结果
- **微生物检验报告** (`microbiology`): 微生物培养、药敏试验等
- **检查报告** (`examination`): 影像学检查、功能检查等
- **病理报告** (`pathology`): 组织病理学检查结果

### 3. 分析周期
- `1month`: 最近1个月的历史数据
- `3months`: 最近3个月的历史数据
- `6months`: 最近6个月的历史数据（默认）
- `1year`: 最近1年的历史数据
- `all`: 所有历史数据

## 系统架构

### 技术栈
- **LangChain**: 大语言模型应用框架
- **OpenAI GPT**: 智能分析引擎（可选）
- **Ollama**: 本地部署模型（可选）
- **PostgreSQL**: 数据存储
- **FastAPI**: API服务框架

### 核心模块
1. **langchain_service.py**: LangChain服务层，处理AI分析逻辑
2. **database_service.py**: 数据库服务层，处理历史数据查询
3. **models.py**: 数据模型定义，包含对比分析结果表
4. **schemas.py**: API请求/响应模型定义

## 环境配置

### 1. 依赖安装
```bash
pip install -r requirements.txt
```

### 2. 环境变量配置
```bash
# 数据库配置
POSTGRES_HOST=10.1.27.65
POSTGRES_PORT=5432
POSTGRES_DATABASE=medical_reports
POSTGRES_USER=postgres
POSTGRES_PASSWORD=admin123

# OpenAI配置（可选）
OPENAI_API_KEY=your-openai-api-key
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo

# 本地模型配置（可选）
LLM_API_URL=http://localhost:11434/api/generate
LLM_MODEL=llama3.1
```

### 3. 数据库初始化
系统启动时会自动创建必要的数据库表，包括：
- `routine_lab_reports`: 常规检验报告
- `microbiology_reports`: 微生物检验报告
- `examination_reports`: 检查报告
- `pathology_reports`: 病理报告
- `report_comparison_analysis`: 对比分析结果

## API使用指南

### 1. 健康检查
```bash
curl -X GET "http://localhost:7700/health"
```

### 2. 历史对比分析
```bash
curl -X POST "http://localhost:7700/compare-reports" \
  -H "Content-Type: application/json" \
  -d '{
    "cardNo": "12345678",
    "reportType": "routine_lab",
    "currentReportId": 123,
    "comparisonPeriod": "6months",
    "includeAIAnalysis": true
  }'
```

### 3. 患者历史报告查询
```bash
curl -X POST "http://localhost:7700/patient-history" \
  -H "Content-Type: application/json" \
  -d '{
    "cardNo": "12345678",
    "reportType": "routine_lab",
    "limit": 10,
    "offset": 0
  }'
```

## 响应格式

### 对比分析响应
```json
{
  "code": "200",
  "cardNo": "12345678",
  "processed_at": "2024-01-01T12:00:00Z",
  "comparison_analysis": "详细的对比分析结果...",
  "key_changes": {
    "significant_changes": ["血糖水平显著上升"],
    "trends": ["指标上升"],
    "abnormal_values": ["存在异常值"],
    "recommendations": ["需要关注"]
  },
  "trend_analysis": "趋势分析详情...",
  "risk_assessment": "风险评估详情...",
  "recommendations": "医疗建议详情...",
  "historical_reports_count": 5,
  "analysis_model": "gpt-3.5-turbo",
  "analysis_confidence": "高"
}
```

## 工作流程

### 1. 数据提交
1. 通过现有API端点提交医疗报告数据
2. 系统进行基础AI分析并存储

### 2. 历史对比分析
1. 调用 `/compare-reports` 端点
2. 系统查询历史报告数据
3. 使用LangChain进行智能对比分析
4. 生成趋势分析、风险评估和建议
5. 保存分析结果到数据库

### 3. 结果查询
1. 通过 `/patient-history` 查询患者历史报告摘要
2. 获取详细的对比分析结果

## 分析示例

### 常规检验报告分析
```
趋势分析：
- 血糖水平：从6.2mmol/L上升至7.8mmol/L，呈现上升趋势
- 血压：收缩压从120mmHg上升至145mmHg，需要关注
- 胆固醇：总胆固醇水平稳定在5.2mmol/L左右

风险评估：
- 糖尿病风险：中等风险，血糖控制需要加强
- 心血管风险：轻度升高，建议监控血压变化

医疗建议：
- 建议4周后复查血糖和糖化血红蛋白
- 调整饮食结构，增加运动量
- 考虑启动降糖药物治疗
```

## 优化建议

### 1. 性能优化
- 使用Redis缓存频繁查询的历史数据
- 实现异步处理大量历史数据
- 优化数据库查询语句

### 2. 准确性提升
- 增加更多专业医学知识到Prompt模板
- 结合临床指南和诊疗规范
- 定期更新分析模型

### 3. 扩展功能
- 支持多模态数据分析（图像、文本、数值）
- 实现跨科室的综合分析
- 添加预测性分析功能

## 故障排除

### 1. 常见问题
- **LangChain初始化失败**: 检查OpenAI API Key或本地模型服务
- **数据库连接失败**: 确认PostgreSQL服务状态和连接参数
- **分析结果为空**: 检查历史数据是否存在

### 2. 日志查看
```bash
tail -f medical_report_api.log
```

### 3. 调试模式
设置环境变量 `DEBUG=true` 启用详细日志输出

## 联系支持

如有问题或建议，请联系技术支持团队。

---

*最后更新时间: 2024-01-01* 