import importlib
import inspect
import json
import os
from typing import Dict, Any, List

from quancri.tools.tool import Tool


class Agent:
    def __init__(self, llm_provider):
        self.tools: Dict[str, Tool] = {}
        self.llm_provider = llm_provider

    def register_tool(self, tool: Tool):
        """Register a new tool with the agent"""
        metadata = tool.metadata
        self.tools[metadata.name] = tool

    def register_tools_from_directory(self, directory: str):
        """Auto-register all tools from a directory"""
        for file in os.listdir(directory):
            if file.endswith('.py'):
                module_name = file[:-3]
                module = importlib.import_module(f"tools.{module_name}")
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and issubclass(obj, Tool) and obj != Tool:
                        self.register_tool(obj())

    async def execute_step(self, step: dict, previous_results: List[dict]) -> Any:
        """Execute a single step of the analysis"""
        if not step['requires_tool']:
            return None

        tool_name = step.get('tool_name')
        if not tool_name:
            return None

        tool = self.tools.get(tool_name)
        if not tool:
            step['step'] = f"[Tool not available] {step['step']}"
            return None

        try:
            # Inject previous results into tool parameters if needed
            tool_params = step['tool_params'].copy() if step.get('tool_params') else {}
            
            # If use_previous_results is specified, add the result to tool_params
            if 'use_previous_results' in tool_params:
                step_index = tool_params.pop('use_previous_results')
                if isinstance(step_index, int) and 0 <= step_index < len(previous_results):
                    tool_params['previous_result'] = previous_results[step_index]['result']

            # Get the function name to call (default to execute if not specified)
            function_name = tool_params.pop('function_name', 'execute')
            # Get the function from the tool
            tool_function = getattr(tool, function_name, None)
            if not tool_function:
                print(f"Function {function_name} not found in {tool_name}")
                step['step'] = f"[Function not available] {function_name} in {step['step']}"
                return None

            # Only pass previous_result if the function explicitly accepts it
            sig = inspect.signature(tool_function)
            if 'previous_result' not in sig.parameters:
                tool_params.pop('previous_result', None)

            # Debug print to see what's being called
            print(f"Calling {tool_name}.{function_name} with params: {tool_params}")
            
            # Handle both async and non-async function calls
            if inspect.iscoroutinefunction(tool_function):
                result = await tool_function(**tool_params)
            else:
                result = tool_function(**tool_params)

            # Debug print for result
            print(f"Result from {function_name}: {result is not None}")

            return result
        except Exception as e:
            print(f"Error executing {tool_name}.{function_name}: {str(e)}")
            step['step'] = f"[Error] {step['step']}: {str(e)}"
            return None

    async def process_question(self, question: str) -> str:
        """
        Main method to process a question:
        1. Analyze question and break into steps
        2. Execute each step (using tools if needed)
        3. Generate final response
        """

        # Analyze question
        steps = await self.analyze_question(question, self.tools)

        # Execute steps
        context = []
        for step in steps:
            result = await self.execute_step(step, context)
            # Get tool metadata if available
            tool_metadata = None
            if step.get("tool_name"):
                tool = self.tools.get(step["tool_name"])
                if tool:
                    tool_metadata = {
                        "name": tool.metadata.name,
                        "description": tool.metadata.description,
                        "category": tool.metadata.category.value,
                        "function_called": step.get("tool_params", {}).get("function_name", "execute"),
                        "function_parameters": step.get("tool_params", {})
                    }

            context.append({
                "step": step["step"],
                "requires_tool": step["requires_tool"],
                "tool_name": step.get("tool_name"),
                "tool_metadata": tool_metadata,
                "result": result
            })

        print("Steps taken: \n {}".format(json.dumps(context, indent=2)))
        # Generate response
        return await self.generate_response(question, context)

    def _update_tools_description(self, tools: Dict[str, Tool]):
        """Update the tools description for prompt context"""
        self.tools_description = {
            name: {
                "description": tool.metadata.description,
                "category": tool.metadata.category.value,
                "functions": [{
                    "name": func["name"],
                    "description": func["description"],
                    "parameters": [{
                        "name": param.name,
                        "type": param.type,
                        "description": param.description,
                        "required": param.required
                    } for param in func["parameters"]],
                    "return_type": func["return_type"]
                } for func in tool.metadata.functions]
            } for name, tool in tools.items()
        }

    async def analyze_question(self, question: str, tools: Dict[str, Tool]) -> List[dict]:
        """Break down question into steps and identify required tools"""
        self._update_tools_description(self.tools)  # Use self.tools instead of tools parameter

        prompt = f"""You are an AI assistant that analyzes questions and breaks them down into steps. Your output must be valid JSON.

Available tools:
{json.dumps(self.tools_description, indent=2)}

Question: {question}

Pre-Analysis (Do NOT include these as steps in your output):
- Does this question need real-time data?
- Does this question need external information?
- Could this be answered with simple reasoning alone?
- Is historical data required?

Based on the above analysis:
1. First, determine if this question actually requires any tools to answer:
   - Does it need real-time data (like current stock prices)?
   - Does it need external information (like news articles)?
   - Could it be answered with simple reasoning alone?
   - Is historical or archived data required?
2. If NO tools are needed, return a single step with requires_tool: false
3. If tools ARE needed:
   - Break down into minimal necessary steps
   - Only use tools for steps that absolutely require external data
   - Combine steps where possible to minimize tool usage
   - Don't use tools for simple calculations or logic
4. For each step that might need a tool, ask:
   - Is real-time or external data REQUIRED for this step?
   - Does any available tool EXACTLY match what's needed?
   - Could this step be completed with simple reasoning instead?
   - Would the tool provide valuable data we can't get otherwise?
5. Return a JSON array where each object has this structure:
{{
    "step": "description of the step",
    "requires_tool": boolean,
    "tool_name": "name of the tool if requires_tool is true, otherwise null",
    "tool_params": {{ }} // parameters for the tool if requires_tool is true, otherwise null
}}

Rules:
- Default to NOT using a tool unless absolutely necessary
- Don't force tool usage just because a tool is available
- Keep steps simple and focused
- Use null for tool_name and tool_params when no tool is needed
- Ensure tool parameters exactly match the tool's requirements
- Your entire response must be a valid JSON array

Example of a question that doesn't need tools:
Question: "What is 2 + 2?"
[
    {{
        "step": "Calculate basic arithmetic",
        "requires_tool": false,
        "tool_name": null,
        "tool_params": null
    }}
]

Example of selective tool usage:
Question: "What's Tesla's stock price and what does this mean?"
[
    {{
        "step": "Fetch current Tesla stock price",
        "requires_tool": true,
        "tool_name": "StockPriceTool",
        "tool_params": {{"symbol": "TSLA"}}
    }},
    {{
        "step": "Analyze price implications",
        "requires_tool": false,
        "tool_name": null,
        "tool_params": null
    }}
]

Example valid response format that can be returned from tools:
[
    {{
        "step": "Fetch current price for AAPL stock",
        "requires_tool": true,
        "tool_name": "StockPriceTool",
        "tool_params": {{"symbol": "AAPL"}}
    }},
    
    {{
        "step": "Format the price for display",
        "requires_tool": false,
        "tool_name": null,
        "tool_params": null
    }},
    {{
        "step": "What is the weather forecase for next 5 days",
        "requires_tool": true,
        "tool_name": "WeatherTool",
        "tool_params": {{"symbol": "AAPL"}}
    }},
    {{
        "step": "Fetch company-specific news about Tesla",
        "requires_tool": true,
        "tool_name": "NewsAPIClient",
        "tool_params": {{
            "function_name": "fetch_company_news",
            "company_name": "Tesla",
            "days": 7,
            "include_ticker": true
        }}
    }},
    {{
        "step": "Get technology sector news",
        "requires_tool": true,
        "tool_name": "NewsAPIClient",
        "tool_params": {{
            "function_name": "fetch_sector_news",
            "sector": "technology",
            "max_articles": 5
        }}
    }}
]

Return ONLY the JSON array for the given question, with no additional text:
"""

        # First attempt with strict JSON parsing
        response = await self.llm_provider.generate(
            messages=[{"role": "user", "content": prompt}]
        )

        try:
            # Try to parse the response directly
            return json.loads(response)
        except json.JSONDecodeError:
            print("Error")

    async def generate_response(self, question: str, context: List[dict]) -> str:
        """Generate natural language response using step results"""
        prompt = f"""You are an AI assistant tasked with generating a natural language response to a user's question based on the results of analysis steps.

Original question: {question}

Steps and results:
{json.dumps(context, indent=2)}

Analysis Instructions:
1. First analyze each step's results and their relationships:
   - Identify key data points and trends
   - Note any correlations between different steps
   - Consider how each step contributes to answering the question
   - Check for any data inconsistencies or gaps

2. Synthesize the information:
   - Connect related findings across different steps
   - Compare and contrast relevant data points
   - Identify patterns or trends in the data
   - Draw meaningful conclusions from the combined results

3. Generate a response that:
   - Directly answers the original question
   - Supports conclusions with specific data
   - Explains any important relationships or patterns found
   - Highlights significant insights
   - Acknowledges any limitations or uncertainties in the data

Format your response in a clear, professional, but conversational tone.
Include relevant numerical data and proper context for all findings.
If there are multiple aspects to the answer, organize them logically."""

        return await self.llm_provider.generate(
            messages=[{"role": "user", "content": prompt}]
        )

