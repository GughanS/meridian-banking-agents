
from app.db.session import SessionLocal
from app.graph.state import AgentState
from app.llm.client import get_llm_client
from app.llm.registry import ToolContext, registry

AGENT_CONFIGS = {
    "CustomerAgent": {
        "prompt": "You are the Customer Agent. You handle accounts, transactions, and cards. You MUST use tools to answer questions.",
        "tools": ["get_customer_profile", "get_accounts", "get_transactions", "get_cards", "propose_card_block"]
    },
    "RiskAgent": {
        "prompt": "You are the Risk Agent. You handle fraud alerts, disputes, card security, and fraud escalation. You MUST use tools to answer questions.",
        "tools": ["get_fraud_alerts", "get_disputes", "propose_dispute", "escalate_fraud", "get_cards", "propose_card_block"]
    },
    "CreditAgent": {
        "prompt": "You are the Credit Agent. You handle credit scores, loan options, EMI calculators, and applications. You MUST use tools to answer questions.",
        "tools": ["get_credit_profile", "get_loan_products", "calculate_loan_options", "propose_loan_application"]
    }
}

async def execute_agent(agent_name: str, state: AgentState) -> dict:
    config = AGENT_CONFIGS.get(agent_name)
    if not config:
        return {"messages": [{"role": "model", "content": f"Error: Agent {agent_name} not configured."}]}
        
    client = get_llm_client()
    system_prompt = config["prompt"]
    tool_names = config["tools"]
    genai_tools = registry.get_genai_tools_by_names(tool_names)
    
    messages = list(state.get("messages", []))
    new_messages = []
    
    async with SessionLocal() as db:
        ctx = ToolContext(db=db, customer_id=state["customer_id"], session_id=state["session_id"])
        
        for _ in range(5):
            try:
                response = await client.generate_content(system_prompt, messages, tools=genai_tools)
                
                if hasattr(response, 'candidates') and response.candidates and response.candidates[0].content.parts:
                    has_tool_call = False
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'function_call') and part.function_call:
                            has_tool_call = True
                            call = part.function_call
                            call_msg = {
                                "role": "model",
                                "function_call": {
                                    "name": call.name,
                                    "args": dict(call.args) if call.args else {}
                                }
                            }
                            messages.append(call_msg)
                            new_messages.append(call_msg)
                            
                            args = dict(call.args) if call.args else {}
                            result = await registry.execute(call.name, args, ctx)
                            
                            resp_msg = {
                                "role": "tool",
                                "tool_name": call.name,
                                "content": result
                            }
                            messages.append(resp_msg)
                            new_messages.append(resp_msg)
                        
                        elif hasattr(part, 'text') and part.text:
                            text_msg = {"role": "model", "content": part.text}
                            messages.append(text_msg)
                            new_messages.append(text_msg)
                            
                    if not has_tool_call:
                        break
                else:
                    text = response.text if hasattr(response, 'text') and response.text else "I couldn't process that."
                    text_msg = {"role": "model", "content": text}
                    messages.append(text_msg)
                    new_messages.append(text_msg)
                    break
                    
            except Exception as e:
                err_msg = {"role": "model", "content": f"An error occurred: {e!s}"}
                messages.append(err_msg)
                new_messages.append(err_msg)
                break
                
    return {"messages": new_messages}

async def customer_agent_node(state: AgentState) -> dict:
    return await execute_agent("CustomerAgent", state)

async def risk_agent_node(state: AgentState) -> dict:
    return await execute_agent("RiskAgent", state)

async def credit_agent_node(state: AgentState) -> dict:
    return await execute_agent("CreditAgent", state)
