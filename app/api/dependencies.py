"""
API依赖注入模块
定义FastAPI的依赖项
"""

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from ..models.database import get_db
from ..services.query_service import QueryService


def get_query_service(db: Session = Depends(get_db)) -> QueryService:
    """
    获取查询服务实例

    Args:
        db: 数据库会话

    Returns:
        QueryService: 查询服务实例
    """
    return QueryService(db)