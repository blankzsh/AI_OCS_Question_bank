"""
AI服务提供商基础接口
定义所有AI提供商必须实现的标准接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import requests
import time
import traceback


class AIProviderBase(ABC):
    """AI服务提供商基础类"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化AI提供商

        Args:
            config: 提供商配置字典
        """
        self.config = config
        self.name = config.get('name', 'Unknown')
        self.api_key = config.get('api_key', '')
        self.base_url = config.get('base_url', '')
        self.model = config.get('model', '')
        self.max_tokens = config.get('max_tokens', 512)
        self.temperature = config.get('temperature', 0.1)
        self.top_p = config.get('top_p', 0.9)
        self.timeout = config.get('timeout', 30)
        self.max_retries = config.get('max_retries', 3)
        self.retry_delay = config.get('retry_delay', 2)

    @abstractmethod
    def query(self, question: str, options: str = "", question_type: str = "") -> str:
        """
        查询AI模型获取答案

        Args:
            question: 问题内容
            options: 选项内容
            question_type: 问题类型

        Returns:
            str: AI返回的答案
        """
        pass

    @abstractmethod
    def _build_prompt(self, question: str, options: str, question_type: str) -> str:
        """
        构建提示词

        Args:
            question: 问题内容
            options: 选项内容
            question_type: 问题类型

        Returns:
            str: 构建的提示词
        """
        pass

    @abstractmethod
    def _prepare_request_data(self, prompt: str) -> Dict[str, Any]:
        """
        准备请求数据

        Args:
            prompt: 提示词

        Returns:
            Dict: 请求数据
        """
        pass

    def _make_request(self, url: str, headers: Dict[str, str], data: Dict[str, Any]) -> str:
        """
        发送HTTP请求（带重试机制）

        Args:
            url: 请求URL
            headers: 请求头
            data: 请求数据

        Returns:
            str: 响应内容

        Raises:
            Exception: 请求失败时抛出异常
        """
        for attempt in range(self.max_retries):
            try:
                print(f"[{self.name}] 尝试 {attempt + 1}/{self.max_retries}")
                print(f"[{self.name}] 请求URL: {url}")

                response = requests.post(
                    url,
                    json=data,
                    headers=headers,
                    timeout=self.timeout,
                    verify=False
                )

                print(f"[{self.name}] 响应状态码: {response.status_code}")

                # 如果是服务器错误，尝试重试
                if response.status_code >= 500:
                    if attempt < self.max_retries - 1:
                        print(f"[{self.name}] 服务器错误，将在 {self.retry_delay} 秒后重试...")
                        time.sleep(self.retry_delay)
                        continue

                response.raise_for_status()
                return response.text

            except requests.exceptions.Timeout:
                print(f"[{self.name}] 请求超时")
                if attempt < self.max_retries - 1:
                    print(f"[{self.name}] 将在 {self.retry_delay} 秒后重试...")
                    time.sleep(self.retry_delay)
                else:
                    raise Exception("API调用超时，请稍后再试")

            except requests.exceptions.RequestException as e:
                print(f"[{self.name}] 请求异常: {str(e)}")
                if attempt < self.max_retries - 1:
                    print(f"[{self.name}] 将在 {self.retry_delay} 秒后重试...")
                    time.sleep(self.retry_delay)
                else:
                    raise Exception(f"API请求异常: {str(e)}")

            except Exception as e:
                error_trace = traceback.format_exc()
                print(f"[{self.name}] 调用失败: {str(e)}")
                print(f"[{self.name}] 详细错误信息: {error_trace}")
                raise Exception(f"API调用失败: {str(e)}")

        raise Exception("多次尝试后仍无法获取答案，请稍后再试")

    @abstractmethod
    def _parse_response(self, response_text: str) -> str:
        """
        解析响应内容

        Args:
            response_text: 原始响应文本

        Returns:
            str: 解析后的答案
        """
        pass

    def _extract_answer_from_json(self, ai_answer: str) -> str:
        """
        从AI返回的答案中提取JSON格式的答案

        Args:
            ai_answer: AI返回的原始答案

        Returns:
            str: 提取的答案内容
        """
        import json
        import re

        try:
            # 尝试解析JSON格式的答案
            if "{" in ai_answer and "}" in ai_answer:
                # 提取JSON部分 - 从第一个{到最后一个}
                start_idx = ai_answer.find("{")
                end_idx = ai_answer.rfind("}") + 1
                json_str = ai_answer[start_idx:end_idx]

                # 处理可能的格式问题
                # 1. 替换单引号为双引号
                json_str = json_str.replace("'", '"')

                # 2. 处理没有引号的键名 {answer: -> {"answer":
                json_str = re.sub(r'{(\s*)(\w+)(\s*):', r'{\1"\2"\3:', json_str)
                json_str = re.sub(r',(\s*)(\w+)(\s*):', r',\1"\2"\3:', json_str)

                # 3. 移除所有换行符和多余空格，使JSON更紧凑
                json_str = re.sub(r'\s+', ' ', json_str).strip()

                print(f"[{self.name}] 处理后的JSON字符串: {json_str}")

                # 尝试解析JSON
                answer_dict = json.loads(json_str)

                # 提取answer字段
                if "answer" in answer_dict:
                    return answer_dict["answer"]
                elif "anwser" in answer_dict:  # 处理可能的拼写错误
                    return answer_dict["anwser"]

        except json.JSONDecodeError as e:
            print(f"[{self.name}] 解析AI回答JSON失败: {str(e)}")

            # 尝试直接提取引号中的内容作为答案
            if '"answer"' in ai_answer or '"anwser"' in ai_answer:
                try:
                    # 使用正则表达式提取引号中的内容
                    answer_match = re.search(r'"answer"\s*:\s*"([^"]+)"', ai_answer)
                    if answer_match:
                        return answer_match.group(1)
                    else:
                        answer_match = re.search(r'"anwser"\s*:\s*"([^"]+)"', ai_answer)
                        if answer_match:
                            return answer_match.group(1)
                except Exception as regex_error:
                    print(f"[{self.name}] 正则提取答案失败: {str(regex_error)}")

        # 如果JSON解析失败，返回原始答案
        return ai_answer

    def is_enabled(self) -> bool:
        """检查提供商是否启用"""
        return (
            self.config.get('enabled', False) and
            bool(self.api_key)
        )

    def get_name(self) -> str:
        """获取提供商名称"""
        return self.name

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, enabled={self.is_enabled()})"