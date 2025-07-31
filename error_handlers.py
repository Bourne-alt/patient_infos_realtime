"""
统一错误处理模块
提供一致的错误响应格式和处理逻辑
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, Union
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class MedicalReportException(Exception):
    """医疗报告处理异常基类"""
    
    def __init__(self, message: str, error_code: str = "500", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(MedicalReportException):
    """数据验证错误"""
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message, "400")
        if field:
            self.details = {"field": field}


class DatabaseError(MedicalReportException):
    """数据库操作错误"""
    
    def __init__(self, message: str, operation: Optional[str] = None):
        super().__init__(message, "500")
        if operation:
            self.details = {"operation": operation}


class LLMError(MedicalReportException):
    """LLM分析错误"""
    
    def __init__(self, message: str, model: Optional[str] = None):
        super().__init__(message, "503")
        if model:
            self.details = {"model": model}


class UnifiedErrorHandler:
    """统一错误处理器"""
    
    @staticmethod
    def create_error_response(
        card_no: str, 
        error: Union[Exception, str],
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        创建统一格式的错误响应
        
        Args:
            card_no: 患者卡号
            error: 错误对象或错误消息
            context: 错误上下文描述
            
        Returns:
            错误响应字典
        """
        # 处理字符串错误
        if isinstance(error, str):
            return {
                "code": "500",
                "cardNo": card_no,
                "error": error,
                "message": context or "操作失败",
                "processed_at": datetime.utcnow().isoformat()
            }
        
        # 处理自定义异常
        if isinstance(error, MedicalReportException):
            return {
                "code": error.error_code,
                "cardNo": card_no,
                "error": error.message,
                "message": context or "医疗报告处理异常",
                "details": error.details,
                "processed_at": datetime.utcnow().isoformat()
            }
        
        # 处理数据库异常
        if isinstance(error, SQLAlchemyError):
            error_msg, error_code = UnifiedErrorHandler._handle_database_error(error)
            return {
                "code": error_code,
                "cardNo": card_no,
                "error": error_msg,
                "message": context or "数据库操作失败",
                "processed_at": datetime.utcnow().isoformat()
            }
        
        # 处理HTTP异常
        if isinstance(error, HTTPException):
            return {
                "code": str(error.status_code),
                "cardNo": card_no,
                "error": error.detail,
                "message": context or "HTTP请求异常",
                "processed_at": datetime.utcnow().isoformat()
            }
        
        # 处理通用异常
        logger.error(f"未处理的异常类型: {type(error).__name__} - {str(error)}")
        return {
            "code": "500",
            "cardNo": card_no,
            "error": "服务器内部错误",
            "message": context or "系统异常",
            "processed_at": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def _handle_database_error(error: SQLAlchemyError) -> tuple[str, str]:
        """处理数据库错误"""
        if isinstance(error, IntegrityError):
            return "数据完整性约束违反", "400"
        elif isinstance(error, OperationalError):
            return "数据库连接或操作错误", "503"
        else:
            return "数据库操作失败", "500"
    
    @staticmethod
    def log_error(card_no: str, error: Exception, context: Optional[str] = None):
        """记录错误日志"""
        error_context = f"患者: {card_no}"
        if context:
            error_context += f" - {context}"
        
        logger.error(f"{error_context} - {type(error).__name__}: {str(error)}")
        
        # 记录详细堆栈信息（仅用于调试）
        if logger.isEnabledFor(logging.DEBUG):
            import traceback
            logger.debug(f"错误堆栈: {traceback.format_exc()}")


class ErrorResponseFactory:
    """错误响应工厂类"""
    
    @staticmethod
    def validation_error(card_no: str, message: str, field: Optional[str] = None) -> Dict[str, Any]:
        """创建验证错误响应"""
        error = ValidationError(message, field)
        return UnifiedErrorHandler.create_error_response(card_no, error, "数据验证失败")
    
    @staticmethod
    def database_error(card_no: str, operation: str, error: SQLAlchemyError) -> Dict[str, Any]:
        """创建数据库错误响应"""
        UnifiedErrorHandler.log_error(card_no, error, operation)
        db_error = DatabaseError(f"{operation}失败", operation)
        return UnifiedErrorHandler.create_error_response(card_no, db_error)
    
    @staticmethod
    def llm_error(card_no: str, error: Exception, model: Optional[str] = None) -> Dict[str, Any]:
        """创建LLM错误响应"""
        UnifiedErrorHandler.log_error(card_no, error, "LLM分析")
        llm_error = LLMError("AI分析服务暂时不可用", model)
        return UnifiedErrorHandler.create_error_response(card_no, llm_error)
    
    @staticmethod
    def processing_error(card_no: str, message: str, context: Optional[str] = None) -> Dict[str, Any]:
        """创建处理错误响应"""
        return UnifiedErrorHandler.create_error_response(card_no, message, context)


# 全局错误处理器实例
error_handler = UnifiedErrorHandler()
error_factory = ErrorResponseFactory()