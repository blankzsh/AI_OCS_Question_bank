"""
FastAPI应用主模块
创建和配置FastAPI应用实例
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
import uvicorn
import json
import os
from contextlib import asynccontextmanager

from .config import get_settings
from .models.database import init_database, db_manager
from .api.routes import query
from .models.schemas import ErrorResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    print("正在启动AI智能题库系统...")

    # 初始化数据库
    if not init_database():
        print("数据库初始化失败")
        raise Exception("数据库初始化失败")

    print("数据库初始化成功")
    print("AI智能题库系统启动完成")

    yield

    # 关闭时执行
    print("正在关闭AI智能题库系统...")
    db_manager.close()
    print("系统已安全关闭")


def create_app() -> FastAPI:
    """创建FastAPI应用实例"""

    # 获取配置
    settings = get_settings()

    # 创建FastAPI应用
    app = FastAPI(
        title=settings.app.name,
        description=settings.app.description,
        version=settings.app.version,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )

    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.security.cors_origins,
        allow_credentials=True,
        allow_methods=settings.security.cors_methods,
        allow_headers=settings.security.cors_headers,
    )

    # 注册路由
    app.include_router(query.router)

    # 注册异常处理器
    register_exception_handlers(app)

    # 注册中间件
    register_middleware(app)

    return app


def register_exception_handlers(app: FastAPI):
    """注册异常处理器"""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """HTTP异常处理"""
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail if isinstance(exc.detail, dict) else {
                "success": False,
                "error": exc.detail,
                "error_code": f"HTTP_{exc.status_code}"
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """通用异常处理"""
        print(f"未处理的异常: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "服务器内部错误",
                "error_code": "INTERNAL_SERVER_ERROR"
            }
        )


def register_middleware(app: FastAPI):
    """注册中间件"""

    @app.middleware("http")
    async def logging_middleware(request: Request, call_next):
        """请求日志中间件"""
        # 记录请求
        print(f"[{request.method}] {request.url}")

        # 处理请求
        response = await call_next(request)

        # 记录响应状态
        print(f"[响应] {response.status_code}")

        return response


def print_api_config(host: str, port: int):
    """打印API配置信息"""
    settings = get_settings()

    # 如果host是0.0.0.0，在配置中显示为127.0.0.1
    display_host = "127.0.0.1" if host == "0.0.0.0" else host

    api_config = {
        "name": settings.app.name,
        "homepage": settings.app.homepage,
        "url": f"http://{display_host}:{port}/api/query",
        "method": "get",
        "type": "GM_xmlhttpRequest",
        "contentType": "json",
        "data": {
            "title": "${title}",
            "options": "${options}",
            "type": "${type}"
        },
        "handler": "return (res)=>res.code === 0 ? [undefined, undefined] : [undefined,res.data.data]"
    }

    print("\n" + "="*50)
    print("API配置信息:")
    print("="*50)
    print(json.dumps(api_config, ensure_ascii=False, indent=2))
    print("="*50)

    print(f"API文档地址: http://{display_host}:{port}/docs")
    print(f"ReDoc文档地址: http://{display_host}:{port}/redoc")
    print(f"健康检查地址: http://{display_host}:{port}/api/health")
    print("="*50)


def create_log_directory():
    """创建日志目录"""
    settings = get_settings()
    log_dir = os.path.dirname(settings.logging.file)

    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
        print(f"创建日志目录: {log_dir}")


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    # 创建日志目录
    create_log_directory()

    # 获取配置
    settings = get_settings()

    # 启动参数
    host = settings.server.host
    port = settings.server.port
    reload = settings.server.reload

    # 打印配置信息
    display_host = "127.0.0.1" if host == "0.0.0.0" else host
    print(f"启动FastAPI服务器")
    print(f"地址: http://{display_host}:{port}")
    print(f"热重载: {'开启' if reload else '关闭'}")
    print(f"调试模式: {'开启' if settings.app.debug else '关闭'}")

    # 打印API配置
    print_api_config(host, port)

    # 启动服务器
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=settings.logging.lower()
    )