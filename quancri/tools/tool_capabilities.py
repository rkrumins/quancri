from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from quancri.tools.stock_tools import StockPriceTool
from quancri.tools.tool import Tool


@dataclass
class ToolCapability:
    """Defines a specific capability of a tool"""
    name: str
    description: str
    required_params: List[str]
    example_usage: str
    fallback_tools: List[str] = None
    fallback_strategy: str = None


class ToolRegistry:
    """Central registry for tools and their capabilities"""

    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self.capabilities: Dict[str, List[ToolCapability]] = {}

    def register_tool(self, tool: Tool):
        """Register a tool and discover its capabilities"""
        metadata = tool.metadata
        self.tools[metadata.name] = tool

        # Discover capabilities from tool metadata and docstring
        capabilities = self._discover_capabilities(tool)
        self.capabilities[metadata.name] = capabilities

    def _discover_capabilities(self, tool: Tool) -> List[ToolCapability]:
        """Analyze tool metadata and docstring to discover capabilities"""
        metadata = tool.metadata
        capabilities = []

        if isinstance(tool, StockPriceTool):
            # Define specific capabilities for stock price tool
            capabilities.extend([
                ToolCapability(
                    name="get_current_price",
                    description="Get current stock price for a symbol",
                    required_params=["symbol"],
                    example_usage="Get current price for AAPL",
                    fallback_tools=["WebSearchTool", "CachedPriceTool"],
                    fallback_strategy="Try cached data or general market info"
                ),
                ToolCapability(
                    name="get_historical_prices",
                    description="Get historical stock prices for a date range",
                    required_params=["symbol", "start_date", "end_date"],
                    example_usage="Get AAPL prices from 2025-01-01 to 2025-01-07",
                    fallback_tools=["WebSearchTool", "CachedPriceTool"],
                    fallback_strategy="Use available data points and interpolate"
                )
            ])

        # Add generic capabilities based on method signature
        for param in metadata.parameters:
            if param.required:
                cap_name = f"get_by_{param.name}"
                capabilities.append(
                    ToolCapability(
                        name=cap_name,
                        description=f"Get data by {param.name}",
                        required_params=[param.name],
                        example_usage=f"Use {param.name} to fetch data",
                        fallback_strategy="Use general information"
                    )
                )

        return capabilities

    def find_tool_for_capability(self,
                                 capability_name: str,
                                 required_params: List[str] = None) -> Tuple[Optional[str], Optional[str]]:
        """Find the best tool and fallback for a given capability"""
        best_match = None
        fallback = None

        for tool_name, capabilities in self.capabilities.items():
            for cap in capabilities:
                if cap.name == capability_name:
                    if not required_params or all(param in cap.required_params for param in required_params):
                        if tool_name in self.tools:
                            best_match = tool_name
                            if cap.fallback_tools:
                                # Find first available fallback tool
                                fallback = next(
                                    (t for t in cap.fallback_tools if t in self.tools),
                                    None
                                )
                            break

        return best_match, fallback

    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """Get a tool by name"""
        return self.tools.get(tool_name)

    def get_capabilities(self) -> Dict[str, List[dict]]:
        """Get all capabilities in a format suitable for LLM context"""
        return {
            tool_name: [
                {
                    "name": cap.name,
                    "description": cap.description,
                    "required_params": cap.required_params,
                    "example": cap.example_usage
                }
                for cap in caps
            ]
            for tool_name, caps in self.capabilities.items()
        }
