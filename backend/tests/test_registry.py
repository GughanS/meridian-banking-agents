import json
from uuid import uuid4

import pytest

from app.llm.registry import ToolContext, registry


@pytest.mark.asyncio
async def test_registry_schema():
    # Check that tools are registered
    assert "get_customer_profile" in registry.tools
    assert "get_credit_profile" in registry.tools
    assert "calculate_loan_options" in registry.tools
    
    # Check that it produces genai Tool objects
    genai_tools = registry.get_genai_tools()
    assert len(genai_tools) > 0
    assert hasattr(genai_tools[0], 'function_declarations')

@pytest.mark.asyncio
async def test_tool_execute_invalid_name():
    ctx = ToolContext(db=None, customer_id=uuid4(), session_id=uuid4()) # type: ignore
    res = await registry.execute("invalid_tool", {}, ctx)
    parsed = json.loads(res)
    assert parsed["status"] == "error"
    assert "not found" in parsed["message"]
