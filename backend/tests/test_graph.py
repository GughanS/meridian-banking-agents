import os
from uuid import uuid4

import pytest

from app.graph.workflow import get_compiled_graph


@pytest.mark.asyncio
async def test_graph_routing_and_execution(monkeypatch):
    os.environ["LLM_PROVIDER"] = "mock"
    
    from app.llm.client import MockLLMClient
    
    class RoutingMock(MockLLMClient):
        async def generate_content(self, system_prompt, messages, tools):
            class MockResponse:
                text = "RiskAgent" if "Supervisor" in system_prompt else "Mock Risk Response"
                candidates = []
            return MockResponse()
            
    monkeypatch.setattr("app.graph.nodes.supervisor.get_llm_client", lambda: RoutingMock("mock"))
    monkeypatch.setattr("app.graph.nodes.specialists.get_llm_client", lambda: RoutingMock("mock"))
    
    graph = await get_compiled_graph()
    
    config = {"configurable": {"thread_id": "test_thread"}}
    state = {
        "messages": [{"role": "user", "content": "I see a fraudulent charge, please help"}],
        "customer_id": uuid4(),
        "session_id": uuid4()
    }
    
    result = await graph.ainvoke(state, config=config)
    
    assert result["next_agent"] == "RiskAgent"
    assert len(result["messages"]) > 1
    assert result["messages"][-1]["content"] == "Mock Risk Response"
