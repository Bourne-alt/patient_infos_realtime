"""
依赖注入管理模块
管理FastAPI依赖注入，提供数据库会话、服务等依赖
"""

import logging
from typing import Generator
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from singletons import get_database_session, get_medical_analyzer
from database_service import DatabaseService
from langchain_service import MedicalReportAnalyzer
from exceptions import ErrorHandler, DatabaseError

logger = logging.getLogger(__name__)

load_dotenv()


def get_db() -> Generator[Session, None, None]:
    """
    依赖注入：获取数据库会话
    
    Yields:
        数据库会话对象
    """
    db = None
    try:
        db = get_database_session()
        yield db
    except Exception as e:
        logger.error(f"数据库会话创建失败: {e}")
        if db:
            db.rollback()
        raise HTTPException(status_code=500, detail="数据库连接失败")
    finally:
        if db:
            db.close()


def get_database_service(db: Session = Depends(get_db)) -> DatabaseService:
    """
    依赖注入：获取数据库服务
    
    Args:
        db: 数据库会话（由FastAPI依赖注入提供）
        
    Returns:
        数据库服务实例
    """
    try:
        return DatabaseService(db)
    except Exception as e:
        logger.error(f"数据库服务创建失败: {e}")
        raise HTTPException(status_code=500, detail="数据库服务初始化失败")


def get_analyzer() -> MedicalReportAnalyzer:
    """
    依赖注入：获取医疗报告分析器
    
    Returns:
        医疗报告分析器实例
    """
    try:
        return get_medical_analyzer()
    except Exception as e:
        logger.error(f"分析器获取失败: {e}")
        raise HTTPException(status_code=500, detail="分析器服务不可用")


class ServiceContainer:
    """服务容器类 - 管理所有服务依赖"""
    
    def __init__(self):
        self._db_service = None
        self._analyzer = None
    
    def get_db_service(self, db: Session) -> DatabaseService:
        """获取数据库服务（带缓存）"""
        if self._db_service is None or self._db_service.db != db:
            self._db_service = DatabaseService(db)
        return self._db_service
    
    def get_analyzer(self) -> MedicalReportAnalyzer:
        """获取分析器（带缓存）"""
        if self._analyzer is None:
            self._analyzer = get_medical_analyzer()
        return self._analyzer


# 全局服务容器实例
service_container = ServiceContainer()


def get_service_container() -> ServiceContainer:
    """
    依赖注入：获取服务容器
    
    Returns:
        服务容器实例
    """
    return service_container


# 便捷的组合依赖
def get_services(
    db: Session = Depends(get_db),
    container: ServiceContainer = Depends(get_service_container)
) -> tuple[DatabaseService, MedicalReportAnalyzer]:
    """
    依赖注入：一次性获取数据库服务和分析器
    
    Args:
        db: 数据库会话
        container: 服务容器
        
    Returns:
        (数据库服务, 医疗报告分析器) 元组
    """
    try:
        db_service = container.get_db_service(db)
        analyzer = container.get_analyzer()
        return db_service, analyzer
    except Exception as e:
        logger.error(f"服务获取失败: {e}")
        raise HTTPException(status_code=500, detail="服务初始化失败")


# 用于健康检查的轻量级依赖
def get_health_check_db() -> Generator[Session, None, None]:
    """
    健康检查用的数据库连接（不抛出异常）
    
    Yields:
        数据库会话对象或None
    """
    db = None
    try:
        db = get_database_session()
        yield db
    except Exception as e:
        logger.warning(f"健康检查数据库连接失败: {e}")
        yield None
    finally:
        if db:
            try:
                db.close()
            except:
                pass  # 忽略关闭时的异常


def validate_request_data(card_no: str) -> str:
    """
    依赖注入：验证请求数据
    
    Args:
        card_no: 患者卡号
        
    Returns:
        验证后的卡号
        
    Raises:
        HTTPException: 如果数据验证失败
    """
    if not card_no or not card_no.strip():
        raise HTTPException(status_code=400, detail="患者卡号不能为空")
    
    # 简单的卡号格式验证
    card_no = card_no.strip()
    if len(card_no) < 3:
        raise HTTPException(status_code=400, detail="患者卡号格式错误")
    
    return card_no


# 中间件依赖
def log_request_info(request_info: dict = None):
    """
    依赖注入：记录请求信息
    
    Args:
        request_info: 请求信息字典
    """
    if request_info:
        logger.info(f"处理请求: {request_info}")


# 错误处理依赖
def get_error_handler() -> ErrorHandler:
    """
    依赖注入：获取错误处理器
    
    Returns:
        错误处理器实例
    """
    return ErrorHandler()


# 权限验证依赖（占位符，可以扩展）
def verify_permissions(required_permission: str = "basic"):
    """
    依赖注入：权限验证
    
    Args:
        required_permission: 需要的权限级别
        
    Returns:
        权限验证函数
    """
    def permission_checker():
        # 这里可以实现具体的权限验证逻辑
        # 目前只是占位符
        logger.debug(f"验证权限: {required_permission}")
        return True
    
    return permission_checker