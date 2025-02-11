from dataclasses import dataclass
from typing import Dict, Optional, Any


@dataclass
class LLMConfig:
    """Configuration for LLM providers"""
    api_key: str
    model: str
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 8192
    extra_params: Optional[Dict[str, Any]] = None

