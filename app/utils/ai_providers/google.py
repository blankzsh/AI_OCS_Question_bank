"""
Google Studio AI服务适配器
支持Google Gemini平台的AI模型调用
"""

import json
from typing import Dict, Any
from .base import AIProviderBase


class GoogleProvider(AIProviderBase):
    """Google Studio AI服务提供商"""

    def query(self, question: str, options: str = "", question_type: str = "") -> str:
        """
        查询Google Gemini AI模型获取答案

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
                "Content-Type": "application/json"
            }

            # Google API使用API Key作为查询参数
            url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"

            # 发送请求
            response_text = self._make_request(url, headers, request_data)

            # 解析响应
            answer = self._parse_response(response_text)

            # 提取JSON格式的答案
            return self._extract_answer_from_json(answer)

        except Exception as e:
            print(f"[Google] 查询失败: {str(e)}")
            return f"Google Studio API调用失败: {str(e)}"

    def _build_prompt(self, question: str, options: str, question_type: str) -> str:
        """
        构建Google Gemini提示词

        Args:
            question: 问题内容
            options: 选项内容
            question_type: 问题类型

        Returns:
            str: 构建的提示词
        """
        content = '''你是一个专业的题库回答助手。请根据提供的问题和选项给出准确答案。

答题规则：
1. 选择题：直接返回选项内容，不是字母
2. 多选题：多个答案用"###"连接
3. 判断题：直接返回"对"或"错"
4. 填空题：直接填写内容，多个空用"###"连接

回答格式必须是严格的JSON格式：{"answer":"你的答案"}

请回答以下问题：'''

        return f"{content}\n\n问题：{question}\n选项：{options}\n类型：{question_type}"

    def _prepare_request_data(self, prompt: str) -> Dict[str, Any]:
        """
        准备Google Gemini请求数据

        Args:
            prompt: 提示词

        Returns:
            Dict: 请求数据
        """
        return {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": self.temperature,
                "topP": self.top_p,
                "maxOutputTokens": self.max_tokens,
                "stopSequences": []
            },
            "safetySettings": [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE"
                }
            ]
        }

    def _parse_response(self, response_text: str) -> str:
        """
        解析Google Gemini响应内容

        Args:
            response_text: 原始响应文本

        Returns:
            str: 解析后的答案
        """
        try:
            # 解析JSON响应
            result = json.loads(response_text)

            if "candidates" in result and len(result["candidates"]) > 0:
                candidate = result["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    answer = candidate["content"]["parts"][0]["text"]
                    print(f"[Google] AI返回答案: {answer[:100]}...")
                    return answer

            print(f"[Google] API响应格式异常: {response_text}")
            return "无法从API获取答案"

        except json.JSONDecodeError as e:
            print(f"[Google] JSON解析错误: {str(e)}")
            print(f"[Google] 响应内容: {response_text}")
            return f"API响应解析失败: {str(e)}"

    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息

        Returns:
            Dict: 模型信息
        """
        return {
            "provider": "Google Studio",
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
                "safety_filters",
                "multimodal"
            ]
        }