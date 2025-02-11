import os
from abc import ABC, abstractmethod
from getpass import getpass
from typing import List, Optional, Dict

import aiohttp
from langchain_groq import ChatGroq
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

from quancri.models.llm_model import LLMConfig


class LLMProvider(ABC):
    """Base class for LLM providers"""

    def __init__(self, config: LLMConfig):
        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None

    async def ensure_session(self):
        """Ensure aiohttp session exists"""
        if self._session is None:
            self._session = aiohttp.ClientSession()

    async def close(self):
        """Close aiohttp session"""
        if self._session:
            await self._session.close()
            self._session = None

    @abstractmethod
    async def generate(self,
                       messages: List[Dict[str, str]],
                       temperature: Optional[float] = None,
                       max_tokens: Optional[int] = None) -> str:
        """Generate response from LLM"""
        pass

class AnthropicProvider(LLMProvider):
    """Claude-specific implementation"""

    async def generate(self,
                       messages: List[Dict[str, str]],
                       temperature: Optional[float] = None,
                       max_tokens: Optional[int] = None) -> str:
        client = AsyncAnthropic(api_key=self.config.api_key)

        response = await client.messages.create(
            model=self.config.model,
            max_tokens=max_tokens or self.config.max_tokens,
            temperature=temperature or self.config.temperature,
            messages=messages
        )
        return response.content


class OpenAIProvider(LLMProvider):
    """OpenAI-specific implementation"""

    async def generate(self,
                       messages: List[Dict[str, str]],
                       temperature: Optional[float] = None,
                       max_tokens: Optional[int] = None) -> str:
        client = AsyncOpenAI(api_key=self.config.api_key)

        response = await client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=temperature or self.config.temperature,
            max_tokens=max_tokens or self.config.max_tokens,
            **self.config.extra_params or {}
        )
        return response.choices[0].message.content

class LangChainProvider(LLMProvider):
    async def generate(self, messages: List[Dict[str, str]], temperature: Optional[float] = None,
                       max_tokens: Optional[int] = None) -> str:
        llm_model = "llama-3.1-8b-instant"

        if "GROQ_API_KEY" not in os.environ:
            os.environ["GROQ_API_KEY"] = getpass("Enter your Groq API key: ")

        llm = ChatGroq(
            model=llm_model,
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
            # other params...
        )
        answer = llm.invoke(messages[0]["content"])
        return answer.content


class GroqProvider(LLMProvider):
    """Groq-specific implementation"""

    async def generate(self,
                       messages: List[Dict[str, str]],
                       temperature: Optional[float] = None,
                       max_tokens: Optional[int] = None) -> str:
        await self.ensure_session()

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature or self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
            **(self.config.extra_params or {})
        }

        base_url = self.config.base_url or "https://api.groq.com/v1"
        async with self._session.post(f"{base_url}/chat/completions",
                                      json=data,
                                      headers=headers) as response:
            response_data = await response.json()
            return response_data["choices"][0]["message"]["content"]

