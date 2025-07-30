# 数据库统一重构说明

## 概述

本次重构将原来的多个独立报告表合并为一个统一的 `medical_reports` 表，简化了数据库结构，提高了可维护性。

## 重构内容

### 1. 表结构变化

#### 原有结构
- `routine_lab_reports` - 常规检验报告表
- `microbiology_reports` - 微生物检验报告表  
- `examination_reports` - 检查报告表
- `pathology_reports` - 病理报告表

#### 新结构
- `medical_reports` - 统一医疗报告表（包含所有类型的报告）

### 2. 字段变化

#### 删除的字段
- `result_list` - 原常规检验报告的结果列表字段

#### 新增的字段
- `report_type` - 报告类型字段（必填，有索引）
  - `routine_lab` - 常规检验报告
  - `microbiology` - 微生物检验报告  
  - `examination` - 检查报告
  - `pathology` - 病理报告
- `report_data` - 统一的报告数据字段（JSON格式）

#### 保留的字段
- `card_no` - 患者卡号
- `patient_no` - 住院号（可选）
- `report_date` - 报告日期
- `dept_code` - 科室编码（可选）
- `dept_name` - 科室名称（可选）
- `diagnosis_code` - 诊断编码（可选）
- `diagnosis_name` - 诊断名称（可选）
- `ai_analysis` - AI分析结果
- `processed_at` - 处理时间
- `created_at` - 创建时间
- `updated_at` - 更新时间

### 3. 数据存储格式

不同类型的报告数据都存储在 `report_data` JSON字段中：

#### 常规检验报告 (routine_lab)
```json
{
  "white_blood_cell": "6.5",
  "red_blood_cell": "4.8", 
  "hemoglobin": "145",
  "platelet": "280"
}
```

#### 微生物检验报告 (microbiology)
```json
{
  "microbe_result_list": [...],
  "bacterial_result_list": [...],
  "drug_sensitivity_list": [...],
  "diagnosis_date": "2025-04-20",
  "test_result_code": "...",
  "test_result_name": "..."
}
```

#### 检查报告 (examination)
```json
{
  "exam_result_code": "...",
  "exam_result_name": "...",
  "exam_quantify_result": "...",
  "exam_observation": "...",
  "exam_result": "..."
}
```

#### 病理报告 (pathology)
```json
{
  "chief_complaint": "...",
  "symptom_describe": "...",
  "symptom_start_time": "...",
  "exam_observation": "...",
  "exam_result": "..."
}
```

## 代码变化

### 1. 模型层变化 (models.py)
- 删除了 `RoutineLabReport`, `MicrobiologyReport`, `ExaminationReport`, `PathologyReport` 模型
- 新增了统一的 `MedicalReport` 模型

### 2. API层变化 (api.py)
- 所有报告端点现在都使用 `MedicalReport` 模型
- 不同类型的报告数据被整理为JSON格式存储在 `report_data` 字段中
- 添加了 `report_type` 字段标识报告类型

### 3. 数据库服务层变化 (database_service.py)
- 所有查询方法都改为查询 `medical_reports` 表
- 添加了 `report_type` 过滤条件
- 简化了数据转换逻辑

## 优势

### 1. 简化维护
- 只需维护一个表结构
- 统一的查询和索引策略
- 减少了代码重复

### 2. 扩展性更好  
- 添加新的报告类型只需增加 `report_type` 值
- 不需要创建新表或修改表结构
- JSON字段支持灵活的数据格式

### 3. 查询效率
- 单表查询避免了复杂的JOIN操作
- 统一的索引策略
- 更好的分页和排序支持

### 4. 数据一致性
- 统一的字段命名和数据类型
- 一致的时间戳管理
- 统一的AI分析结果存储

## 迁移步骤

### 1. 数据库迁移
```bash
# 使用新的初始化脚本
psql -U postgres -f init_unified_database.sql
```

### 2. 数据迁移（如果有旧数据）
```sql
-- 迁移常规检验报告
INSERT INTO medical_reports (card_no, report_type, report_date, report_data, ai_analysis, created_at)
SELECT card_no, 'routine_lab', report_date, result_list, ai_analysis, created_at
FROM routine_lab_reports;

-- 迁移其他类型报告...
```

### 3. 应用部署
- 更新代码到新版本
- 重启服务
- 验证功能正常

## 向后兼容性

### API兼容性
- 所有现有的API端点保持不变
- 请求和响应格式保持一致
- 客户端无需修改

### 功能兼容性
- 所有现有功能继续正常工作
- 历史对比分析功能增强
- 数据查询性能提升

## 注意事项

1. **数据备份**: 在执行迁移前请备份现有数据
2. **索引优化**: 新表包含了针对查询模式优化的索引
3. **JSON字段**: 使用JSONB格式支持高效的JSON查询
4. **报告类型**: 确保所有API调用都使用正确的report_type值

## 测试验证

### 1. 功能测试
- 所有报告类型的创建和查询
- 历史对比分析功能
- 患者历史报告查询

### 2. 性能测试  
- 大量数据下的查询性能
- 并发访问测试
- 内存使用情况

### 3. 数据完整性测试
- 数据迁移后的完整性验证
- 外键约束检查
- JSON数据格式验证

## 总结

这次数据库统一重构大大简化了系统架构，提高了可维护性和扩展性，同时保持了完全的向后兼容性。新的统一表结构为未来的功能扩展奠定了良好的基础。 