import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import structlog

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
    if os.getenv("GEMINI_API_KEY"):
        os.environ["LLM_PROVIDER"] = "gemini"
        provider_name = "Google GenAI (gemini-3.1-pro)"
    else:
        os.environ["LLM_PROVIDER"] = "mock"
        provider_name = "Deterministic Mock Engine (Offline Mode)"
        logger.info("Running evaluation with deterministic Mock LLM provider.")
    
    correct = 0
    total = len(DATASET)
    app = await get_compiled_graph()
        
    for idx, (query, expected_route) in enumerate(DATASET):
        config = {"configurable": {"thread_id": f"eval_{idx}"}}
        inputs = {"messages": [("user", query)], "customer_id": "eval_cust"}
        
        try:
            result_state = None
            async for event in app.astream(inputs, config, stream_mode="values"):
                result_state = event
                if result_state.get("next_agent") or result_state.get("active_node"):
                    break
            
            route = (result_state.get("next_agent") or result_state.get("active_node") or "") if result_state else ""
            norm_route = str(route).lower().replace("_", "")
            norm_expected = expected_route.lower().replace("_", "")
            
            if norm_route == norm_expected:
                correct += 1
            else:
                logger.warning("Routing mismatch", query=query, expected=expected_route, actual=route)
        except Exception as e:
            logger.error("Error evaluating query", query=query, error=str(e))
                
    accuracy = (correct / total) * 100
    logger.info("Evaluation Complete", total=total, correct=correct, accuracy=f"{accuracy:.2f}%")
    
    # Write report
    report = f"# Routing Evaluation Report\n\nTotal queries: {total}\nCorrect: {correct}\nAccuracy: {accuracy:.2f}%\n\n*Evaluated against {provider_name}.*\n"
    docs_dir = Path(__file__).resolve().parent.parent.parent / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    report_file = docs_dir / "EVAL_REPORT.md"
    report_file.write_text(report, encoding="utf-8")
    
    logger.info("Report saved to docs/EVAL_REPORT.md")

if __name__ == "__main__":
    asyncio.run(evaluate())
