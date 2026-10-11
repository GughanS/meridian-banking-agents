from app.graph.state import AgentState
from app.llm.client import get_llm_client

SUPERVISOR_PROMPT = """You are the Supervisor Agent for Meridian Bank. 
Your job is to route the user's request to the correct specialist agent or finish the conversation.
You have access to the following agents:
- CustomerAgent: Handles account balances, transactions, and card management (blocking/unblocking).
- RiskAgent: Handles fraud alerts, transaction disputes, and escalating fraud.
- CreditAgent: Handles credit profile, loan eligibility, EMI calculations, and loan applications.

If the user's request requires one of these domains, output EXACTLY ONE word corresponding to the agent name (e.g. "CustomerAgent").
If the request is fully handled or requires no further action, output EXACTLY the word "FINISH".
Do not output anything else.
"""

async def supervisor_node(state: AgentState) -> dict:
    client = get_llm_client()
    messages = list(state.get("messages", []))
    
    route_messages = messages + [{"role": "user", "content": "Based on the conversation above, which agent should handle the latest request? Output only the agent name or FINISH."}]
    
    try:
        response = await client.generate_content(SUPERVISOR_PROMPT, route_messages, tools=[])
        text = response.text.strip().strip('"').strip("'") if hasattr(response, 'text') and response.text else "FINISH"
        
        valid_routes = ["CustomerAgent", "RiskAgent", "CreditAgent", "FINISH"]
        found_route = "FINISH"
        for route in valid_routes:
            if route.lower() in text.lower():
                found_route = route
                break
                
        return {"next_agent": found_route}
    except Exception:
        return {"next_agent": "FINISH"}
