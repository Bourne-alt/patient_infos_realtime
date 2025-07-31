"""
简化的配置管理模块
直接从.env文件读取环境变量，使用扁平化结构
"""

import os
from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# 确保加载.env文件
load_dotenv(override=True)


class Settings(BaseSettings):
    """应用程序配置 - 简化的扁平化结构"""
    
    # ========== 应用基本信息 ==========
    title: str = "医疗报告分析API"
    description: str = "接收医疗报告数据，调用大模型进行分析，并存储到数据库"
    version: str = "2.1.0"
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # ========== 数据库配置 ==========
    postgres_host: str = Field(default="10.1.27.65", env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")
    postgres_database: str = Field(default="patient_info", env="POSTGRES_DATABASE")
    postgres_user: str = Field(default="postgres", env="POSTGRES_USER")
    postgres_password: str = Field(default="admin123", env="POSTGRES_PASSWORD")
    
    # 数据库连接池配置
    db_pool_size: int = Field(default=8, env="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=15, env="DB_MAX_OVERFLOW")
    db_pool_timeout: int = Field(default=20, env="DB_POOL_TIMEOUT")
    db_pool_recycle: int = Field(default=1800, env="DB_POOL_RECYCLE")
    
    # ========== LLM配置 ==========
    # 优先读取.env文件中的值，如果没有则使用默认值
    openai_api_url: str = Field(
        default=os.getenv("OPENAI_BASE_URL", "http://localhost:11434/api/generate"), 
        env="OPENAI_BASE_URL"
    )
    openai_model: str = Field(
        default=os.getenv("OPENAI_MODEL", "llama3.1"), 
        env="OPENAI_MODEL"
    )
    openai_api_key: str = Field(
        default=os.getenv("OPENAI_API_KEY", "sk-proj-1234567890"), 
        env="OPENAI_API_KEY"
    )
    
    # LLM请求配置
    llm_timeout: int = Field(default=120, env="LLM_TIMEOUT")
    llm_temperature: float = Field(default=0.7, env="LLM_TEMPERATURE")
    llm_top_p: float = Field(default=0.9, env="LLM_TOP_P")
    llm_max_tokens: int = Field(default=2000, env="LLM_MAX_TOKENS")
    
    # LLM缓存配置
    llm_cache_enabled: bool = Field(default=True, env="LLM_CACHE_ENABLED")
    llm_cache_size: int = Field(default=200, env="LLM_CACHE_SIZE")
    llm_cache_ttl_hours: int = Field(default=12, env="LLM_CACHE_TTL_HOURS")
    
    # ========== 服务器配置 ==========
    server_host: str = Field(default="0.0.0.0", env="HOST")
    server_port: int = Field(default=7700, env="PORT")
    workers: int = Field(default=1, env="WORKERS")
    
    # CORS配置
    cors_origins: str = Field(default="http://localhost:3000", env="CORS_ORIGINS")
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    
    # 日志配置
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="medical_report_api.log", env="LOG_FILE")
    
    # ========== 其他配置 ==========
    enable_request_logging: bool = Field(default=True, env="ENABLE_REQUEST_LOGGING")
    cache_cleanup_interval: int = Field(default=3600, env="CACHE_CLEANUP_INTERVAL")
    
    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.environment.lower() == "development"
    
    @property
    def database_url(self) -> str:
        """构建数据库连接URL"""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_database}"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """获取CORS允许的源列表"""
        if isinstance(self.cors_origins, str):
            return [origin.strip() for origin in self.cors_origins.split(",")]
        return [self.cors_origins]
    
    @property
    def is_llm_configured(self) -> bool:
        """检查LLM是否已正确配置"""
        return self.openai_api_key != "sk-proj-1234567890" and len(self.openai_api_key) > 20
    
    def get_cors_config(self) -> dict:
        """获取CORS配置"""
        if self.is_production:
            # 生产环境使用严格的CORS设置
            return {
                "allow_origins": self.cors_origins_list,
                "allow_credentials": self.cors_allow_credentials,
                "allow_methods": ["GET", "POST"],
                "allow_headers": ["Content-Type", "Authorization"]
            }
        else:
            # 开发环境使用宽松的CORS设置
            return {
                "allow_origins": ["*"],
                "allow_credentials": True,
                "allow_methods": ["*"],
                "allow_headers": ["*"]
            }
    
    class Config:
        # 从.env文件加载配置
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "allow"  # 允许额外的环境变量


# 创建全局配置实例
def create_settings() -> Settings:
    """创建配置实例"""
    return Settings()


# 全局配置实例
settings = create_settings()


def get_settings() -> Settings:
    """获取应用配置（用于依赖注入）"""
    return settings


# 配置验证函数
def validate_configuration():
    """验证配置是否正确"""
    errors = []
    
    # 验证数据库配置
    try:
        # 尝试构建数据库URL
        db_url = settings.database_url
        if not db_url:
            errors.append("数据库URL构建失败")
    except Exception as e:
        errors.append(f"数据库配置错误: {e}")
    
    # 验证LLM配置
    if not settings.openai_api_url:
        errors.append("LLM API URL未配置")
    
    # 验证服务器配置
    if settings.server_port < 1 or settings.server_port > 65535:
        errors.append("服务器端口配置错误")
    
    if errors:
        error_msg = "配置验证失败:\n" + "\n".join(f"- {error}" for error in errors)
        raise ValueError(error_msg)
    
    return True


# 配置摘要函数（用于健康检查）
def get_config_summary() -> dict:
    """获取配置摘要（隐藏敏感信息）"""
    return {
        "application": {
            "title": settings.title,
            "version": settings.version,
            "environment": settings.environment,
            "debug": settings.debug
        },
        "database": {
            "host": settings.postgres_host,
            "port": settings.postgres_port,
            "database": settings.postgres_database,
            "pool_size": settings.db_pool_size,
            "max_overflow": settings.db_max_overflow
        },
        "llm": {
            "model": settings.openai_model,
            "api_configured": settings.is_llm_configured,
            "cache_enabled": settings.llm_cache_enabled,
            "cache_size": settings.llm_cache_size,
            "api_url": settings.openai_api_url
        },
        "server": {
            "host": settings.server_host,
            "port": settings.server_port,
            "cors_origins_count": len(settings.cors_origins_list)
        }
    }


# 为了向后兼容，提供分组配置访问方式
class DatabaseConfig:
    """数据库配置向后兼容类"""
    def __init__(self, settings: Settings):
        self.host = settings.postgres_host
        self.port = settings.postgres_port
        self.database = settings.postgres_database
        self.user = settings.postgres_user
        self.password = settings.postgres_password
        self.pool_size = settings.db_pool_size
        self.max_overflow = settings.db_max_overflow
        self.pool_timeout = settings.db_pool_timeout
        self.pool_recycle = settings.db_pool_recycle
    
    @property
    def url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class LLMConfig:
    """LLM配置向后兼容类"""
    def __init__(self, settings: Settings):
        self.api_url = settings.openai_api_url
        self.model = settings.openai_model
        self.api_key = settings.openai_api_key
        self.timeout = settings.llm_timeout
        self.temperature = settings.llm_temperature
        self.top_p = settings.llm_top_p
        self.max_tokens = settings.llm_max_tokens
        self.cache_enabled = settings.llm_cache_enabled
        self.cache_size = settings.llm_cache_size
        self.cache_ttl_hours = settings.llm_cache_ttl_hours
    
    @property
    def is_configured(self) -> bool:
        return settings.is_llm_configured


class ServerConfig:
    """服务器配置向后兼容类"""
    def __init__(self, settings: Settings):
        self.host = settings.server_host
        self.port = settings.server_port
        self.cors_origins = settings.cors_origins_list
        self.cors_allow_credentials = settings.cors_allow_credentials
        self.log_level = settings.log_level
        self.log_file = settings.log_file
        self.workers = settings.workers


# 向后兼容：为settings添加分组属性
settings.database = DatabaseConfig(settings)
settings.llm = LLMConfig(settings)
settings.server = ServerConfig(settings)


if __name__ == "__main__":
    # 测试配置加载
    try:
        validate_configuration()
        print("✅ 配置验证通过")
        print("\n📋 配置摘要:")
        import json
        print(json.dumps(get_config_summary(), indent=2, ensure_ascii=False))
        
        print("\n🔍 关键配置值:")
        print(f"数据库URL: {settings.database_url}")
        print(f"LLM API URL: {settings.openai_api_url}")
        print(f"LLM Model: {settings.openai_model}")
        print(f"LLM已配置: {settings.is_llm_configured}")
        print(f"服务器地址: {settings.server_host}:{settings.server_port}")
        
    except Exception as e:
        print(f"❌ 配置验证失败: {e}")
        import traceback
        traceback.print_exc()