"""
OpenAI AI服务适配器
支持OpenAI平台的AI模型调用
"""

import json
from typing import Dict, Any
from .base import AIProviderBase


class OpenAIProvider(AIProviderBase):
    """OpenAI AI服务提供商"""

    def query(self, question: str, options: str = "", question_type: str = "") -> str:
        """
        查询OpenAI AI模型获取答案

        Args:
            question: 问题内容
            options: 选项内容
            question_type: 问题类型

        Returns:
            str: AI返回的答案
        """
        try:
            # 构建提示词
            prompt = self._build_prompt(question, options, question_type)

            # 准备请求数据
            request_data = self._prepare_request_data(prompt)

            # 准备请求头
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            # 发送请求
            response_text = self._make_request(self.base_url + "/chat/completions", headers, request_data)

            # 解析响应
            answer = self._parse_response(response_text)

            # 提取JSON格式的答案
            return self._extract_answer_from_json(answer)

        except Exception as e:
            print(f"[OpenAI] 查询失败: {str(e)}")
            return f"OpenAI API调用失败: {str(e)}"

    def _build_prompt(self, question: str, options: str, question_type: str) -> str:
        """
        构建OpenAI提示词

        Args:
            question: 问题内容
            options: 选项内容
            question_type: 问题类型

        Returns:
            str: 构建的提示词
        """
        content = '''You are a professional question answering assistant. Please provide accurate answers based on the given questions and options.

Answering Rules:
1. Multiple choice: Return the option content directly, not the letter
2. Multiple select: Connect multiple answers with "###"
3. True/False: Return "对" or "错" directly
4. Fill in the blank: Fill in the content directly, use "###" to connect multiple blanks

Response format must be strict JSON: {"answer":"your_answer"}

Please answer the following question in Chinese:'''

        return f"{content}\n\nQuestion: {question}\nOptions: {options}\nType: {question_type}"

    def _prepare_request_data(self, prompt: str) -> Dict[str, Any]:
        """
        准备OpenAI请求数据

        Args:
            prompt: 提示词

        Returns:
            Dict: 请求数据
        """
        return {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的题库回答助手，总是以JSON格式{'answer': '答案'}返回答案。请用中文回答。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "stream": False,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "frequency_penalty": 0.1,
            "presence_penalty": 0.1,
            "stop": None
        }

    def _parse_response(self, response_text: str) -> str:
        """
        解析OpenAI响应内容

        Args:
            response_text: 原始响应文本

        Returns:
            str: 解析后的答案
        """
        try:
            # 解析JSON响应
            result = json.loads(response_text)

            if "choices" in result and len(result["choices"]) > 0:
                answer = result["choices"][0]["message"]["content"]
                print(f"[OpenAI] AI返回答案: {answer[:100]}...")
                return answer
            else:
                print(f"[OpenAI] API响应格式异常: {response_text}")
                return "无法从API获取答案"

        except json.JSONDecodeError as e:
            print(f"[OpenAI] JSON解析错误: {str(e)}")
            print(f"[OpenAI] 响应内容: {response_text}")
            return f"API响应解析失败: {str(e)}"

    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息

        Returns:
            Dict: 模型信息
        """
        return {
            "provider": "OpenAI",
            "model": self.model,
            "base_url": self.base_url,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "supported_features": [
                "chat_completion",
                "json_response",
                "temperature_control",
                "token_limit",
                "system_prompt",
                "function_calling"
            ]
        }