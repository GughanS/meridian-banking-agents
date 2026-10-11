import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import aiosqlite
import structlog
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from app.graph.workflow import get_compiled_graph

logger = structlog.get_logger(__name__)

DATASET = [
    ("What is my balance?", "customer_agent"),
    ("I lost my card, please block it", "risk_agent"),
    ("Can I get a home loan?", "credit_agent"),
    ("What are my latest transactions?", "customer_agent"),
    ("I see a transaction I didn't make", "risk_agent"),
    ("Is my credit score good enough for a 50k loan?", "credit_agent"),
    ("Transfer 100 to Rahul", "customer_agent"),
    ("My account has been compromised", "risk_agent"),
    ("Calculate my EMI for a 200k loan over 5 years", "credit_agent"),
    ("Change my address to New York", "customer_agent")
]

async def evaluate():
    logger.info("Starting Routing Evaluation...")
    # Temporarily force gemini for evaluation if key is available
    if not os.getenv("GEMINI_API_KEY"):
        logger.warning("No GEMINI_API_KEY found. Evaluation requires a real LLM for meaningful results.")
        return

    os.environ["LLM_PROVIDER"] = "gemini"
    
    correct = 0
    total = len(DATASET)
    
    async with aiosqlite.connect(":memory:") as db:
        saver = AsyncSqliteSaver(db)
        app = await get_compiled_graph(saver)
        
        for idx, (query, expected_route) in enumerate(DATASET):
            config = {"configurable": {"thread_id": f"eval_{idx}"}}
            inputs = {"messages": [("user", query)], "customer_id": "eval_cust"}
            
            # The supervisor is the first node that runs. We can capture its output.
            # However, running the graph executes until completion. 
            # The active_node is updated in the state by the supervisor.
            
            try:
                # We'll just run step-by-step to see the route
                result_state = None
                async for event in app.astream(inputs, config, stream_mode="values"):
                    result_state = event
                    # Check if active_node was set by supervisor
                    if result_state.get("active_node"):
                        break
                
                route = result_state.get("active_node")
                if route == expected_route:
                    correct += 1
                else:
                    logger.warning("Routing mismatch", query=query, expected=expected_route, actual=route)
            except Exception as e:
                logger.error("Error evaluating query", query=query, error=str(e))
                
    accuracy = (correct / total) * 100
    logger.info("Evaluation Complete", total=total, correct=correct, accuracy=f"{accuracy:.2f}%")
    
    # Write report
    report = f"# Routing Evaluation Report\n\nTotal queries: {total}\nCorrect: {correct}\nAccuracy: {accuracy:.2f}%\n"
    os.makedirs("docs", exist_ok=True)
    with open("docs/EVAL_REPORT.md", "w") as f:
        f.write(report)
    
    logger.info("Report saved to docs/EVAL_REPORT.md")

if __name__ == "__main__":
    asyncio.run(evaluate())
