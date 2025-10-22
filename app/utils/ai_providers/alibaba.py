"""
阿里百炼AI服务适配器
支持阿里云百炼平台的AI模型调用
"""

import json
from typing import Dict, Any
from .base import AIProviderBase


class AlibabaProvider(AIProviderBase):
    """阿里百炼AI服务提供商"""

    def query(self, question: str, options: str = "", question_type: str = "") -> str:
        """
        查询阿里百炼AI模型获取答案

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
            print(f"[阿里百炼] 查询失败: {str(e)}")
            return f"阿里百炼API调用失败: {str(e)}"

    def _build_prompt(self, question: str, options: str, question_type: str) -> str:
        """
        构建阿里百炼提示词

        Args:
            question: 问题内容
            options: 选项内容
            question_type: 问题类型

        Returns:
            str: 构建的提示词
        """
        content = '''你是一个题库接口函数，请根据问题和选项提供答案。如果是选择题，直接返回对应选项的内容，注意是内容，不是对应字母；如果题目是多选题，将内容用"###"连接；如果选项内容是"对","错"，且只有两项，或者question_type是judgement，你直接返回"对"或"错"的文字，不要返回字母；如果是填空题，直接返回填空内容，多个空使用###连接。回答格式为：{"anwser":"your_anwser_str"}，严格使用此格式回答。比如我问你一个问题，你回答的是"是"，你回答的格式为：{"anwser":"是"}。不要回答嗯，好的，我知道了之类的话，你的回答只能是json。下面是一个问题，请你用json格式回答我，绝对不要使用自然语言'''

        content += f'''{{
            "问题": "{question}",
            "选项": "{options}",
            "类型": "{question_type}"
        }}'''

        return content

    def _prepare_request_data(self, prompt: str) -> Dict[str, Any]:
        """
        准备阿里百炼请求数据

        Args:
            prompt: 提示词

        Returns:
            Dict: 请求数据
        """
        return {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "stream": False,
            "max_tokens": self.max_tokens,
            "stop": None,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "frequency_penalty": 0.5,
            "n": 1,
            "response_format": {"type": "text"}
        }

    def _parse_response(self, response_text: str) -> str:
        """
        解析阿里百炼响应内容

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
                print(f"[阿里百炼] AI返回答案: {answer[:100]}...")
                return answer
            else:
                print(f"[阿里百炼] API响应格式异常: {response_text}")
                return "无法从API获取答案"

        except json.JSONDecodeError as e:
            print(f"[阿里百炼] JSON解析错误: {str(e)}")
            print(f"[阿里百炼] 响应内容: {response_text}")
            return f"API响应解析失败: {str(e)}"

    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息

        Returns:
            Dict: 模型信息
        """
        return {
            "provider": "阿里百炼",
            "model": self.model,
            "base_url": self.base_url,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "supported_features": [
                "chat_completion",
                "json_response",
                "temperature_control",
                "token_limit"
            ]
        }