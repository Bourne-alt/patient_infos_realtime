"""
单例模式管理模块
管理应用中的单例对象，如数据库连接、LangChain分析器等
"""

import os
import logging
from typing import Optional, Dict, Any
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import threading

from langchain_service import MedicalReportAnalyzer

logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库连接管理器 - 单例模式"""
    
    _instance: Optional['DatabaseManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'DatabaseManager':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        # 数据库配置
        self.host = os.getenv("POSTGRES_HOST", "10.1.27.65")
        self.port = os.getenv("POSTGRES_PORT", "5432")
        self.database = os.getenv("POSTGRES_DATABASE", "patient_info")
        self.user = os.getenv("POSTGRES_USER", "postgres")
        self.password = os.getenv("POSTGRES_PASSWORD", "admin123")
        
        # 构建连接URL
        self.database_url = f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
        
        # 创建引擎（带连接池优化）
        self.engine = create_engine(
            self.database_url,
            echo=False,
            # 连接池配置
            poolclass=QueuePool,
            pool_size=10,          # 连接池大小
            max_overflow=20,       # 最大溢出连接数
            pool_timeout=30,       # 获取连接超时时间
            pool_recycle=3600,     # 连接回收时间（1小时）
            pool_pre_ping=True,    # 连接前ping测试
            # 性能优化配置
            connect_args={
                "options": "-c timezone=utc",
                "connect_timeout": 10,
                "application_name": "medical_report_api"
            }
        )
        
        # 创建会话工厂
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        self._initialized = True
        logger.info(f"数据库管理器初始化完成 - 连接池大小: 10, 最大溢出: 20")
    
    def get_engine(self) -> Engine:
        """获取数据库引擎"""
        return self.engine
    
    def get_session_factory(self):
        """获取会话工厂"""
        return self.SessionLocal
    
    @contextmanager
    def get_session(self):
        """获取数据库会话的上下文管理器"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def create_session(self) -> Session:
        """创建新的数据库会话"""
        return self.SessionLocal()
    
    def get_connection_info(self) -> Dict[str, Any]:
        """获取连接信息（用于健康检查）"""
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "pool_size": self.engine.pool.size(),
            "checked_in": self.engine.pool.checkedin(),
            "checked_out": self.engine.pool.checkedout(),
            "overflow": self.engine.pool.overflow()
        }


class AnalyzerManager:
    """分析器管理器 - 单例模式"""
    
    _instance: Optional['AnalyzerManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'AnalyzerManager':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        try:
            # 初始化医疗报告分析器
            self.medical_analyzer = MedicalReportAnalyzer()
            self._initialized = True
            logger.info("分析器管理器初始化完成")
        except Exception as e:
            logger.error(f"分析器管理器初始化失败: {e}")
            raise
    
    def get_medical_analyzer(self) -> MedicalReportAnalyzer:
        """获取医疗报告分析器"""
        return self.medical_analyzer
    
    def get_analyzer_info(self) -> Dict[str, Any]:
        """获取分析器信息"""
        return {
            "model_name": getattr(self.medical_analyzer, 'model_name', 'unknown'),
            "use_local_model": getattr(self.medical_analyzer, 'use_local_model', False),
            "openai_api_base": getattr(self.medical_analyzer, 'openai_api_base', 'not_configured'),
            "initialized": self._initialized
        }


# 全局单例实例
database_manager = DatabaseManager()
analyzer_manager = AnalyzerManager()


# 便捷函数
def get_database_session():
    """获取数据库会话的便捷函数"""
    return database_manager.create_session()


def get_medical_analyzer() -> MedicalReportAnalyzer:
    """获取医疗报告分析器的便捷函数"""
    return analyzer_manager.get_medical_analyzer()


def get_database_engine() -> Engine:
    """获取数据库引擎的便捷函数"""
    return database_manager.get_engine()


def get_connection_info() -> Dict[str, Any]:
    """获取所有连接信息的便捷函数"""
    return {
        "database": database_manager.get_connection_info(),
        "analyzer": analyzer_manager.get_analyzer_info()
    }