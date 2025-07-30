# 医疗报告分析API

这是一个专业的医疗报告分析API，能够接收各种类型的医疗报告数据，调用大模型进行智能分析，并将结果存储到PostgreSQL数据库中。

## 功能特性

- 支持4种医疗报告类型：
  - 常规检验报告
  - 微生物检验报告
  - 检查报告
  - 病理报告

- 集成大模型AI分析
- **历史报告对比分析**：自动查询患者最近的历史报告，进行对比分析，识别变化趋势
- 基于LangChain的深度分析
- PostgreSQL数据库存储
- 完整的错误处理和日志记录
- Docker容器化部署
- RESTful API接口

## 历史报告对比分析功能

### 工作原理

当提交新的医疗报告时，系统会自动：

1. **查询历史报告**：在数据库中查找该患者最近3个月内的同类型报告
2. **智能对比分析**：将当前报告与最近的历史报告进行对比
3. **趋势识别**：分析各项指标的变化趋势（上升、下降、稳定）
4. **风险评估**：基于变化趋势评估健康风险
5. **生成建议**：提供针对性的医疗建议和随访计划

### 对比分析内容

#### 常规检验报告
- 各项检验指标的数值变化
- 异常指标的改善或恶化情况
- 整体健康状况的变化趋势
- 需要重点关注的风险指标

#### 微生物检验报告
- 病原菌数量的变化
- 药敏结果的变化和耐药性分析
- 感染控制效果评估
- 治疗方案的有效性评估

#### 检查报告
- 客观所见的变化对比
- 病变进展、稳定或好转的评估
- 治疗效果的评估

#### 病理报告
- 病理形态学特征的变化
- 疾病进展评估
- 治疗效果的病理学评估

### 分析结果特点

- **专业性**：采用医学专业术语和标准
- **对比性**：突出当前报告与历史报告的差异
- **趋势性**：识别健康状况的变化趋势
- **建议性**：提供具体的医疗建议和随访计划

### 适用场景

- 慢性病患者的定期检查
- 感染性疾病的治疗效果监测
- 术后患者的恢复情况评估
- 健康体检的纵向比较

## API接口

### 1. 常规检验报告 - POST /routine-lab

```json
{
  "cardNo": "患者卡号",
  "reportDate": "报告日期",
  "resultList": "检查结果JSON字符串"
}
```

### 2. 微生物检验报告 - POST /microbiology

```json
{
  "cardNo": "患者卡号",
  "reportDate": "报告日期",
  "microbeResultList": "微生物报告列表JSON字符串",
  "bacterialResultList": "细菌鉴定结果列表JSON字符串",
  "drugSensitivityList": "药敏结果列表JSON字符串",
  "deptCode": "科室编码",
  "deptName": "科室名称",
  "diagnosisCode": "诊断编码",
  "diagnosisName": "诊断名称",
  "diagnosisDate": "诊断日期",
  "testResultCode": "检验结果编码",
  "testResultName": "检验结果名称",
  "testQuantifyResult": "检验定量结果",
  "testQuantifyResultUnit": "检验定量结果单位"
}
```

### 3. 检查报告 - POST /examination

```json
{
  "cardNo": "患者卡号",
  "patientNo": "住院号",
  "reportDate": "报告生成时间",
  "examResultCode": "检查结果代码",
  "examResultName": "检查结果名称",
  "examQuantifyResult": "检查定量结果",
  "examQuantifyResultUnit": "检查定量结果单位",
  "examObservation": "检查报告结果-客观所见",
  "examResult": "检查报告结果-主观提示"
}
```

### 4. 病理报告 - POST /pathology

```json
{
  "cardNo": "患者卡号",
  "patientNo": "住院号",
  "deptCode": "患者科室编码",
  "deptName": "患者科室名称",
  "diagnosisCode": "诊断代码",
  "diagnosisName": "诊断名称",
  "chiefComplaint": "主诉",
  "symptomDescribe": "症状描述",
  "symptomStartTime": "症状开始时间",
  "symptomEndTime": "症状停止时间",
  "examResultCode": "检查结果代码",
  "examResultName": "检查结果名称",
  "examQuantifyResult": "检查定量结果",
  "examQuantifyResultUnit": "检查定量结果单位",
  "diagnosisDescribe": "诊疗过程描述",
  "examObservation": "检查报告结果-客观所见",
  "examResult": "检查报告结果-主观提示"
}
```

### 响应格式

所有接口都返回统一的响应格式：

```json
{
  "code": "200",
  "cardNo": "患者卡号",
  "processed_at": "处理时间",
  "ai_analysis": "AI分析结果",
  "error": "错误信息（仅在出错时）"
}
```

## 部署方式

### 1. Docker部署（推荐）

```bash
# 克隆代码
git clone <repository-url>
cd medical_report_api

# 构建并启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f medical-report-api
```

### 2. 本地部署

```bash
# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export POSTGRES_HOST=10.1.27.65
export POSTGRES_PORT=5432
export POSTGRES_DATABASE=medical_reports
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=admin123
export LLM_API_URL=http://localhost:11434/api/generate
export LLM_MODEL=llama3.1

# 启动服务
uvicorn api:app --host 0.0.0.0 --port 7700
```

## 环境变量配置

- `POSTGRES_HOST`: PostgreSQL主机地址
- `POSTGRES_PORT`: PostgreSQL端口
- `POSTGRES_DATABASE`: 数据库名称
- `POSTGRES_USER`: 数据库用户名
- `POSTGRES_PASSWORD`: 数据库密码
- `LLM_API_URL`: 大模型API地址
- `LLM_MODEL`: 大模型名称

## 健康检查

访问 `GET /health` 来检查服务状态：

```json
{
  "status": "healthy",
  "database": "connected",
  "llm_api": "connected",
  "timestamp": "2023-12-01T10:30:00.000Z"
}
```

## 日志文件

- 应用日志：`medical_report_api.log`
- 包含详细的请求、响应和错误信息

## 技术栈

- **框架**: FastAPI
- **数据库**: PostgreSQL
- **AI模型**: Ollama/LLaMA
- **容器化**: Docker
- **日志**: Python logging
- **异步处理**: asyncio

## 开发说明

1. 所有医疗报告数据都会进行AI分析
2. **历史对比分析**：系统会自动查询患者最近的历史报告进行对比分析
3. 分析结果存储在对应的数据库表中
4. 支持并发处理多个报告
5. 完整的错误处理和重试机制
6. 详细的日志记录便于调试

### 历史对比分析技术细节

- **查询范围**：默认查询3个月内的同类型历史报告
- **选择策略**：优先选择最近的一条历史报告进行对比
- **分析逻辑**：
  - 如果存在历史报告，进行对比分析
  - 如果没有历史报告，进行单独分析并提示首次检验
- **存储策略**：当前报告和历史报告数据都会记录在分析结果中
- **性能优化**：历史报告查询采用索引优化，支持高并发访问

### 测试功能

运行测试脚本验证历史对比分析功能：

```bash
python test_historical_comparison.py
```

测试脚本会：
1. 检查API健康状态
2. 提交第一份报告（作为历史报告）
3. 提交第二份报告（触发对比分析）
4. 验证对比分析结果是否包含历史对比内容

## 联系方式

如有问题，请联系开发团队。 