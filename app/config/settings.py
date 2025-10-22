"""
配置管理模块
使用Pydantic进行配置验证和管理
"""

import os
import yaml
from typing import List, Optional, Dict, Any
from pydantic import Field, validator
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class DatabaseConfig(BaseSettings):
    """数据库配置"""
    url: str = Field(default="sqlite:///./question_bank.db", description="数据库连接URL")
    echo: bool = Field(default=False, description="是否打印SQL语句")
    pool_size: int = Field(default=5, description="连接池大小")
    max_overflow: int = Field(default=10, description="最大溢出连接数")


class ServerConfig(BaseSettings):
    """服务器配置"""
    host: str = Field(default="0.0.0.0", description="服务器主机")
    port: int = Field(default=8000, description="服务器端口")
    reload: bool = Field(default=False, description="是否开启热重载")


class ProviderConfig(BaseSettings):
    """AI提供商配置"""
    name: str = Field(description="提供商名称")
    enabled: bool = Field(default=True, description="是否启用")
    api_key: str = Field(default="", description="API密钥")
    base_url: str = Field(description="API基础URL")
    model: str = Field(description="模型名称")
    max_tokens: int = Field(default=512, description="最大令牌数")
    temperature: float = Field(default=0.1, description="温度参数")
    top_p: float = Field(default=0.9, description="Top-p参数")


class AIConfig(BaseSettings):
    """AI服务配置"""
    default_provider: str = Field(default="alibaba", description="默认AI提供商")
    timeout: int = Field(default=30, description="请求超时时间（秒）")
    max_retries: int = Field(default=3, description="最大重试次数")
    retry_delay: int = Field(default=2, description="重试延迟（秒）")


class LoggingConfig(BaseSettings):
    """日志配置"""
    level: str = Field(default="INFO", description="日志级别")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="日志格式"
    )
    file: str = Field(default="logs/app.log", description="日志文件路径")
    max_size: str = Field(default="10MB", description="日志文件最大大小")
    backup_count: int = Field(default=5, description="日志备份数量")


class CacheConfig(BaseSettings):
    """缓存配置"""
    enabled: bool = Field(default=True, description="是否启用缓存")
    ttl: int = Field(default=3600, description="缓存时间（秒）")


class SecurityConfig(BaseSettings):
    """安全配置"""
    cors_origins: List[str] = Field(default=["*"], description="允许的CORS源")
    cors_methods: List[str] = Field(default=["GET", "POST"], description="允许的CORS方法")
    cors_headers: List[str] = Field(default=["*"], description="允许的CORS头部")


class AppConfig(BaseSettings):
    """应用配置"""
    name: str = Field(default="ZE题库(自建版)", description="应用名称")
    version: str = Field(default="2.0.0", description="应用版本")
    description: str = Field(
        default="基于FastAPI的智能题库查询系统",
        description="应用描述"
    )
    homepage: str = Field(
        default="https://pages.zaizhexue.top/",
        description="应用主页"
    )
    debug: bool = Field(default=True, description="调试模式")


class Settings(BaseSettings):
    """全局配置"""
    app: AppConfig = Field(default_factory=AppConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    providers: Dict[str, ProviderConfig] = Field(default_factory=dict)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @classmethod
    def load_from_yaml(cls, file_path: str = "config.yaml") -> "Settings":
        """从YAML文件加载配置"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"配置文件不存在: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)

            # 处理providers配置
            providers = {}
            if 'providers' in config_data:
                for provider_name, provider_data in config_data['providers'].items():
                    providers[provider_name] = ProviderConfig(**provider_data)

            config_data['providers'] = providers

            return cls(**config_data)

        except yaml.YAMLError as e:
            raise ValueError(f"配置文件格式错误: {e}")
        except Exception as e:
            raise ValueError(f"加载配置文件失败: {e}")

    def get_provider_config(self, provider_name: str) -> Optional[ProviderConfig]:
        """获取指定提供商配置"""
        return self.providers.get(provider_name)

    def get_default_provider_config(self) -> Optional[ProviderConfig]:
        """获取默认提供商配置"""
        return self.get_provider_config(self.ai.default_provider)

    def list_enabled_providers(self) -> List[str]:
        """列出所有启用的提供商"""
        return [
            name for name, config in self.providers.items()
            if config.enabled and config.api_key
        ]


# 全局配置实例
settings = Settings.load_from_yaml()


def get_settings() -> Settings:
    """获取配置实例（依赖注入用）"""
    return settings


def reload_settings() -> Settings:
    """重新加载配置"""
    global settings
    settings = Settings.load_from_yaml()
    return settings