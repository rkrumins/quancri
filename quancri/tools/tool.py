import inspect
from abc import abstractmethod, ABC
from typing import Union, Any

from quancri.models.tool_model import ToolMetadata, ToolParameter, ToolCategory


class Tool(ABC):
    def __init__(self):
        self._metadata = None

    def _get_type_str(self, annotation) -> str:
        """Helper method to convert type annotations to string representation"""
        if annotation == inspect._empty:
            return 'Any'

        # Handle Optional types
        if hasattr(annotation, '__origin__') and annotation.__origin__ is Union:
            args = annotation.__args__
            if type(None) in args:
                non_none_args = [arg for arg in args if arg is not type(None)]
                if len(non_none_args) == 1:
                    return f'Optional[{self._get_type_str(non_none_args[0])}]'

        # Handle special form types (Any, NoReturn, etc.)
        if hasattr(annotation, '_name'):
            return annotation._name

        # Handle List, Dict, etc.
        if hasattr(annotation, '__origin__'):
            args = ', '.join(self._get_type_str(arg) for arg in annotation.__args__)
            origin_name = annotation.__origin__.__name__ if hasattr(annotation.__origin__, '__name__') else str(annotation.__origin__)
            return f'{origin_name}[{args}]'

        # Handle basic types
        if hasattr(annotation, '__name__'):
            return annotation.__name__

        return str(annotation)

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Execute the tool with given parameters"""
        pass

    def _extract_param_description(self, docstring: str, param_name: str) -> str:
        """Extract parameter description from docstring"""
        if not docstring:
            return f"Parameter {param_name}"
        
        lines = docstring.split('\n')
        in_args = False
        param_desc = ""
        
        for line in lines:
            line = line.strip()
            if line.startswith('Args:'):
                in_args = True
                continue
            if in_args:
                if line.startswith(f'{param_name}:') or line.startswith(f'{param_name} :'):
                    param_desc = line.split(':', 1)[1].strip()
                    break
                elif not line or line.startswith('Returns:'):
                    break
        
        return param_desc or f"Parameter {param_name}"

    def _get_function_metadata(self, func) -> dict:
        """Extract metadata for a given function"""
        sig = inspect.signature(func)
        doc = inspect.getdoc(func)
        
        # Extract parameters
        parameters = []
        for name, param in sig.parameters.items():
            if name != 'self':
                param_type = self._get_type_str(param.annotation)
                description = self._extract_param_description(doc, name)
                parameters.append(ToolParameter(
                    name=name,
                    type=param_type,
                    description=description,
                    required=param.default == inspect.Parameter.empty
                ))
        
        # Get function description from docstring
        description = doc.split('\n')[0].strip() if doc else f"Function {func.__name__}"
        
        return {
            "name": func.__name__,
            "description": description,
            "parameters": parameters,
            "return_type": self._get_type_str(sig.return_annotation)
        }

    @property
    def metadata(self) -> ToolMetadata:
        """Extract metadata from all documented functions in the tool"""
        if not hasattr(self, '_metadata') or self._metadata is None:
            # Get all public methods (don't start with underscore)
            functions = []
            for name, func in inspect.getmembers(self.__class__, predicate=inspect.isfunction):
                if not name.startswith('_'):
                    func_metadata = self._get_function_metadata(func)
                    if func_metadata:
                        functions.append(func_metadata)

            if not functions:
                raise ValueError(f"Tool {self.__class__.__name__} has no documented functions")

            # Use the class docstring for the overall description
            class_doc = inspect.getdoc(self.__class__)
            description = class_doc.split("\n")[0].strip() if class_doc else f"Tool {self.__class__.__name__}"

            self._metadata = ToolMetadata(
                name=self.__class__.__name__,
                description=description,
                category=getattr(self, 'category', ToolCategory.GENERAL),
                functions=functions  # Add the functions list to the metadata
            )

        return self._metadata


