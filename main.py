"""
AI问答系统启动入口
作者：Toni Wang (shell7@petalmail.com)

使用方法:
    python main.py

功能特性:
- FastAPI异步框架
- 多AI平台支持 (阿里百炼、DeepSeek、OpenAI、Google Studio)
- SQLite本地数据库缓存
- 模块化架构设计
- 自动API文档生成
"""

from app.main import app

if __name__ == "__main__":
    import uvicorn
    from app.config import get_settings

    # 获取配置
    settings = get_settings()

    # 启动参数
    host = settings.server.host
    port = settings.server.port
    reload = settings.server.reload

    print("AI智能题库系统 v2.0")
    print("="*50)
    print(f"作者: Toni Wang")
    print(f"邮箱: shell7@petalmail.com")
    print(f"地址: http://{host}:{port}")
    print("="*50)

    # 启动服务器
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )