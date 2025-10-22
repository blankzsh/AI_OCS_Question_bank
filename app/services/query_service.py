"""
查询服务业务逻辑
处理问题查询的核心业务逻辑
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from ..models.schemas import QueryRequest, QueryData
from ..models.database import QuestionAnswerRepository
from ..utils.ai_providers.factory import AIProviderFactory
from ..config import get_settings


class QueryService:
    """查询服务类"""

    def __init__(self, db: Session):
        self.db = db
        self.repository = QuestionAnswerRepository(db)
        self.settings = get_settings()
        self.ai_factory = AIProviderFactory()

    def query_answer(self, request: QueryRequest) -> QueryData:
        """
        查询问题答案

        Args:
            request: 查询请求

        Returns:
            QueryData: 查询结果数据
        """
        try:
            print(f"[查询服务] 开始查询: {request.title[:50]}...")

            # 1. 首先查询本地数据库
            local_answer = self._query_local_database(request.title)
            if local_answer:
                print(f"[查询服务] 从本地数据库找到答案")
                return QueryData(
                    code=1,
                    data=local_answer.answer,
                    msg="来于本地数据库题库",
                    source="public"
                )

            # 2. 使用AI查询
            ai_answer = self._query_ai_provider(request)
            if ai_answer and self._is_valid_answer(ai_answer):
                print(f"[查询服务] AI返回有效答案")

                # 3. 保存到数据库
                self._save_to_database(request, ai_answer)

                return QueryData(
                    code=1,
                    data=ai_answer,
                    msg="AI回答",
                    source="ai"
                )
            else:
                print(f"[查询服务] AI未返回有效答案")
                return QueryData(
                    code=0,
                    data=None,
                    msg="未找到答案",
                    source="ai"
                )

        except Exception as e:
            print(f"[查询服务] 查询过程发生异常: {str(e)}")
            return QueryData(
                code=0,
                data=None,
                msg=f"查询失败: {str(e)}",
                source="system"
            )

    def _query_local_database(self, question: str) -> Optional[Any]:
        """
        查询本地数据库

        Args:
            question: 问题内容

        Returns:
            数据库记录或None
        """
        try:
            return self.repository.find_by_question(question)
        except Exception as e:
            print(f"[查询服务] 数据库查询失败: {str(e)}")
            return None

    def _query_ai_provider(self, request: QueryRequest) -> Optional[str]:
        """
        使用AI提供商查询答案

        Args:
            request: 查询请求

        Returns:
            AI返回的答案或None
        """
        try:
            # 获取默认AI提供商
            provider = self.ai_factory.get_default_provider()
            if not provider:
                print(f"[查询服务] 没有可用的AI提供商")
                return None

            print(f"[查询服务] 使用AI提供商: {provider.get_name()}")

            # 调用AI查询
            answer = provider.query(
                question=request.title,
                options=request.options or "",
                question_type=request.type or ""
            )

            return answer

        except Exception as e:
            print(f"[查询服务] AI查询失败: {str(e)}")
            return None

    def _is_valid_answer(self, answer: str) -> bool:
        """
        检查答案是否有效

        Args:
            answer: AI返回的答案

        Returns:
            bool: 答案是否有效
        """
        if not answer or not answer.strip():
            return False

        # 检查是否包含错误信息
        error_keywords = [
            "API调用失败",
            "无法从API获取答案",
            "API请求异常",
            "调用失败",
            "解析失败",
            "超时",
            "错误"
        ]

        answer_lower = answer.lower()
        for keyword in error_keywords:
            if keyword in answer_lower:
                return False

        return True

    def _save_to_database(self, request: QueryRequest, answer: str):
        """
        保存答案到数据库

        Args:
            request: 查询请求
            answer: 答案内容
        """
        try:
            self.repository.create(
                question=request.title,
                answer=answer,
                options=request.options or "",
                question_type=request.type or ""
            )
            print(f"[查询服务] 答案已保存到数据库")
        except Exception as e:
            print(f"[查询服务] 保存到数据库失败: {str(e)}")

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取查询统计信息

        Returns:
            Dict: 统计信息
        """
        try:
            total_questions = self.repository.count_all()
            recent_questions = self.repository.list_recent(5)

            # 获取AI提供商信息
            ai_providers_info = self.ai_factory.get_provider_info()
            available_providers = [
                name for name, info in ai_providers_info.items()
                if info["is_available"]
            ]

            return {
                "total_questions": total_questions,
                "available_ai_providers": len(available_providers),
                "recent_questions": [
                    {
                        "question": q.question[:100] + "..." if len(q.question) > 100 else q.question,
                        "answer": q.answer[:50] + "..." if len(q.answer) > 50 else q.answer,
                        "created_at": q.created_at.isoformat() if q.created_at else None
                    }
                    for q in recent_questions
                ],
                "ai_providers": available_providers
            }

        except Exception as e:
            print(f"[查询服务] 获取统计信息失败: {str(e)}")
            return {
                "total_questions": 0,
                "available_ai_providers": 0,
                "recent_questions": [],
                "ai_providers": []
            }

    def switch_ai_provider(self, provider_name: str) -> bool:
        """
        切换AI提供商

        Args:
            provider_name: 提供商名称

        Returns:
            bool: 是否切换成功
        """
        try:
            # 检查提供商是否存在且可用
            provider = self.ai_factory.create_provider(provider_name)
            if not provider or not provider.is_enabled():
                print(f"[查询服务] 提供商不可用: {provider_name}")
                return False

            # 这里可以实现动态切换配置的逻辑
            print(f"[查询服务] 已切换到AI提供商: {provider_name}")
            return True

        except Exception as e:
            print(f"[查询服务] 切换AI提供商失败: {str(e)}")
            return False

    def get_ai_providers_status(self) -> Dict[str, Any]:
        """
        获取AI提供商状态

        Returns:
            Dict: AI提供商状态信息
        """
        try:
            providers_info = self.ai_factory.get_provider_info()
            default_provider = self.settings.ai.default_provider

            return {
                "default_provider": default_provider,
                "providers": providers_info,
                "total_count": len(providers_info),
                "available_count": len([
                    name for name, info in providers_info.items()
                    if info["is_available"]
                ])
            }

        except Exception as e:
            print(f"[查询服务] 获取AI提供商状态失败: {str(e)}")
            return {
                "default_provider": "",
                "providers": {},
                "total_count": 0,
                "available_count": 0
            }