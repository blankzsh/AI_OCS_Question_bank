"""
Pydantic数据模型定义
用于API请求和响应的数据验证和序列化
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from datetime import datetime


# 请求模型
class QueryRequest(BaseModel):
    """查询请求模型"""
    title: str = Field(..., min_length=1, max_length=1000, description="问题标题")
    options: Optional[str] = Field("", max_length=2000, description="选项内容")
    type: Optional[str] = Field("", max_length=50, description="问题类型")

    @validator('title')
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError('问题标题不能为空')
        return v.strip()

    @validator('options')
    def validate_options(cls, v):
        if v is None:
            return ""
        return v

    @validator('type')
    def validate_type(cls, v):
        if v is None:
            return ""
        # 支持的问题类型
        allowed_types = ["", "选择题", "多选题", "填空题", "判断题", "judgement", "single", "multiple", "fill", "truefalse", "choice"]
        if v not in allowed_types:
            raise ValueError(f'不支持的问题类型: {v}')
        return v

    class Config:
        schema_extra = {
            "example": {
                "title": "中国的首都是哪里？",
                "options": "A. 北京 B. 上海 C. 广州 D. 深圳",
                "type": "选择题"
            }
        }


# 响应模型
class QueryResponse(BaseModel):
    """查询响应模型"""
    success: bool = Field(..., description="请求是否成功")
    data: Optional['QueryData'] = Field(None, description="查询结果数据")
    error: Optional[str] = Field(None, description="错误信息")

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "code": 1,
                    "data": "北京",
                    "msg": "AI回答",
                    "source": "ai"
                }
            }
        }


class QueryData(BaseModel):
    """查询数据模型"""
    code: int = Field(..., description="状态码 (0:未找到答案, 1:找到答案)")
    data: Optional[str] = Field(None, description="答案内容")
    msg: str = Field(..., description="消息说明")
    source: str = Field(..., description="答案来源 (public:本地数据库, ai:AI回答)")

    @validator('code')
    def validate_code(cls, v):
        if v not in [0, 1]:
            raise ValueError('状态码只能是0或1')
        return v

    @validator('source')
    def validate_source(cls, v):
        allowed_sources = ["public", "ai"]
        if v not in allowed_sources:
            raise ValueError(f'不支持的答案来源: {v}')
        return v

    class Config:
        schema_extra = {
            "example": {
                "code": 1,
                "data": "北京",
                "msg": "AI回答",
                "source": "ai"
            }
        }


# 数据库模型（ORM）
class QuestionAnswerDB(BaseModel):
    """问题答案数据库模型"""
    id: Optional[int] = Field(None, description="记录ID")
    question: str = Field(..., description="问题内容")
    answer: str = Field(..., description="答案内容")
    options: Optional[str] = Field("", description="选项内容")
    type: Optional[str] = Field("", description="问题类型")
    created_at: Optional[datetime] = Field(None, description="创建时间")

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "question": "中国的首都是哪里？",
                "answer": "北京",
                "options": "A. 北京 B. 上海 C. 广州 D. 深圳",
                "type": "选择题",
                "created_at": "2024-01-01T00:00:00"
            }
        }


# AI相关模型
class AIProviderInfo(BaseModel):
    """AI提供商信息模型"""
    name: str = Field(..., description="提供商名称")
    enabled: bool = Field(..., description="是否启用")
    has_api_key: bool = Field(..., description="是否有API密钥")
    model: str = Field(..., description="模型名称")
    is_available: bool = Field(..., description="是否可用")

    class Config:
        schema_extra = {
            "example": {
                "name": "阿里百炼",
                "enabled": True,
                "has_api_key": True,
                "model": "qwen-turbo",
                "is_available": True
            }
        }


class AIConfigResponse(BaseModel):
    """AI配置响应模型"""
    default_provider: str = Field(..., description="默认提供商")
    available_providers: List[AIProviderInfo] = Field(..., description="可用提供商列表")
    total_providers: int = Field(..., description="总提供商数量")

    class Config:
        schema_extra = {
            "example": {
                "default_provider": "alibaba",
                "available_providers": [
                    {
                        "name": "阿里百炼",
                        "enabled": True,
                        "has_api_key": True,
                        "model": "qwen-turbo",
                        "is_available": True
                    }
                ],
                "total_providers": 1
            }
        }


# 系统信息模型
class SystemInfo(BaseModel):
    """系统信息模型"""
    app_name: str = Field(..., description="应用名称")
    version: str = Field(..., description="应用版本")
    description: str = Field(..., description="应用描述")
    homepage: str = Field(..., description="应用主页")
    author: str = Field(..., description="作者")
    email: str = Field(..., description="邮箱")
    ai_providers_count: int = Field(..., description="AI提供商数量")
    database_status: str = Field(..., description="数据库状态")

    class Config:
        schema_extra = {
            "example": {
                "app_name": "ZE题库(自建版)",
                "version": "2.0.0",
                "description": "基于FastAPI的智能题库查询系统",
                "homepage": "https://pages.zaizhexue.top/",
                "author": "Toni Wang",
                "email": "shell7@petalmail.com",
                "ai_providers_count": 4,
                "database_status": "connected"
            }
        }


# 错误响应模型
class ErrorResponse(BaseModel):
    """错误响应模型"""
    success: bool = Field(False, description="请求失败")
    error: str = Field(..., description="错误信息")
    error_code: Optional[str] = Field(None, description="错误代码")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")

    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "error": "缺少题目参数",
                "error_code": "MISSING_TITLE",
                "details": {
                    "field": "title",
                    "message": "题目参数不能为空"
                }
            }
        }


# 健康检查模型
class HealthCheckResponse(BaseModel):
    """健康检查响应模型"""
    status: str = Field(..., description="服务状态")
    timestamp: datetime = Field(..., description="检查时间")
    version: str = Field(..., description="应用版本")
    database: str = Field(..., description="数据库状态")
    ai_providers: int = Field(..., description="可用AI提供商数量")

    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2024-01-01T00:00:00",
                "version": "2.0.0",
                "database": "connected",
                "ai_providers": 2
            }
        }