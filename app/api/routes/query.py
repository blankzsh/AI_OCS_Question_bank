"""
查询相关的API路由
处理问题查询的主要业务接口
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any

from ...models.schemas import (
    QueryRequest, QueryResponse, QueryData,
    SystemInfo, HealthCheckResponse, AIConfigResponse, ErrorResponse
)
from ...models.database import get_db, QuestionAnswerRepository
from ...services.query_service import QueryService
from ...utils.ai_providers.factory import AIProviderFactory
from ...config import get_settings

# 创建路由器
router = APIRouter(prefix="/api", tags=["查询"])

# 全局设置
settings = get_settings()


@router.get("/query", response_model=QueryResponse)
async def query_answer(
    title: str = Query(..., description="问题标题"),
    options: str = Query("", description="选项内容"),
    type: str = Query("", description="问题类型"),
    db: Session = Depends(get_db)
):
    """
    查询问题答案接口

    兼容原有的API格式，支持GET请求

    Args:
        title: 问题标题
        options: 选项内容
        type: 问题类型
        db: 数据库会话

    Returns:
        QueryResponse: 查询响应结果
    """
    try:
        # 验证输入参数
        if not title or not title.strip():
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": "缺少题目参数",
                    "error_code": "MISSING_TITLE"
                }
            )

        # 创建查询请求
        request = QueryRequest(
            title=title.strip(),
            options=options,
            type=type
        )

        # 创建查询服务
        query_service = QueryService(db)

        # 执行查询
        result = query_service.query_answer(request)

        # 返回响应
        return QueryResponse(
            success=True,
            data=result
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] 查询接口异常: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": f"查询失败: {str(e)}",
                "error_code": "QUERY_ERROR"
            }
        )


@router.post("/query", response_model=QueryResponse)
async def query_answer_post(
    request: QueryRequest,
    db: Session = Depends(get_db)
):
    """
    查询问题答案接口 (POST版本)

    支持POST请求，使用JSON格式传参

    Args:
        request: 查询请求对象
        db: 数据库会话

    Returns:
        QueryResponse: 查询响应结果
    """
    try:
        # 创建查询服务
        query_service = QueryService(db)

        # 执行查询
        result = query_service.query_answer(request)

        # 返回响应
        return QueryResponse(
            success=True,
            data=result
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] POST查询接口异常: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": f"查询失败: {str(e)}",
                "error_code": "QUERY_ERROR"
            }
        )


@router.get("/stats", response_model=Dict[str, Any])
async def get_statistics(db: Session = Depends(get_db)):
    """
    获取系统统计信息

    Args:
        db: 数据库会话

    Returns:
        Dict: 统计信息
    """
    try:
        query_service = QueryService(db)
        return query_service.get_statistics()
    except Exception as e:
        print(f"[API] 获取统计信息失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": f"获取统计信息失败: {str(e)}",
                "error_code": "STATS_ERROR"
            }
        )


@router.get("/ai-providers", response_model=AIConfigResponse)
async def get_ai_providers():
    """
    获取AI提供商配置信息

    Returns:
        AIConfigResponse: AI配置响应
    """
    try:
        factory = AIProviderFactory()
        providers_info = factory.get_provider_info()

        # 转换为响应格式
        provider_list = []
        for name, info in providers_info.items():
            provider_list.append({
                "name": info["name"],
                "enabled": info["enabled"],
                "has_api_key": info["has_api_key"],
                "model": info["model"],
                "is_available": info["is_available"]
            })

        return AIConfigResponse(
            default_provider=settings.ai.default_provider,
            available_providers=provider_list,
            total_providers=len(provider_list)
        )

    except Exception as e:
        print(f"[API] 获取AI提供商信息失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": f"获取AI配置失败: {str(e)}",
                "error_code": "AI_CONFIG_ERROR"
            }
        )


@router.get("/system/info", response_model=SystemInfo)
async def get_system_info(db: Session = Depends(get_db)):
    """
    获取系统信息

    Args:
        db: 数据库会话

    Returns:
        SystemInfo: 系统信息
    """
    try:
        # 获取数据库状态
        repository = QuestionAnswerRepository(db)
        total_questions = repository.count_all()

        # 获取AI提供商数量
        factory = AIProviderFactory()
        available_providers = factory.get_available_providers()

        return SystemInfo(
            app_name=settings.app.name,
            version=settings.app.version,
            description=settings.app.description,
            homepage=settings.app.homepage,
            author="Toni Wang",
            email="shell7@petalmail.com",
            ai_providers_count=len(available_providers),
            database_status="connected" if total_questions >= 0 else "disconnected"
        )

    except Exception as e:
        print(f"[API] 获取系统信息失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": f"获取系统信息失败: {str(e)}",
                "error_code": "SYSTEM_INFO_ERROR"
            }
        )


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(db: Session = Depends(get_db)):
    """
    健康检查接口

    Args:
        db: 数据库会话

    Returns:
        HealthCheckResponse: 健康检查结果
    """
    from datetime import datetime

    try:
        # 检查数据库连接
        repository = QuestionAnswerRepository(db)
        db_status = "connected" if repository.count_all() >= 0 else "disconnected"

        # 检查AI提供商
        factory = AIProviderFactory()
        available_providers = factory.get_available_providers()

        return HealthCheckResponse(
            status="healthy",
            timestamp=datetime.now(),
            version=settings.app.version,
            database=db_status,
            ai_providers=len(available_providers)
        )

    except Exception as e:
        print(f"[API] 健康检查失败: {str(e)}")
        return HealthCheckResponse(
            status="unhealthy",
            timestamp=datetime.now(),
            version=settings.app.version,
            database="disconnected",
            ai_providers=0
        )


@router.post("/ai/switch/{provider_name}")
async def switch_ai_provider(
    provider_name: str,
    db: Session = Depends(get_db)
):
    """
    切换AI提供商

    Args:
        provider_name: 提供商名称
        db: 数据库会话

    Returns:
        Dict: 切换结果
    """
    try:
        query_service = QueryService(db)
        success = query_service.switch_ai_provider(provider_name)

        if success:
            return {
                "success": True,
                "message": f"已切换到AI提供商: {provider_name}"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": f"切换AI提供商失败: {provider_name}",
                    "error_code": "SWITCH_ERROR"
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] 切换AI提供商异常: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": f"切换失败: {str(e)}",
                "error_code": "SWITCH_ERROR"
            }
        )