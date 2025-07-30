"""
统一的异常处理模块
定义所有自定义异常和错误处理策略
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class MedicalReportError(Exception):
    """医疗报告处理基础异常"""
    
    def __init__(self, message: str, card_no: Optional[str] = None, error_code: str = "UNKNOWN_ERROR"):
        self.message = message
        self.card_no = card_no
        self.error_code = error_code
        self.timestamp = datetime.utcnow()
        super().__init__(self.message)


class DatabaseError(MedicalReportError):
    """数据库操作异常"""
    
    def __init__(self, message: str, card_no: Optional[str] = None, operation: str = "unknown"):
        super().__init__(message, card_no, "DATABASE_ERROR")
        self.operation = operation


class LLMAnalysisError(MedicalReportError):
    """大模型分析异常"""
    
    def __init__(self, message: str, card_no: Optional[str] = None, model_name: str = "unknown"):
        super().__init__(message, card_no, "LLM_ANALYSIS_ERROR")
        self.model_name = model_name


class DataValidationError(MedicalReportError):
    """数据验证异常"""
    
    def __init__(self, message: str, card_no: Optional[str] = None, field_name: str = "unknown"):
        super().__init__(message, card_no, "DATA_VALIDATION_ERROR")
        self.field_name = field_name


class LangChainError(MedicalReportError):
    """LangChain操作异常"""
    
    def __init__(self, message: str, card_no: Optional[str] = None, chain_type: str = "unknown"):
        super().__init__(message, card_no, "LANGCHAIN_ERROR")
        self.chain_type = chain_type


class ErrorHandler:
    """统一错误处理器"""
    
    @staticmethod
    def create_error_response(
        card_no: str, 
        error: Exception, 
        default_message: str = "处理失败"
    ) -> Dict[str, Any]:
        """
        创建统一的错误响应格式
        
        Args:
            card_no: 患者卡号
            error: 异常对象
            default_message: 默认错误消息
            
        Returns:
            错误响应字典
        """
        # 记录错误日志
        logger.error(f"处理错误 - 患者: {card_no}, 错误: {str(error)}", exc_info=True)
        
        if isinstance(error, MedicalReportError):
            error_code = error.error_code
            error_message = error.message
        elif isinstance(error, ValueError):
            error_code = "VALIDATION_ERROR"
            error_message = "数据格式错误"
        elif isinstance(error, ConnectionError):
            error_code = "CONNECTION_ERROR"
            error_message = "服务连接失败"
        else:
            error_code = "INTERNAL_ERROR"
            error_message = default_message
        
        return {
            "code": "500",
            "cardNo": card_no,
            "error": error_message,
            "error_code": error_code,
            "message": "请联系技术支持或稍后重试",
            "processed_at": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def create_http_exception(
        status_code: int,
        error: Exception,
        default_detail: str = "服务器内部错误"
    ) -> HTTPException:
        """
        创建HTTP异常
        
        Args:
            status_code: HTTP状态码
            error: 异常对象
            default_detail: 默认错误详情
            
        Returns:
            HTTPException对象
        """
        if isinstance(error, MedicalReportError):
            detail = error.message
        elif isinstance(error, ValueError):
            detail = "请求数据格式错误"
        else:
            detail = default_detail
        
        logger.error(f"HTTP异常 - 状态码: {status_code}, 详情: {detail}", exc_info=True)
        return HTTPException(status_code=status_code, detail=detail)
    
    @staticmethod
    def log_and_handle_database_error(operation: str, card_no: str, error: Exception) -> DatabaseError:
        """
        记录并处理数据库错误
        
        Args:
            operation: 数据库操作类型
            card_no: 患者卡号
            error: 原始异常
            
        Returns:
            DatabaseError异常
        """
        error_msg = f"数据库{operation}操作失败: {str(error)}"
        logger.error(f"数据库错误 - 患者: {card_no}, 操作: {operation}, 错误: {error_msg}")
        return DatabaseError(error_msg, card_no, operation)
    
    @staticmethod
    def log_and_handle_llm_error(model_name: str, card_no: str, error: Exception) -> LLMAnalysisError:
        """
        记录并处理大模型分析错误
        
        Args:
            model_name: 模型名称
            card_no: 患者卡号
            error: 原始异常
            
        Returns:
            LLMAnalysisError异常
        """
        error_msg = f"大模型{model_name}分析失败: {str(error)}"
        logger.error(f"LLM错误 - 患者: {card_no}, 模型: {model_name}, 错误: {error_msg}")
        return LLMAnalysisError(error_msg, card_no, model_name)
    
    @staticmethod
    def log_and_handle_langchain_error(chain_type: str, card_no: str, error: Exception) -> LangChainError:
        """
        记录并处理LangChain错误
        
        Args:
            chain_type: 链类型
            card_no: 患者卡号
            error: 原始异常
            
        Returns:
            LangChainError异常
        """
        error_msg = f"LangChain {chain_type} 执行失败: {str(error)}"
        logger.error(f"LangChain错误 - 患者: {card_no}, 链类型: {chain_type}, 错误: {error_msg}")
        return LangChainError(error_msg, card_no, chain_type)


# 便捷函数
def handle_database_error(operation: str, card_no: str, error: Exception) -> DatabaseError:
    """便捷的数据库错误处理函数"""
    return ErrorHandler.log_and_handle_database_error(operation, card_no, error)


def handle_llm_error(model_name: str, card_no: str, error: Exception) -> LLMAnalysisError:
    """便捷的大模型错误处理函数"""
    return ErrorHandler.log_and_handle_llm_error(model_name, card_no, error)


def handle_langchain_error(chain_type: str, card_no: str, error: Exception) -> LangChainError:
    """便捷的LangChain错误处理函数"""
    return ErrorHandler.log_and_handle_langchain_error(chain_type, card_no, error)


def create_error_response(card_no: str, error: Exception, default_message: str = "处理失败") -> Dict[str, Any]:
    """便捷的错误响应创建函数"""
    return ErrorHandler.create_error_response(card_no, error, default_message)