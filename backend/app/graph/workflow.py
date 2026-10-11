import os

import aiosqlite
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, StateGraph

from app.graph.nodes.specialists import (
    credit_agent_node,
    customer_agent_node,
    risk_agent_node,
)
from app.graph.nodes.supervisor import supervisor_node
from app.graph.state import AgentState


def route_from_supervisor(state: AgentState):
    next_agent = state.get("next_agent")
    if next_agent == "FINISH" or not next_agent:
        return END
    return next_agent

def build_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("Supervisor", supervisor_node)
    workflow.add_node("CustomerAgent", customer_agent_node)
    workflow.add_node("RiskAgent", risk_agent_node)
    workflow.add_node("CreditAgent", credit_agent_node)
    
    workflow.add_conditional_edges(
        "Supervisor",
        route_from_supervisor,
        {
            "CustomerAgent": "CustomerAgent",
            "RiskAgent": "RiskAgent",
            "CreditAgent": "CreditAgent",
            END: END
        }
    )
    
    workflow.add_edge("CustomerAgent", END)
    workflow.add_edge("RiskAgent", END)
    workflow.add_edge("CreditAgent", END)
    
    workflow.set_entry_point("Supervisor")
    return workflow

async def get_compiled_graph():
    # Use memory for tests or file for production
    db_path = os.getenv("CHECKPOINT_DB_URL", ":memory:")
    conn = await aiosqlite.connect(db_path)
    checkpointer = AsyncSqliteSaver(conn)
    await checkpointer.setup()
    
    graph = build_graph()
    return graph.compile(checkpointer=checkpointer)
