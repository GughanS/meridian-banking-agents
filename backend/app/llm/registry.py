import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from google.genai import types
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class ToolContext:
    db: AsyncSession
    customer_id: UUID
    session_id: UUID

class ToolDef:
    def __init__(
        self,
        name: str,
        description: str,
        schema: type[BaseModel],
        handler: Callable[..., Awaitable[Any]]
    ):
        self.name = name
        self.description = description
        self.schema = schema
        self.handler = handler
        
    def to_genai_tool(self) -> types.Tool:
        schema_dict = self.schema.model_json_schema()
        
        # Pydantic json schema wraps properties.
        # google-genai accepts OpenAPI compatible schemas in a dict
        properties = schema_dict.get("properties", {})
        required = schema_dict.get("required", [])
        
        genai_schema = {
            "type": "OBJECT",
            "properties": properties,
            "required": required
        }
        
        func_decl = types.FunctionDeclaration(
            name=self.name,
            description=self.description,
            parameters=genai_schema if properties else None
        )
        return types.Tool(function_declarations=[func_decl])

class ToolRegistry:
    def __init__(self):
        self.tools: dict[str, ToolDef] = {}
        
    def register(self, name: str, description: str, schema: type[BaseModel]):
        def decorator(func: Callable[..., Awaitable[Any]]):
            self.tools[name] = ToolDef(name, description, schema, func)
            return func
        return decorator
        
    def get_genai_tools(self) -> list[types.Tool]:
        if not self.tools:
            return []
        decls = []
        for t in self.tools.values():
            decls.extend(t.to_genai_tool().function_declarations)
        return [types.Tool(function_declarations=decls)]
        
    def get_genai_tools_by_names(self, names: list[str]) -> list[types.Tool]:
        decls = []
        for name in names:
            if name in self.tools:
                decls.extend(self.tools[name].to_genai_tool().function_declarations)
        if not decls:
            return []
        return [types.Tool(function_declarations=decls)]
        
    async def execute(self, name: str, kwargs: dict, context: ToolContext) -> str:
        if name not in self.tools:
            return json.dumps({"status": "error", "message": f"Tool {name} not found."})
            
        tool = self.tools[name]
        try:
            validated_args = tool.schema(**kwargs)
            result = await tool.handler(context, **validated_args.model_dump())
            return json.dumps({"status": "success", "data": result}, default=str)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

registry = ToolRegistry()
