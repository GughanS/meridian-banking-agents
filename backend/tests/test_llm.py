import pytest

from app.llm.client import MockLLMClient, get_llm_client


@pytest.mark.asyncio
async def test_llm_client_mock():
    # Smoke test for mock LLM client
    client = get_llm_client(model_id="mock")
    assert isinstance(client, MockLLMClient)
    assert await client.validate_model() is True
    
    res = await client.generate_content("Sys prompt", [{"role": "user", "content": "Hello"}], [])
    assert res.text == "Mock response"
