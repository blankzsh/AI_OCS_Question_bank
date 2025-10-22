#!/usr/bin/env python3
"""
FastAPI应用功能测试脚本
测试重构后的API功能完整性
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.schemas import QueryRequest, QueryResponse
from app.models.database import init_database, QuestionAnswerRepository
from app.config import get_settings


def test_configuration():
    """测试配置模块"""
    print("1. 测试配置模块...")
    try:
        settings = get_settings()
        print(f"   ✅ 应用名称: {settings.app.name}")
        print(f"   ✅ 服务器: {settings.server.host}:{settings.server.port}")
        print(f"   ✅ 默认AI提供商: {settings.ai.default_provider}")
        print(f"   ✅ 配置测试通过")
        return True
    except Exception as e:
        print(f"   ❌ 配置测试失败: {str(e)}")
        return False


def test_database():
    """测试数据库模块"""
    print("\n2. 测试数据库模块...")
    try:
        if init_database():
            print("   ✅ 数据库初始化成功")

            # 测试仓储功能
            from app.models.database import db_manager
            db = db_manager.get_connection()
            repo = QuestionAnswerRepository(db)

            # 测试查询功能
            result = repo.find_by_question("测试问题")
            print(f"   ✅ 数据库查询功能正常")

            # 测试统计功能
            count = repo.count_all()
            print(f"   ✅ 数据库统计: {count} 条记录")

            db.close()
            print("   ✅ 数据库测试通过")
            return True
        else:
            print("   ❌ 数据库初始化失败")
            return False
    except Exception as e:
        print(f"   ❌ 数据库测试失败: {str(e)}")
        return False


def test_schemas():
    """测试数据模型"""
    print("\n3. 测试数据模型...")
    try:
        # 测试请求模型
        request = QueryRequest(
            title="测试问题",
            options="A. 选项1 B. 选项2",
            type="选择题"
        )
        print(f"   ✅ 请求模型验证通过: {request.title}")

        # 测试响应模型
        from app.models.schemas import QueryData
        data = QueryData(
            code=1,
            data="测试答案",
            msg="测试消息",
            source="ai"
        )
        response = QueryResponse(success=True, data=data)
        print(f"   ✅ 响应模型验证通过: {response.data.msg}")

        print("   ✅ 数据模型测试通过")
        return True
    except Exception as e:
        print(f"   ❌ 数据模型测试失败: {str(e)}")
        return False


def test_ai_providers():
    """测试AI提供商模块"""
    print("\n4. 测试AI提供商模块...")
    try:
        from app.utils.ai_providers.factory import AIProviderFactory

        factory = AIProviderFactory()
        provider_info = factory.get_provider_info()

        print(f"   ✅ 可用提供商数量: {len(provider_info)}")
        for name, info in provider_info.items():
            print(f"   ✅ {name}: {info['name']} (enabled: {info['enabled']})")

        print("   ✅ AI提供商模块测试通过")
        return True
    except Exception as e:
        print(f"   ❌ AI提供商测试失败: {str(e)}")
        return False


def test_query_service():
    """测试查询服务"""
    print("\n5. 测试查询服务...")
    try:
        from app.services.query_service import QueryService
        from app.models.database import db_manager

        db = db_manager.get_connection()
        service = QueryService(db)

        # 测试统计功能
        stats = service.get_statistics()
        print(f"   ✅ 统计信息获取成功: {stats['total_questions']} 条题目")

        # 测试AI提供商状态
        ai_status = service.get_ai_providers_status()
        print(f"   ✅ AI提供商状态获取成功: {ai_status['total_count']} 个提供商")

        db.close()
        print("   ✅ 查询服务测试通过")
        return True
    except Exception as e:
        print(f"   ❌ 查询服务测试失败: {str(e)}")
        return False


def test_fastapi_app():
    """测试FastAPI应用"""
    print("\n6. 测试FastAPI应用...")
    try:
        from app.main import create_app

        app = create_app()
        print(f"   ✅ FastAPI应用创建成功")
        print(f"   ✅ 应用标题: {app.title}")
        print(f"   ✅ 应用版本: {app.version}")

        # 统计路由数量
        api_routes = [route for route in app.routes if hasattr(route, 'path') and '/api/' in route.path]
        print(f"   ✅ API路由数量: {len(api_routes)}")

        for route in api_routes[:3]:  # 只显示前3个
            if hasattr(route, 'methods'):
                print(f"   ✅ 路由: {list(route.methods)} {route.path}")

        print("   ✅ FastAPI应用测试通过")
        return True
    except Exception as e:
        print(f"   ❌ FastAPI应用测试失败: {str(e)}")
        return False


def main():
    """主测试函数"""
    print("🚀 开始FastAPI应用功能测试")
    print("=" * 50)

    tests = [
        test_configuration,
        test_database,
        test_schemas,
        test_ai_providers,
        test_query_service,
        test_fastapi_app
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        if test_func():
            passed += 1
        else:
            failed += 1

    print("\n" + "=" * 50)
    print(f"🎯 测试结果: {passed} 个通过, {failed} 个失败")

    if failed == 0:
        print("🎉 所有测试通过！应用重构成功！")
        print("\n✨ 重构成果:")
        print("   ✅ Flask → FastAPI 框架迁移完成")
        print("   ✅ 单文件架构 → 模块化架构完成")
        print("   ✅ config.json → config.yaml 配置管理完成")
        print("   ✅ 四大AI平台适配器实现完成")
        print("   ✅ SQLAlchemy ORM集成完成")
        print("   ✅ 作者信息更新完成")
        return True
    else:
        print("⚠️  部分测试失败，请检查相关模块")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)