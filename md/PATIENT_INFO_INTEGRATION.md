# Patient Info 表集成功能说明

## 概述

本文档描述了将 `patient_info` 表集成到医疗报告分析API中的功能。现在系统能够从 `patient_info` 表的 `lis_result_detail` 字段获取历史检验数据进行对比分析。

## 功能特性

### 1. 简化数据源支持
- **唯一数据源**: `patient_info` 表的 `lis_result_detail` 字段
- **文本对比**: 直接使用文本内容进行历史对比分析
- **跳过机制**: 当没有历史数据时，跳过历史对比，只进行单独分析

### 2. 新增数据库模型

#### PatientInfo 模型
```python
class PatientInfo(Base):
    """患者信息表"""
    __tablename__ = "patient_info"
    
    id = Column(Integer, primary_key=True, index=True)
    card_no = Column(String(50), nullable=False, index=True, comment="患者卡号")
    clinic_code = Column(String(50), comment="就诊代码")
    patient_name = Column(String(100), comment="患者姓名")
    sex_code = Column(String(10), comment="性别代码（1-男，2-女）")
    dept_code = Column(String(50), comment="科室代码")
    dept_name = Column(String(100), comment="科室名称")
    reg_date = Column(DateTime, comment="就诊登记日期")
    doctor_code = Column(String(50), comment="医生代码")
    allergy_history = Column(Text, comment="过敏史")
    discharge_summary = Column(Text, comment="出院小结")
    discharge_info = Column(Text, comment="出院信息")
    lis_result_detail = Column(Text, comment="检验结果详情")  # 关键字段
    ai_report = Column(Text, comment="AI分析报告")
    created_at = Column(DateTime, default=datetime.utcnow, comment="记录创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="记录更新时间")
```

### 3. 新增数据库服务方法

#### `get_latest_lis_result_detail(card_no: str)`
- 功能：获取指定患者最新的检验结果详情
- 参数：`card_no` - 患者卡号
- 返回：包含完整患者信息和检验结果的字典

#### `get_patient_info_history(card_no: str, comparison_period: str)`
- 功能：获取患者在指定时间段内的历史检验记录
- 参数：
  - `card_no` - 患者卡号
  - `comparison_period` - 对比时间段（"1month", "3months", "6months", "1year", "all"）
- 返回：历史记录列表

## 实现细节

### 1. API端点修改

所有医疗报告处理端点都已更新，包括：
- `/routine-lab` - 常规检验报告
- `/microbiology` - 微生物检验报告
- `/examination` - 检查报告
- `/pathology` - 病理报告

### 2. 查询逻辑流程

```python
# 1. 从patient_info表获取数据
latest_lis_result = db_service.get_latest_lis_result_detail(request.cardNo)

# 2. 如果找到数据，直接使用文本内容
if latest_lis_result and latest_lis_result.get('lis_result_detail'):
    latest_historical_report = {
        "card_no": latest_lis_result['card_no'],
        "patient_name": latest_lis_result.get('patient_name'),
        "report_date": str(latest_lis_result['reg_date']),
        "lis_result_detail": latest_lis_result['lis_result_detail'],  # 直接使用文本内容
        "source": "patient_info_table"
    }
else:
    # 3. 如果没有找到数据，跳过历史对比
    logger.info(f"未找到patient_info表历史数据 - 跳过历史对比")
```

### 3. 数据格式要求

`lis_result_detail` 字段应存储**文本格式**的检验数据，例如：

```text
血常规检查报告:
白细胞计数: 6.5 × 10^9/L (参考值: 3.5-9.5)
红细胞计数: 4.8 × 10^12/L (参考值: 4.3-5.8)
血红蛋白: 145 g/L (参考值: 130-175)
血小板计数: 280 × 10^9/L (参考值: 125-350)

生化检查报告:
血糖: 5.8 mmol/L (参考值: 3.9-6.1)
总胆固醇: 4.2 mmol/L (参考值: 2.8-5.17)
甘油三酯: 1.8 mmol/L (参考值: 0.56-1.70)

检查日期: 2025-04-20
报告状态: 已完成
```

## 使用示例

### 测试集成功能

运行测试脚本：
```bash
cd patient_infos_realtime
python test_patient_info_integration.py
```

### API调用示例

当调用任何报告分析API时，系统会自动：
1. 检查 `patient_info` 表中是否有该患者的最新检验数据
2. 如果有，直接使用文本内容进行历史对比分析
3. 如果没有，跳过历史对比，只进行当前报告的单独分析

## 优势

1. **简单高效**: 直接使用文本内容，无需复杂的数据解析
2. **数据统一性**: 所有检验数据集中存储在 `patient_info` 表
3. **鲁棒性**: 避免JSON解析错误，提高系统稳定性
4. **灵活性**: 支持任意格式的文本检验报告

## 注意事项

1. **文本格式**: `lis_result_detail` 应存储结构化的文本报告
2. **数据库连接**: 确保对 `patient_info` 表有读写权限
3. **性能考虑**: 建议为 `card_no` 和 `reg_date` 字段添加索引
4. **文本质量**: 确保检验结果文本包含关键信息和数值

## 日志记录

系统会记录以下关键信息：
- 历史数据查询结果
- 文本内容验证情况
- 查询结果统计
- 错误和异常信息 