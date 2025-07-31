"""
数据库服务模块
处理患者历史报告数据的查询和存储
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from models import (
    MedicalReport, ReportComparisonAnalysis, PatientInfo
)
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

class DatabaseService:
    """数据库服务类"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def _get_date_filter(self, comparison_period: str) -> datetime:
        """根据对比期间获取日期筛选条件"""
        now = datetime.utcnow()
        
        period_map = {
            "1month": now - timedelta(days=30),
            "3months": now - timedelta(days=90),
            "6months": now - timedelta(days=180),
            "1year": now - timedelta(days=365),
            "all": datetime.min
        }
        
        return period_map.get(comparison_period, now - timedelta(days=180))
    
    def get_routine_lab_reports(
        self, 
        card_no: str, 
        comparison_period: str = "6months",
        exclude_report_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取患者的常规检验报告历史数据
        
        Args:
            card_no: 患者卡号
            comparison_period: 对比时间段
            exclude_report_id: 排除的报告ID（通常是当前报告）
            
        Returns:
            历史报告数据列表
        """
        try:
            date_filter = self._get_date_filter(comparison_period)
            
            query = self.db.query(MedicalReport).filter(
                MedicalReport.card_no == card_no,
                MedicalReport.report_type == "routine_lab",
                MedicalReport.created_at >= date_filter
            )
            
            if exclude_report_id:
                query = query.filter(MedicalReport.id != exclude_report_id)
            
            reports = query.order_by(desc(MedicalReport.created_at)).all()
            
            # 转换为字典格式
            result = []
            for report in reports:
                report_data = {
                    "id": report.id,
                    "card_no": report.card_no,
                    "report_type": report.report_type,
                    "report_date": report.report_date,
                    "report_data": report.report_data,
                    "ai_analysis": report.ai_analysis,
                    "created_at": report.created_at,
                    "updated_at": report.updated_at
                }
                result.append(report_data)
            
            logger.info(f"获取常规检验报告历史数据: {card_no} - {len(result)}份")
            return result
            
        except Exception as e:
            logger.error(f"获取常规检验报告历史数据失败: {e}")
            return []
    
    def get_microbiology_reports(
        self, 
        card_no: str, 
        comparison_period: str = "6months",
        exclude_report_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取患者的微生物检验报告历史数据
        
        Args:
            card_no: 患者卡号
            comparison_period: 对比时间段
            exclude_report_id: 排除的报告ID
            
        Returns:
            历史报告数据列表
        """
        try:
            date_filter = self._get_date_filter(comparison_period)
            
            query = self.db.query(MedicalReport).filter(
                MedicalReport.card_no == card_no,
                MedicalReport.report_type == "microbiology",
                MedicalReport.created_at >= date_filter
            )
            
            if exclude_report_id:
                query = query.filter(MedicalReport.id != exclude_report_id)
            
            reports = query.order_by(desc(MedicalReport.created_at)).all()
            
            # 转换为字典格式
            result = []
            for report in reports:
                report_data = {
                    "id": report.id,
                    "card_no": report.card_no,
                    "report_type": report.report_type,
                    "report_date": report.report_date,
                    "report_data": report.report_data,
                    "dept_code": report.dept_code,
                    "dept_name": report.dept_name,
                    "diagnosis_code": report.diagnosis_code,
                    "diagnosis_name": report.diagnosis_name,
                    "ai_analysis": report.ai_analysis,
                    "created_at": report.created_at,
                    "updated_at": report.updated_at
                }
                result.append(report_data)
            
            logger.info(f"获取微生物检验报告历史数据: {card_no} - {len(result)}份")
            return result
            
        except Exception as e:
            logger.error(f"获取微生物检验报告历史数据失败: {e}")
            return []
    
    def get_examination_reports(
        self, 
        card_no: str, 
        comparison_period: str = "6months",
        exclude_report_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取患者的检查报告历史数据
        
        Args:
            card_no: 患者卡号
            comparison_period: 对比时间段
            exclude_report_id: 排除的报告ID
            
        Returns:
            历史报告数据列表
        """
        try:
            date_filter = self._get_date_filter(comparison_period)
            
            query = self.db.query(MedicalReport).filter(
                MedicalReport.card_no == card_no,
                MedicalReport.report_type == "examination",
                MedicalReport.created_at >= date_filter
            )
            
            if exclude_report_id:
                query = query.filter(MedicalReport.id != exclude_report_id)
            
            reports = query.order_by(desc(MedicalReport.created_at)).all()
            
            # 转换为字典格式
            result = []
            for report in reports:
                report_data = {
                    "id": report.id,
                    "card_no": report.card_no,
                    "patient_no": report.patient_no,
                    "report_type": report.report_type,
                    "report_date": report.report_date,
                    "report_data": report.report_data,
                    "ai_analysis": report.ai_analysis,
                    "created_at": report.created_at,
                    "updated_at": report.updated_at
                }
                result.append(report_data)
            
            logger.info(f"获取检查报告历史数据: {card_no} - {len(result)}份")
            return result
            
        except Exception as e:
            logger.error(f"获取检查报告历史数据失败: {e}")
            return []
    
    def get_pathology_reports(
        self, 
        card_no: str, 
        comparison_period: str = "6months",
        exclude_report_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取患者的病理报告历史数据
        
        Args:
            card_no: 患者卡号
            comparison_period: 对比时间段
            exclude_report_id: 排除的报告ID
            
        Returns:
            历史报告数据列表
        """
        try:
            date_filter = self._get_date_filter(comparison_period)
            
            query = self.db.query(MedicalReport).filter(
                MedicalReport.card_no == card_no,
                MedicalReport.report_type == "pathology",
                MedicalReport.created_at >= date_filter
            )
            
            if exclude_report_id:
                query = query.filter(MedicalReport.id != exclude_report_id)
            
            reports = query.order_by(desc(MedicalReport.created_at)).all()
            
            # 转换为字典格式
            result = []
            for report in reports:
                report_data = {
                    "id": report.id,
                    "card_no": report.card_no,
                    "patient_no": report.patient_no,
                    "report_type": report.report_type,
                    "report_date": report.report_date,
                    "report_data": report.report_data,
                    "dept_code": report.dept_code,
                    "dept_name": report.dept_name,
                    "diagnosis_code": report.diagnosis_code,
                    "diagnosis_name": report.diagnosis_name,
                    "ai_analysis": report.ai_analysis,
                    "created_at": report.created_at,
                    "updated_at": report.updated_at
                }
                result.append(report_data)
            
            logger.info(f"获取病理报告历史数据: {card_no} - {len(result)}份")
            return result
            
        except Exception as e:
            logger.error(f"获取病理报告历史数据失败: {e}")
            return []
    
    def get_historical_reports_by_type(
        self, 
        card_no: str, 
        report_type: str, 
        comparison_period: str = "6months",
        exclude_report_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        根据报告类型获取历史报告数据
        
        Args:
            card_no: 患者卡号
            report_type: 报告类型
            comparison_period: 对比时间段
            exclude_report_id: 排除的报告ID
            
        Returns:
            历史报告数据列表
        """
        type_method_map = {
            "routine_lab": self.get_routine_lab_reports,
            "microbiology": self.get_microbiology_reports,
            "examination": self.get_examination_reports,
            "pathology": self.get_pathology_reports
        }
        
        method = type_method_map.get(report_type)
        if not method:
            logger.error(f"不支持的报告类型: {report_type}")
            return []
        
        return method(card_no, comparison_period, exclude_report_id)
    
    def get_current_report_by_id(self, report_type: str, report_id: int) -> Optional[Dict[str, Any]]:
        """
        根据报告ID获取当前报告数据
        
        Args:
            report_type: 报告类型
            report_id: 报告ID
            
        Returns:
            当前报告数据
        """
        try:
            report = self.db.query(MedicalReport).filter(
                MedicalReport.id == report_id,
                MedicalReport.report_type == report_type
            ).first()
            
            if not report:
                logger.error(f"未找到报告: {report_type} - {report_id}")
                return None
            
            # 转换为字典格式
            result = {
                "id": report.id,
                "card_no": report.card_no,
                "patient_no": report.patient_no,
                "report_type": report.report_type,
                "report_date": report.report_date,
                "report_data": report.report_data,
                "dept_code": report.dept_code,
                "dept_name": report.dept_name,
                "diagnosis_code": report.diagnosis_code,
                "diagnosis_name": report.diagnosis_name,
                "ai_analysis": report.ai_analysis,
                "created_at": report.created_at,
                "updated_at": report.updated_at
            }
            
            return result
            
        except Exception as e:
            logger.error(f"获取当前报告数据失败: {e}")
            return None
    
    def save_comparison_analysis(
        self, 
        card_no: str,
        patient_no: Optional[str],
        report_type: str,
        current_report_id: int,
        current_report_date: str,
        current_report_data: Dict[str, Any],
        historical_reports_data: List[Dict[str, Any]],
        comparison_period: str,
        analysis_result: Dict[str, Any]
    ) -> bool:
        """
        保存对比分析结果到数据库
        
        Args:
            card_no: 患者卡号
            patient_no: 住院号
            report_type: 报告类型
            current_report_id: 当前报告ID
            current_report_date: 当前报告日期
            current_report_data: 当前报告数据
            historical_reports_data: 历史报告数据
            comparison_period: 对比时间段
            analysis_result: 分析结果
            
        Returns:
            是否保存成功
        """
        try:
            # 创建对比分析记录
            comparison_analysis = ReportComparisonAnalysis(
                card_no=card_no,
                patient_no=patient_no,
                report_type=report_type,
                current_report_id=current_report_id,
                current_report_date=current_report_date,
                current_report_data=current_report_data,
                historical_reports_count=len(historical_reports_data),
                historical_reports_data=historical_reports_data,
                comparison_period=comparison_period,
                langchain_analysis=analysis_result.get("langchain_analysis"),
                key_changes=analysis_result.get("key_changes"),
                trend_analysis=analysis_result.get("trend_analysis"),
                risk_assessment=analysis_result.get("risk_assessment"),
                recommendations=analysis_result.get("recommendations"),
                analysis_model=analysis_result.get("analysis_model"),
                analysis_confidence=analysis_result.get("analysis_confidence"),
                analysis_tokens_used=analysis_result.get("tokens_used"),
                processed_at=datetime.utcnow()
            )
            
            self.db.add(comparison_analysis)
            self.db.commit()
            
            logger.info(f"保存对比分析结果成功: {card_no} - {report_type}")
            return True
            
        except Exception as e:
            logger.error(f"保存对比分析结果失败: {e}")
            self.db.rollback()
            return False
    
    def get_patient_all_reports_summary(
        self, 
        card_no: str, 
        limit: int = 10, 
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        获取患者所有报告的摘要信息
        
        Args:
            card_no: 患者卡号
            limit: 返回记录数量限制
            offset: 偏移量
            
        Returns:
            (报告摘要列表, 总数量)
        """
        try:
            # 获取所有类型的报告（使用统一的MedicalReport表）
            all_reports_query = self.db.query(MedicalReport).filter(
                MedicalReport.card_no == card_no
            ).order_by(desc(MedicalReport.created_at))
            
            # 获取总数量
            total_count = all_reports_query.count()
            
            # 分页获取报告
            reports = all_reports_query.offset(offset).limit(limit).all()
            
            # 转换为摘要格式
            all_reports = []
            for report in reports:
                all_reports.append({
                    "report_id": report.id,
                    "report_date": report.report_date,
                    "report_type": report.report_type,
                    "key_findings": report.ai_analysis[:100] + "..." if report.ai_analysis else None,
                    "created_at": report.created_at
                })
            
            return all_reports, total_count
            
        except Exception as e:
            logger.error(f"获取患者报告摘要失败: {e}")
            return [], 0

    def get_latest_lis_result_detail(self, card_no: str) -> Optional[Dict[str, Any]]:
        """
        从patient_info表中获取最新的lis_result_detail字段值
        
        Args:
            card_no: 患者卡号
            
        Returns:
            最新的检验结果详情数据，如果找不到则返回None
        """
        try:
            # 查询该患者最新的记录（按reg_date或created_at倒序）
            patient_record = self.db.query(PatientInfo).filter(
                PatientInfo.card_no == card_no,
                PatientInfo.lis_result_detail.isnot(None),  # 确保有检验结果
                PatientInfo.lis_result_detail != ""         # 确保非空字符串
            ).order_by(
                desc(PatientInfo.reg_date), 
                desc(PatientInfo.created_at)
            ).first()
            
            if patient_record:
                # 标准化日期处理
                reg_date_str = str(patient_record.reg_date) if patient_record.reg_date else ""
                
                result = {
                    "id": patient_record.id,
                    "card_no": patient_record.card_no,
                    "patient_name": patient_record.patient_name or "",
                    "reg_date": patient_record.reg_date,
                    "reg_date_str": reg_date_str,
                    "lis_result_detail": patient_record.lis_result_detail.strip(),  # 去除首尾空白
                    "created_at": patient_record.created_at,
                    "updated_at": patient_record.updated_at
                }
                
                logger.info(f"获取到最新检验结果详情 - 患者: {card_no}, 登记日期: {reg_date_str}")
                return result
            else:
                logger.info(f"未找到患者有效检验结果详情 - 患者卡号: {card_no}")
                return None
                
        except Exception as e:
            logger.error(f"获取最新检验结果详情失败: {card_no} - {e}")
            return None
    
    def get_patient_info_history(
        self, 
        card_no: str, 
        comparison_period: str = "6months"
    ) -> List[Dict[str, Any]]:
        """
        获取患者在patient_info表中的历史记录（包含lis_result_detail）
        
        Args:
            card_no: 患者卡号
            comparison_period: 对比时间段
            
        Returns:
            历史记录列表
        """
        try:
            date_filter = self._get_date_filter(comparison_period)
            
            # 查询该患者的历史记录
            patient_records = self.db.query(PatientInfo).filter(
                PatientInfo.card_no == card_no,
                PatientInfo.created_at >= date_filter,
                PatientInfo.lis_result_detail.isnot(None)  # 只获取有检验结果的记录
            ).order_by(desc(PatientInfo.reg_date), desc(PatientInfo.created_at)).all()
            
            # 转换为字典格式
            result = []
            for record in patient_records:
                record_data = {
                    "id": record.id,
                    "card_no": record.card_no,
                    "patient_name": record.patient_name,
                    "reg_date": record.reg_date,
                    "dept_name": record.dept_name,
                    "lis_result_detail": record.lis_result_detail,
                    "ai_report": record.ai_report,
                    "pathology_reports": record.pathology_reports,
                    "pacs_reports": record.pacs_reports,
                    "microbiological_reports": record.microbiological_reports,
                    "created_at": record.created_at,
                    "updated_at": record.updated_at
                }
                result.append(record_data)
            
            logger.info(f"获取患者历史检验记录: {card_no} - {len(result)}条记录")
            return result
            
        except Exception as e:
            logger.error(f"获取患者历史检验记录失败: {e}")
            return []

    def get_latest_pathology_reports(self, card_no: str) -> Optional[Dict[str, Any]]:
        """
        从patient_info表中获取最新的病理报告
        
        Args:
            card_no: 患者卡号
            
        Returns:
            最新的病理报告数据，如果找不到则返回None
        """
        try:
            patient_record = self.db.query(PatientInfo).filter(
                PatientInfo.card_no == card_no,
                PatientInfo.pathology_reports.isnot(None),
                PatientInfo.pathology_reports != ""
            ).order_by(
                desc(PatientInfo.reg_date), 
                desc(PatientInfo.created_at)
            ).first()
            
            if patient_record:
                reg_date_str = str(patient_record.reg_date) if patient_record.reg_date else ""
                result = {
                    "id": patient_record.id,
                    "card_no": patient_record.card_no,
                    "patient_name": patient_record.patient_name or "",
                    "reg_date": patient_record.reg_date,
                    "reg_date_str": reg_date_str,
                    "pathology_reports": patient_record.pathology_reports.strip(),
                    "created_at": patient_record.created_at,
                    "updated_at": patient_record.updated_at
                }
                logger.info(f"获取到最新病理报告 - 患者: {card_no}, 登记日期: {reg_date_str}")
                return result
            else:
                logger.info(f"未找到患者病理报告 - 患者卡号: {card_no}")
                return None
                
        except Exception as e:
            logger.error(f"获取最新病理报告失败: {card_no} - {e}")
            return None

    def get_latest_pacs_reports(self, card_no: str) -> Optional[Dict[str, Any]]:
        """
        从patient_info表中获取最新的PACS检查报告
        
        Args:
            card_no: 患者卡号
            
        Returns:
            最新的PACS检查报告数据，如果找不到则返回None
        """
        try:
            patient_record = self.db.query(PatientInfo).filter(
                PatientInfo.card_no == card_no,
                PatientInfo.pacs_reports.isnot(None),
                PatientInfo.pacs_reports != ""
            ).order_by(
                desc(PatientInfo.reg_date), 
                desc(PatientInfo.created_at)
            ).first()
            
            if patient_record:
                reg_date_str = str(patient_record.reg_date) if patient_record.reg_date else ""
                result = {
                    "id": patient_record.id,
                    "card_no": patient_record.card_no,
                    "patient_name": patient_record.patient_name or "",
                    "reg_date": patient_record.reg_date,
                    "reg_date_str": reg_date_str,
                    "pacs_reports": patient_record.pacs_reports.strip(),
                    "created_at": patient_record.created_at,
                    "updated_at": patient_record.updated_at
                }
                logger.info(f"获取到最新PACS检查报告 - 患者: {card_no}, 登记日期: {reg_date_str}")
                return result
            else:
                logger.info(f"未找到患者PACS检查报告 - 患者卡号: {card_no}")
                return None
                
        except Exception as e:
            logger.error(f"获取最新PACS检查报告失败: {card_no} - {e}")
            return None

    def get_latest_microbiological_reports(self, card_no: str) -> Optional[Dict[str, Any]]:
        """
        从patient_info表中获取最新的微生物报告
        
        Args:
            card_no: 患者卡号
            
        Returns:
            最新的微生物报告数据，如果找不到则返回None
        """
        try:
            patient_record = self.db.query(PatientInfo).filter(
                PatientInfo.card_no == card_no,
                PatientInfo.microbiological_reports.isnot(None),
                PatientInfo.microbiological_reports != ""
            ).order_by(
                desc(PatientInfo.reg_date), 
                desc(PatientInfo.created_at)
            ).first()
            
            if patient_record:
                reg_date_str = str(patient_record.reg_date) if patient_record.reg_date else ""
                result = {
                    "id": patient_record.id,
                    "card_no": patient_record.card_no,
                    "patient_name": patient_record.patient_name or "",
                    "reg_date": patient_record.reg_date,
                    "reg_date_str": reg_date_str,
                    "microbiological_reports": patient_record.microbiological_reports.strip(),
                    "created_at": patient_record.created_at,
                    "updated_at": patient_record.updated_at
                }
                logger.info(f"获取到最新微生物报告 - 患者: {card_no}, 登记日期: {reg_date_str}")
                return result
            else:
                logger.info(f"未找到患者微生物报告 - 患者卡号: {card_no}")
                return None
                
        except Exception as e:
            logger.error(f"获取最新微生物报告失败: {card_no} - {e}")
            return None 