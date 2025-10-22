"""
AI服务提供商工厂模式
用于创建和管理不同的AI提供商实例
"""

from typing import Dict, Optional
from ...config import get_settings
from .base import AIProviderBase
from .alibaba import AlibabaProvider
from .deepseek import DeepSeekProvider
from .openai import OpenAIProvider
from .google import GoogleProvider


class AIProviderFactory:
    """AI提供商工厂类"""

    # 提供商映射表
    _providers_map: Dict[str, type] = {
        'alibaba': AlibabaProvider,
        'deepseek': DeepSeekProvider,
        'openai': OpenAIProvider,
        'google': GoogleProvider,
    }

    # 缓存实例
    _instances_cache: Dict[str, AIProviderBase] = {}

    @classmethod
    def create_provider(cls, provider_name: str) -> Optional[AIProviderBase]:
        """
        创建AI提供商实例

        Args:
            provider_name: 提供商名称

        Returns:
            AIProviderBase: 提供商实例，如果创建失败返回None
        """
        # 检查缓存
        if provider_name in cls._instances_cache:
            return cls._instances_cache[provider_name]

        # 获取配置
        settings = get_settings()
        provider_config = settings.get_provider_config(provider_name)

        if not provider_config:
            print(f"[Factory] 未找到提供商配置: {provider_name}")
            return None

        # 检查提供商是否支持
        if provider_name not in cls._providers_map:
            print(f"[Factory] 不支持的提供商: {provider_name}")
            return None

        try:
            # 创建实例
            provider_class = cls._providers_map[provider_name]
            instance = provider_class(provider_config.dict())

            # 检查是否启用
            if not instance.is_enabled():
                print(f"[Factory] 提供商未启用或缺少API密钥: {provider_name}")
                return None

            # 缓存实例
            cls._instances_cache[provider_name] = instance

            print(f"[Factory] 成功创建提供商实例: {provider_name}")
            return instance

        except Exception as e:
            print(f"[Factory] 创建提供商实例失败: {provider_name}, 错误: {str(e)}")
            return None

    @classmethod
    def get_default_provider(cls) -> Optional[AIProviderBase]:
        """
        获取默认提供商实例

        Returns:
            AIProviderBase: 默认提供商实例
        """
        settings = get_settings()
        default_provider_name = settings.ai.default_provider
        return cls.create_provider(default_provider_name)

    @classmethod
    def get_available_providers(cls) -> Dict[str, AIProviderBase]:
        """
        获取所有可用的提供商实例

        Returns:
            Dict[str, AIProviderBase]: 可用提供商字典
        """
        settings = get_settings()
        available_providers = {}

        for provider_name in cls._providers_map.keys():
            provider = cls.create_provider(provider_name)
            if provider and provider.is_enabled():
                available_providers[provider_name] = provider

        return available_providers

    @classmethod
    def get_provider_names(cls) -> list[str]:
        """
        获取所有支持的提供商名称

        Returns:
            list[str]: 提供商名称列表
        """
        return list(cls._providers_map.keys())

    @classmethod
    def register_provider(cls, name: str, provider_class: type):
        """
        注册新的提供商

        Args:
            name: 提供商名称
            provider_class: 提供商类
        """
        if not issubclass(provider_class, AIProviderBase):
            raise ValueError("提供商类必须继承自AIProviderBase")

        cls._providers_map[name] = provider_class
        print(f"[Factory] 注册新提供商: {name}")

    @classmethod
    def clear_cache(cls):
        """清空实例缓存"""
        cls._instances_cache.clear()
        print("[Factory] 已清空提供商实例缓存")

    @classmethod
    def get_provider_info(cls) -> Dict[str, Dict[str, any]]:
        """
        获取所有提供商的信息

        Returns:
            Dict: 提供商信息字典
        """
        settings = get_settings()
        info = {}

        for provider_name in cls._providers_map.keys():
            provider_config = settings.get_provider_config(provider_name)
            if provider_config:
                provider = cls.create_provider(provider_name)
                info[provider_name] = {
                    'name': provider_config.name,
                    'enabled': provider_config.enabled,
                    'has_api_key': bool(provider_config.api_key),
                    'model': provider_config.model,
                    'is_available': provider.is_enabled() if provider else False
                }

        return info