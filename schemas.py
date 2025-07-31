"""
Pydantic模型定义
定义API请求和响应的数据结构
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

# 基础响应模型
class BaseResponse(BaseModel):
    """基础响应模型"""
    code: str = Field(..., description="状态码，成功时为200")
    cardNo: str = Field(..., description="患者卡号")
    error: Optional[str] = Field(None, description="错误信息")
    processed_at: str = Field(..., description="处理时间")

# 常规检验报告模型
class RoutineLabReportRequest(BaseModel):
    """常规检验报告请求模型"""
    cardNo: str = Field(..., description="患者卡号")
    reportDate: str = Field(..., description="报告日期")
    resultList: str = Field(..., description="检查结果JSON字符串")

class RoutineLabReportResponse(BaseResponse):
    """常规检验报告响应模型"""
    ai_analysis: Optional[str] = Field(None, description="AI分析结果")

# 微生物检验报告模型
class MicrobiologyReportRequest(BaseModel):
    """微生物检验报告请求模型"""
    cardNo: str = Field(..., description="患者卡号")
    reportDate: str = Field(..., description="报告日期")
    microbeResultList: str = Field(..., description="微生物报告列表JSON字符串")
    bacterialResultList: str = Field(..., description="细菌鉴定结果列表JSON字符串")
    drugSensitivityList: str = Field(..., description="药敏结果列表JSON字符串")
    deptCode: str = Field(..., description="科室编码")
    deptName: str = Field(..., description="科室名称")
    diagnosisCode: str = Field(..., description="诊断编码")
    diagnosisName: str = Field(..., description="诊断名称")
    diagnosisDate: str = Field(..., description="诊断日期")
    testResultCode: str = Field(..., description="检验结果编码")
    testResultName: str = Field(..., description="检验结果名称")
    testQuantifyResult: str = Field(..., description="检验定量结果")
    testQuantifyResultUnit: str = Field(..., description="检验定量结果单位")

class MicrobiologyReportResponse(BaseResponse):
    """微生物检验报告响应模型"""
    ai_analysis: Optional[str] = Field(None, description="AI分析结果")

# 检查报告模型
class ExaminationReportRequest(BaseModel):
    """检查报告请求模型"""
    cardNo: str = Field(..., description="患者卡号")
    patientNo: str = Field(..., description="住院号")
    reportDate: str = Field(..., description="报告生成时间")
    examResultCode: str = Field(..., description="检查结果代码")
    examResultName: str = Field(..., description="检查结果名称")
    examQuantifyResult: str = Field(..., description="检查定量结果")
    examQuantifyResultUnit: str = Field(..., description="检查定量结果单位")
    examObservation: str = Field(..., description="检查报告结果-客观所见")
    examResult: str = Field(..., description="检查报告结果-主观提示")

class ExaminationReportResponse(BaseResponse):
    """检查报告响应模型"""
    ai_analysis: Optional[str] = Field(None, description="AI分析结果")

# 病理报告模型
class PathologyReportRequest(BaseModel):
    """病理报告请求模型"""
    cardNo: str = Field(..., description="患者卡号")
    patientNo: str = Field(..., description="住院号")
    deptCode: str = Field(..., description="患者科室编码")
    deptName: str = Field(..., description="患者科室名称")
    diagnosisCode: str = Field(..., description="诊断代码")
    diagnosisName: str = Field(..., description="诊断名称")
    chiefComplaint: str = Field(..., description="主诉")
    symptomDescribe: str = Field(..., description="症状描述")
    symptomStartTime: str = Field(..., description="症状开始时间")
    symptomEndTime: str = Field(..., description="症状停止时间")
    examResultCode: str = Field(..., description="检查结果代码")
    examResultName: str = Field(..., description="检查结果名称")
    examQuantifyResult: str = Field(..., description="检查定量结果")
    examQuantifyResultUnit: str = Field(..., description="检查定量结果单位")
    diagnosisDescribe: str = Field(..., description="诊疗过程描述")
    examObservation: str = Field(..., description="检查报告结果-客观所见")
    examResult: str = Field(..., description="检查报告结果-主观提示")

class PathologyReportResponse(BaseResponse):
    """病理报告响应模型"""
    ai_analysis: Optional[str] = Field(None, description="AI分析结果")

# 报告对比分析模型
class ReportComparisonRequest(BaseModel):
    """报告对比分析请求模型"""
    cardNo: str = Field(..., description="患者卡号")
    reportType: str = Field(..., description="报告类型", examples=["routine_lab", "microbiology", "examination", "pathology"])
    currentReportId: int = Field(..., description="当前报告ID")
    comparisonPeriod: Optional[str] = Field("6months", description="对比时间段", examples=["1month", "3months", "6months", "1year", "all"])
    includeAIAnalysis: bool = Field(True, description="是否包含AI分析")

class ReportComparisonResponse(BaseResponse):
    """报告对比分析响应模型"""
    comparison_analysis: Optional[str] = Field(None, description="LangChain对比分析结果")
    key_changes: Optional[Dict[str, Any]] = Field(None, description="关键变化数据")
    trend_analysis: Optional[str] = Field(None, description="趋势分析")
    risk_assessment: Optional[str] = Field(None, description="风险评估")
    recommendations: Optional[str] = Field(None, description="医疗建议")
    historical_reports_count: int = Field(0, description="历史报告数量")
    analysis_model: Optional[str] = Field(None, description="使用的分析模型")
    analysis_confidence: Optional[str] = Field(None, description="分析置信度")

class HistoricalReportSummary(BaseModel):
    """历史报告摘要模型"""
    report_id: int
    report_date: str
    report_type: str
    key_findings: Optional[str] = None
    
    class Config:
        from_attributes = True

class PatientHistoryRequest(BaseModel):
    """患者历史报告请求模型"""
    cardNo: str = Field(..., description="患者卡号")
    reportType: Optional[str] = Field(None, description="报告类型筛选")
    limit: int = Field(10, description="返回记录数量限制")
    offset: int = Field(0, description="偏移量")

class PatientHistoryResponse(BaseModel):
    """患者历史报告响应模型"""
    cardNo: str = Field(..., description="患者卡号")
    total_reports: int = Field(..., description="总报告数量")
    reports: List[HistoricalReportSummary] = Field(..., description="历史报告列表")
    processed_at: str = Field(..., description="处理时间")

# 错误响应模型
class ErrorResponse(BaseModel):
    """错误响应模型"""
    code: str = Field(..., description="错误代码")
    cardNo: Optional[str] = Field(None, description="患者卡号")
    error: str = Field(..., description="错误信息")
    processed_at: str = Field(..., description="处理时间")

# 数据库模型响应（用于查询）
class RoutineLabReportDB(BaseModel):
    """常规检验报告数据库模型"""
    id: int
    card_no: str
    report_date: str
    result_list: Dict[str, Any]
    ai_analysis: Optional[str] = None
    processed_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class MicrobiologyReportDB(BaseModel):
    """微生物检验报告数据库模型"""
    id: int
    card_no: str
    report_date: str
    microbe_result_list: Dict[str, Any]
    bacterial_result_list: Dict[str, Any]
    drug_sensitivity_list: Dict[str, Any]
    dept_code: str
    dept_name: str
    diagnosis_code: str
    diagnosis_name: str
    diagnosis_date: str
    test_result_code: str
    test_result_name: str
    test_quantify_result: str
    test_quantify_result_unit: str
    ai_analysis: Optional[str] = None
    processed_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ExaminationReportDB(BaseModel):
    """检查报告数据库模型"""
    id: int
    card_no: str
    patient_no: str
    report_date: str
    exam_result_code: str
    exam_result_name: str
    exam_quantify_result: str
    exam_quantify_result_unit: str
    exam_observation: str
    exam_result: str
    ai_analysis: Optional[str] = None
    processed_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PathologyReportDB(BaseModel):
    """病理报告数据库模型"""
    id: int
    card_no: str
    patient_no: str
    dept_code: str
    dept_name: str
    diagnosis_code: str
    diagnosis_name: str
    chief_complaint: str
    symptom_describe: str
    symptom_start_time: str
    symptom_end_time: str
    exam_result_code: str
    exam_result_name: str
    exam_quantify_result: str
    exam_quantify_result_unit: str
    diagnosis_describe: str
    exam_observation: str
    exam_result: str
    ai_analysis: Optional[str] = None
    processed_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PatientInfoDB(BaseModel):
    """患者信息数据库模型"""
    id: int
    card_no: str
    clinic_code: Optional[str] = None
    patient_name: Optional[str] = None
    sex_code: Optional[str] = None
    dept_code: Optional[str] = None
    dept_name: Optional[str] = None
    reg_date: Optional[datetime] = None
    doctor_code: Optional[str] = None
    allergy_history: Optional[str] = None
    discharge_summary: Optional[str] = None
    discharge_info: Optional[str] = None
    lis_result_detail: Optional[str] = None
    ai_report: Optional[str] = None
    pathology_reports: Optional[str] = None
    pacs_reports: Optional[str] = None
    microbiological_reports: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ReportComparisonAnalysisDB(BaseModel):
    """报告对比分析数据库模型"""
    id: int
    card_no: str
    patient_no: Optional[str] = None
    report_type: str
    current_report_id: int
    current_report_date: str
    current_report_data: Dict[str, Any]
    historical_reports_count: int
    historical_reports_data: Optional[Dict[str, Any]] = None
    comparison_period: Optional[str] = None
    langchain_analysis: Optional[str] = None
    key_changes: Optional[Dict[str, Any]] = None
    trend_analysis: Optional[str] = None
    risk_assessment: Optional[str] = None
    recommendations: Optional[str] = None
    analysis_model: Optional[str] = None
    analysis_confidence: Optional[str] = None
    analysis_tokens_used: Optional[int] = None
    processed_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True