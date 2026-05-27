"""
LLM客户端封装
支持多Provider自动故障转移，统一使用OpenAI格式调用
"""

import json
import re
from typing import Optional, Dict, Any, List
from openai import OpenAI, RateLimitError, APIError, APIConnectionError

from ..config import Config
from .retry import retry_with_backoff
from ..utils.logger import get_logger

logger = get_logger('kinjeng.llm_client')


class LLMClient:
    """LLM客户端，支持多Provider自动故障转移"""

    RETRY_EXCEPTIONS = (RateLimitError, APIError, APIConnectionError)

    def __init__(
        self,
        providers: Optional[List[Dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        **kwargs
    ):
        self.providers = providers if providers is not None else list(Config.LLM_PROVIDERS)
        self.default_temperature = temperature
        self._active_provider: Optional[Dict[str, Any]] = None
        self._ensure_active_provider()

    def _ensure_active_provider(self):
        """依次尝试每个provider，直到找到一个可用的"""
        for provider in self._get_available_providers():
            try:
                OpenAI(
                    api_key=provider['api_key'],
                    base_url=provider['base_url']
                )
                self._active_provider = provider
                logger.info(
                    f"已激活LLM provider: {provider['name']} "
                    f"(model={provider['model']})"
                )
                return
            except Exception as e:
                logger.warning(
                    f"LLM provider {provider['name']} 初始化失败: {e}"
                )
        raise ValueError("所有LLM provider均不可用，请检查配置")

    def _get_available_providers(self):
        """过滤出有有效api_key的provider"""
        return [p for p in self.providers if p.get('api_key')]

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: int = 4096,
        response_format: Optional[Dict] = None
    ) -> str:
        last_error = None
        providers = self._get_available_providers()
        if not providers:
            raise ValueError("没有可用的LLM provider（所有api_key均为空）")

        for provider in providers:
            try:
                result = self._chat_with_provider(
                    provider, messages, temperature,
                    max_tokens, response_format
                )
                self._active_provider = provider
                return result
            except self.RETRY_EXCEPTIONS as e:
                last_error = e
                logger.warning(
                    f"Provider {provider['name']} 失败，切换到下一个: {e}"
                )

        raise last_error or RuntimeError("所有LLM provider均失败")

    @retry_with_backoff(
        max_retries=3,
        initial_delay=1.0,
        max_delay=10.0,
        exceptions=RETRY_EXCEPTIONS,
        on_retry=lambda e, n: logger.warning(f"LLM请求第{n}次重试: {str(e)}")
    )
    def _chat_with_provider(
        self,
        provider: Dict[str, Any],
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: int = 4096,
        response_format: Optional[Dict] = None
    ) -> str:
        client = OpenAI(
            api_key=provider['api_key'],
            base_url=provider['base_url']
        )
        kwargs = {
            "model": provider['model'],
            "messages": messages,
            "temperature": temperature if temperature is not None else (self.default_temperature or 0.7),
            "max_tokens": max_tokens,
        }
        if response_format:
            kwargs["response_format"] = response_format

        response = client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content
        # 部分模型（如MiniMax M2.5）会在content中包含<think>思考内容，需要移除
        content = re.sub(r'<think>[\s\S]*?</think>', '', content).strip()
        return content

    def chat_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        response = self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"}
        )
        cleaned_response = response.strip()
        cleaned_response = re.sub(r'^```(?:json)?\s*\n?', '', cleaned_response, flags=re.IGNORECASE)
        cleaned_response = re.sub(r'\n?```\s*$', '', cleaned_response)
        cleaned_response = cleaned_response.strip()

        try:
            return json.loads(cleaned_response)
        except json.JSONDecodeError:
            raise ValueError(f"LLM返回的JSON格式无效: {cleaned_response}")
