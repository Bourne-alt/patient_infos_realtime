"""
数据库模型定义
定义医疗报告相关的数据库表结构
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class MedicalReport(Base):
    """统一医疗报告表"""
    __tablename__ = "medical_reports_rt_yl"
    
    id = Column(Integer, primary_key=True, index=True)
    card_no = Column(String(50), nullable=False, index=True, comment="患者卡号")
    patient_no = Column(String(50), comment="住院号")
    report_type = Column(String(50), nullable=False, index=True, comment="报告类型：routine_lab, microbiology, examination, pathology")
    report_date = Column(String(50), nullable=False, comment="报告日期")
    
    # 通用报告数据字段
    report_data = Column(JSON, nullable=False, comment="报告数据JSON格式")
    
    # 可选的扩展字段
    dept_code = Column(String(50), comment="科室编码")
    dept_name = Column(String(100), comment="科室名称")
    doctor_code = Column(String(50), comment="医生编码")
    diagnosis_code = Column(String(50), comment="诊断编码")
    diagnosis_name = Column(String(200), comment="诊断名称")
    
    # AI分析结果
    ai_analysis = Column(Text, comment="AI分析结果")
    
    # 时间戳
    processed_at = Column(DateTime, default=datetime.utcnow, comment="处理时间")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    def __repr__(self):
        return f"<MedicalReport(card_no={self.card_no}, report_type={self.report_type}, report_date={self.report_date})>"

class ReportComparisonAnalysis(Base):
    """报告对比分析结果表"""
    __tablename__ = "report_comparison_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    card_no = Column(String(50), nullable=False, index=True, comment="患者卡号")
    patient_no = Column(String(50), nullable=True, comment="住院号")
    report_type = Column(String(50), nullable=False, comment="报告类型")
    
    # 当前报告信息
    current_report_id = Column(Integer, nullable=False, comment="当前报告ID")
    current_report_date = Column(String(50), nullable=False, comment="当前报告日期")
    current_report_data = Column(JSON, nullable=False, comment="当前报告数据")
    
    # 历史报告信息
    historical_reports_count = Column(Integer, default=0, comment="历史报告数量")
    historical_reports_data = Column(JSON, nullable=True, comment="历史报告数据")
    comparison_period = Column(String(50), nullable=True, comment="对比时间段")
    
    # 对比分析结果
    langchain_analysis = Column(Text, comment="LangChain对比分析结果")
    key_changes = Column(JSON, comment="关键变化JSON数据")
    trend_analysis = Column(Text, comment="趋势分析")
    risk_assessment = Column(Text, comment="风险评估")
    recommendations = Column(Text, comment="医疗建议")
    
    # 分析元数据
    analysis_model = Column(String(100), comment="使用的分析模型")
    analysis_confidence = Column(String(20), comment="分析置信度")
    analysis_tokens_used = Column(Integer, comment="使用的token数量")
    
    # 时间戳
    processed_at = Column(DateTime, default=datetime.utcnow, comment="处理时间")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    def __repr__(self):
        return f"<ReportComparisonAnalysis(card_no={self.card_no}, report_type={self.report_type})>"

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
    lis_result_detail = Column(Text, comment="检验结果详情")
    ai_report = Column(Text, comment="AI分析报告")
    created_at = Column(DateTime, default=datetime.utcnow, comment="记录创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="记录更新时间")

    def __repr__(self):
        return f"<PatientInfo(card_no={self.card_no}, patient_name={self.patient_name})>" 