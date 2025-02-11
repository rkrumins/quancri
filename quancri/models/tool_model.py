from dataclasses import dataclass
from enum import Enum
from typing import List


class ToolCategory(Enum):
    FINANCE = "finance"
    WEATHER = "weather"
    GENERAL = "general"
    NEWS    = "news"

@dataclass
class ToolParameter:
    name: str
    type: str
    description: str
    required: bool = True


@dataclass
class ToolFunction:
    name: str
    description: str
    parameters: List[ToolParameter]
    return_type: str


@dataclass
class ToolMetadata:
    name: str
    description: str
    category: ToolCategory
    functions: List[ToolFunction]
