"""
医疗报告处理服务
统一处理各种类型的医疗报告，消除代码重复
"""

import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum
import asyncio
from functools import lru_cache

from sqlalchemy.orm import Session
from database_service import DatabaseService
from models import MedicalReport

logger = logging.getLogger(__name__)


class ReportType(Enum):
    """报告类型枚举"""
    ROUTINE_LAB = "routine_lab"
    MICROBIOLOGY = "microbiology"
    EXAMINATION = "examination"
    PATHOLOGY = "pathology"


@dataclass
class ReportData:
    """报告数据结构"""
    card_no: str
    report_date: str
    report_type: ReportType
    data: Dict[str, Any]
    patient_no: Optional[str] = None
    dept_code: Optional[str] = None
    dept_name: Optional[str] = None
    diagnosis_code: Optional[str] = None
    diagnosis_name: Optional[str] = None


class LLMCache:
    """LLM调用结果缓存"""
    
    def __init__(self, max_size: int = 100, ttl_hours: int = 24):
        self.cache: Dict[str, Tuple[str, datetime]] = {}
        self.max_size = max_size
        self.ttl = timedelta(hours=ttl_hours)
    
    def _generate_key(self, report_type: str, report_data: Dict[str, Any], 
                      historical_report: Optional[Dict[str, Any]] = None) -> str:
        """生成缓存键"""
        # 创建包含关键数据的字符串
        key_data = {
            "type": report_type,
            "data": report_data,
            "has_history": historical_report is not None
        }
        if historical_report:
            # 只包含历史报告的关键信息，避免缓存键过长
            key_data["history_date"] = historical_report.get("report_date", "")
        
        key_str = json.dumps(key_data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, report_type: str, report_data: Dict[str, Any], 
            historical_report: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """获取缓存结果"""
        key = self._generate_key(report_type, report_data, historical_report)
        
        if key in self.cache:
            result, timestamp = self.cache[key]
            # 检查是否过期
            if datetime.utcnow() - timestamp < self.ttl:
                logger.info(f"LLM缓存命中: {report_type}")
                return result
            else:
                # 删除过期缓存
                del self.cache[key]
        
        return None
    
    def set(self, report_type: str, report_data: Dict[str, Any], 
            result: str, historical_report: Optional[Dict[str, Any]] = None):
        """设置缓存结果"""
        key = self._generate_key(report_type, report_data, historical_report)
        
        # 如果缓存已满，删除最旧的条目
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache.keys(), 
                           key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
        
        self.cache[key] = (result, datetime.utcnow())
        logger.info(f"LLM结果已缓存: {report_type}")
    
    def clear_expired(self):
        """清理过期缓存"""
        current_time = datetime.utcnow()
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if current_time - timestamp >= self.ttl
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.info(f"清理了 {len(expired_keys)} 个过期缓存")


class ReportProcessingService:
    """报告处理服务"""
    
    def __init__(self):
        self.llm_cache = LLMCache(max_size=200, ttl_hours=12)  # 12小时缓存
    
    @lru_cache(maxsize=50)
    def _get_report_type_config(self, report_type: ReportType) -> Dict[str, Any]:
        """获取报告类型配置（缓存）"""
        configs = {
            ReportType.ROUTINE_LAB: {
                "db_type": "routine_lab",
                "analysis_type": "routineLab",
                "required_fields": ["cardNo", "reportDate", "resultList"]
            },
            ReportType.MICROBIOLOGY: {
                "db_type": "microbiology", 
                "analysis_type": "microbiology",
                "required_fields": ["cardNo", "reportDate", "microbeResultList", 
                                  "bacterialResultList", "drugSensitivityList"]
            },
            ReportType.EXAMINATION: {
                "db_type": "examination",
                "analysis_type": "examination", 
                "required_fields": ["cardNo", "reportDate", "examObservation", "examResult"]
            },
            ReportType.PATHOLOGY: {
                "db_type": "pathology",
                "analysis_type": "pathology",
                "required_fields": ["cardNo", "reportDate", "examObservation", "examResult"]
            }
        }
        return configs.get(report_type, {})
    
    def validate_report_data(self, report_data: ReportData) -> Tuple[bool, Optional[str]]:
        """验证报告数据"""
        try:
            config = self._get_report_type_config(report_data.report_type)
            required_fields = config.get("required_fields", [])
            
            # 检查必需字段
            for field in required_fields:
                if field not in report_data.data:
                    return False, f"缺少必需字段: {field}"
            
            # 现在resultList是对象数组，不需要JSON解析验证
            if report_data.report_type == ReportType.ROUTINE_LAB:
                pass
            
            elif report_data.report_type == ReportType.MICROBIOLOGY:
                # 现在这些字段是对象数组，不需要JSON解析验证
                pass
            
            return True, None
            
        except Exception as e:
            logger.error(f"验证报告数据时出错: {e}")
            return False, f"验证失败: {str(e)}"
    
    def prepare_analysis_data(self, report_data: ReportData) -> Dict[str, Any]:
        """准备用于AI分析的数据"""
        analysis_data = {
            "cardNo": report_data.card_no,
            "reportDate": report_data.report_date
        }
        
        if report_data.report_type == ReportType.ROUTINE_LAB:
            # 将Pydantic对象转换为字典
            result_list = report_data.data["resultList"]
            if result_list and hasattr(result_list[0], 'dict'):
                # 如果是Pydantic对象，转换为字典
                analysis_data["resultList"] = [item.dict() if hasattr(item, 'dict') else item for item in result_list]
            else:
                analysis_data["resultList"] = result_list
        
        elif report_data.report_type == ReportType.MICROBIOLOGY:
            # 将Pydantic对象转换为字典
            microbe_list = report_data.data["microbeResultList"]
            bacterial_list = report_data.data["bacterialResultList"]
            drug_list = report_data.data["drugSensitivityList"]
            
            analysis_data.update({
                "microbeResultList": [item.dict() if hasattr(item, 'dict') else item for item in microbe_list] if microbe_list else [],
                "bacterialResultList": [item.dict() if hasattr(item, 'dict') else item for item in bacterial_list] if bacterial_list else [],
                "drugSensitivityList": [item.dict() if hasattr(item, 'dict') else item for item in drug_list] if drug_list else [],
                "deptCode": report_data.dept_code,
                "deptName": report_data.dept_name,
                "diagnosisCode": report_data.diagnosis_code,
                "diagnosisName": report_data.diagnosis_name
            })
            # 添加其他微生物报告字段
            for key in ["diagnosisDate", "testResultCode", "testResultName", 
                       "testQuantifyResult", "testQuantifyResultUnit"]:
                if key in report_data.data:
                    analysis_data[key] = report_data.data[key]
        
        elif report_data.report_type in [ReportType.EXAMINATION, ReportType.PATHOLOGY]:
            # 检查报告和病理报告的共同字段
            common_fields = ["examResultCode", "examResultName", "examQuantifyResult",
                           "examQuantifyResultUnit", "examObservation", "examResult"]
            for field in common_fields:
                if field in report_data.data:
                    analysis_data[field] = report_data.data[field]
            
            if report_data.patient_no:
                analysis_data["patientNo"] = report_data.patient_no
            
            # 病理报告特有字段
            if report_data.report_type == ReportType.PATHOLOGY:
                pathology_fields = ["chiefComplaint", "symptomDescribe", 
                                  "symptomStartTime", "symptomEndTime", "diagnosisDescribe"]
                for field in pathology_fields:
                    if field in report_data.data:
                        analysis_data[field] = report_data.data[field]
        
        return analysis_data
    
    def prepare_database_data(self, report_data: ReportData) -> Dict[str, Any]:
        """准备用于数据库存储的数据"""
        if report_data.report_type == ReportType.ROUTINE_LAB:
            # 将Pydantic对象转换为字典
            result_list = report_data.data["resultList"]
            if result_list and hasattr(result_list[0], 'dict'):
                return [item.dict() if hasattr(item, 'dict') else item for item in result_list]
            return result_list
        
        elif report_data.report_type == ReportType.MICROBIOLOGY:
            # 将Pydantic对象转换为字典，返回列表格式保持一致
            microbe_list = report_data.data["microbeResultList"]
            bacterial_list = report_data.data["bacterialResultList"]
            drug_list = report_data.data["drugSensitivityList"]
            
            # 构建统一的结果列表
            result_list = []
            
            # 添加微生物结果
            if microbe_list:
                for item in microbe_list:
                    result_item = item.dict() if hasattr(item, 'dict') else item
                    result_item["result_type"] = "microbe"
                    result_list.append(result_item)
            
            # 添加细菌结果
            if bacterial_list:
                for item in bacterial_list:
                    result_item = item.dict() if hasattr(item, 'dict') else item
                    result_item["result_type"] = "bacterial"
                    result_list.append(result_item)
            
            # 添加药敏结果
            if drug_list:
                for item in drug_list:
                    result_item = item.dict() if hasattr(item, 'dict') else item
                    result_item["result_type"] = "drug_sensitivity"
                    result_list.append(result_item)
            
            # 添加诊断信息作为单独的结果项
            if any([report_data.data.get("diagnosisDate"), report_data.data.get("testResultCode"), 
                   report_data.data.get("testResultName"), report_data.data.get("testQuantifyResult")]):
                diagnosis_item = {
                    "result_type": "diagnosis",
                    "diagnosis_date": report_data.data.get("diagnosisDate"),
                    "test_result_code": report_data.data.get("testResultCode"),
                    "test_result_name": report_data.data.get("testResultName"),
                    "test_quantify_result": report_data.data.get("testQuantifyResult"),
                    "test_quantify_result_unit": report_data.data.get("testQuantifyResultUnit")
                }
                result_list.append(diagnosis_item)
            
            return result_list
        
        elif report_data.report_type == ReportType.EXAMINATION:
            # 返回列表格式保持一致
            result_list = []
            
            # 构建检查结果项
            exam_item = {
                "result_type": "examination",
                "exam_result_code": report_data.data.get("examResultCode"),
                "exam_result_name": report_data.data.get("examResultName"),
                "exam_quantify_result": report_data.data.get("examQuantifyResult"),
                "exam_quantify_result_unit": report_data.data.get("examQuantifyResultUnit"),
                "exam_observation": report_data.data.get("examObservation"),
                "exam_result": report_data.data.get("examResult")
            }
            result_list.append(exam_item)
            
            return result_list
        
        elif report_data.report_type == ReportType.PATHOLOGY:
            # 返回列表格式保持一致
            result_list = []
            
            # 构建病理结果项
            pathology_item = {
                "result_type": "pathology",
                "chief_complaint": report_data.data.get("chiefComplaint"),
                "symptom_describe": report_data.data.get("symptomDescribe"),
                "symptom_start_time": report_data.data.get("symptomStartTime"),
                "symptom_end_time": report_data.data.get("symptomEndTime"),
                "exam_result_code": report_data.data.get("examResultCode"),
                "exam_result_name": report_data.data.get("examResultName"),
                "exam_quantify_result": report_data.data.get("examQuantifyResult"),
                "exam_quantify_result_unit": report_data.data.get("examQuantifyResultUnit"),
                "diagnosis_describe": report_data.data.get("diagnosisDescribe"),
                "exam_observation": report_data.data.get("examObservation"),
                "exam_result": report_data.data.get("examResult")
            }
            result_list.append(pathology_item)
            
            return result_list
        
        return {}
    
    async def get_cached_analysis(self, report_type: str, report_data: Dict[str, Any], 
                                  historical_report: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """获取缓存的分析结果"""
        return self.llm_cache.get(report_type, report_data, historical_report)
    
    async def cache_analysis_result(self, report_type: str, report_data: Dict[str, Any], 
                                   result: str, historical_report: Optional[Dict[str, Any]] = None):
        """缓存分析结果"""
        self.llm_cache.set(report_type, report_data, result, historical_report)
    
    async def process_report(self, report_data: ReportData, db: Session, 
                           analyze_func, error_handler) -> Dict[str, Any]:
        """统一处理报告的核心方法"""
        try:
            # 1. 验证数据
            is_valid, error_msg = self.validate_report_data(report_data)
            if not is_valid:
                return error_handler(report_data.card_no, error_msg)
            
            # 2. 准备分析数据
            analysis_data = self.prepare_analysis_data(report_data)
            
            # 3. 获取历史报告 - 根据报告类型分类查询
            db_service = DatabaseService(db)
            historical_report = None
            
            # 根据报告类型调用相应的方法
            if report_data.report_type == ReportType.MICROBIOLOGY:
                latest_result = db_service.get_latest_microbiological_reports(report_data.card_no)
                data_field = 'microbiological_reports'
                report_type_name = '微生物报告'
            elif report_data.report_type == ReportType.EXAMINATION:
                latest_result = db_service.get_latest_pacs_reports(report_data.card_no)
                data_field = 'pacs_reports'
                report_type_name = 'PACS检查报告'
            elif report_data.report_type == ReportType.PATHOLOGY:
                latest_result = db_service.get_latest_pathology_reports(report_data.card_no)
                data_field = 'pathology_reports'
                report_type_name = '病理报告'
            else:  # ROUTINE_LAB 默认使用检验结果
                latest_result = db_service.get_latest_lis_result_detail(report_data.card_no)
                data_field = 'lis_result_detail'
                report_type_name = '检验结果详情'
            
            if latest_result and latest_result.get(data_field):
                # 使用标准化的日期字符串
                report_date = latest_result.get('reg_date_str', '')
                if not report_date and latest_result.get('reg_date'):
                    report_date = str(latest_result['reg_date'])
                
                historical_report = {
                    "card_no": latest_result['card_no'],
                    "patient_name": latest_result.get('patient_name', ''),
                    "report_date": report_date,
                    "report_content": latest_result[data_field],  # 统一使用report_content字段名
                    "content_type": data_field,  # 标识内容来源字段
                    "source": "patient_info_table",
                    "data_type": "structured_text",  # 标识数据类型
                    "reg_date": report_date  # 使用字符串格式的日期，避免 JSON 序列化错误
                }
                logger.info(f"找到历史{report_type_name} - 患者: {report_data.card_no}, 日期: {report_date}")
            
            # 4. 检查缓存
            config = self._get_report_type_config(report_data.report_type)
            analysis_type = config.get("analysis_type", report_data.report_type.value)
            
            cached_result = await self.get_cached_analysis(
                analysis_type, analysis_data, historical_report
            )
            
            if cached_result:
                ai_analysis = cached_result
                logger.info(f"使用缓存的AI分析结果 - {report_data.card_no}")
            else:
                # 5. 调用AI分析
                ai_analysis = await analyze_func(analysis_type, analysis_data, historical_report)
                
                # 6. 缓存结果
                await self.cache_analysis_result(
                    analysis_type, analysis_data, ai_analysis, historical_report
                )
            
            # 7. 准备数据库数据
            db_data = self.prepare_database_data(report_data)
            
            # 8. 保存到数据库
            db_report = MedicalReport(
                card_no=report_data.card_no,
                patient_no=report_data.patient_no,
                report_type=config["db_type"],
                report_date=report_data.report_date,
                report_data=db_data,
                dept_code=report_data.dept_code,
                dept_name=report_data.dept_name,
                diagnosis_code=report_data.diagnosis_code,
                diagnosis_name=report_data.diagnosis_name,
                ai_analysis=ai_analysis,
                processed_at=datetime.utcnow()
            )
            
            db.add(db_report)
            db.commit()
            db.refresh(db_report)
            
            logger.info(f"{report_data.report_type.value}报告保存成功 - 患者: {report_data.card_no}")
            
            return {
                "code": "200",
                "cardNo": report_data.card_no,
                "processed_at": datetime.utcnow().isoformat(),
                "ai_analysis": ai_analysis
            }
            
        except Exception as e:
            logger.error(f"处理{report_data.report_type.value}报告失败: {e}")
            db.rollback()
            return error_handler(report_data.card_no, f"处理失败: {str(e)}")
    
    def cleanup_cache(self):
        """清理过期缓存"""
        self.llm_cache.clear_expired()


# 全局报告处理服务实例
report_service = ReportProcessingService()