import json
import os
from typing import Any, Protocol

import structlog
from google import genai
from google.genai import types

logger = structlog.get_logger(__name__)

class LLMClient(Protocol):
    async def generate_content(self, system_prompt: str, messages: list[dict[str, Any]], tools: list[Any]) -> Any:
        ...
    async def validate_model(self) -> bool:
        ...

class GeminiClient:
    def __init__(self, model_id: str):
        self.model_id = model_id
        # Client automatically picks up GEMINI_API_KEY from environment
        self.client = genai.Client()
        
    async def validate_model(self) -> bool:
        try:
            # list models
            available_models = self.client.models.list()
            model_names = [m.name for m in available_models]
            # Names are usually 'models/gemini-2.5-flash'
            if not any(self.model_id in name for name in model_names):
                logger.warning(f"Model {self.model_id} not found in available models.")
                return False
            return True
        except Exception as e:
            logger.error(f"Failed to validate model: {e}")
            return False

    async def generate_content(self, system_prompt: str, messages: list[dict[str, Any]], tools: list[Any]) -> Any:
        contents = []
        import json
        for msg in messages:
            if msg["role"] == "user":
                contents.append(types.Content(role="user", parts=[types.Part.from_text(text=msg["content"])]))
            elif msg["role"] == "model":
                if "function_call" in msg:
                    fc = types.FunctionCall(name=msg["function_call"]["name"], args=msg["function_call"]["args"])
                    contents.append(types.Content(role="model", parts=[types.Part.from_function_call(function_call=fc)]))
                else:
                    contents.append(types.Content(role="model", parts=[types.Part.from_text(text=msg.get("content", ""))]))
            elif msg["role"] == "tool":
                try:
                    resp_dict = json.loads(msg["content"])
                except Exception:
                    resp_dict = {"response": msg["content"]}
                fr = types.FunctionResponse(name=msg["tool_name"], response=resp_dict)
                contents.append(types.Content(role="user", parts=[types.Part.from_function_response(function_response=fr)]))
            
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            tools=tools if tools else None,
            temperature=0.0,
        )
        
        response = await self.client.aio.models.generate_content(
            model=self.model_id,
            contents=contents,
            config=config
        )
        return response

class MockLLMClient:
    def __init__(self, model_id: str):
        self.model_id = model_id
        
    async def validate_model(self) -> bool:
        return True
        
    async def generate_content(self, system_prompt: str, messages: list[dict[str, Any]], tools: list[Any]) -> Any:
        user_text = ""
        for msg in messages:
            content = ""
            if isinstance(msg, dict):
                c = msg.get("content", "")
                if isinstance(c, str) and not c.startswith("Based on the conversation"):
                    content = c
            elif isinstance(msg, (list, tuple)) and len(msg) >= 2:
                content = str(msg[1])
            elif hasattr(msg, "content"):
                c = str(msg.content)
                if not c.startswith("Based on the conversation"):
                    content = c
            if content:
                user_text += " " + content.lower()

        resp_text = "Mock response"
        func_calls: list[Any] = []

        class MockFunctionCallWrapper:
            def __init__(self, name: str, args: dict[str, Any]):
                self.name = name
                self.args = args

        class MockPart:
            def __init__(self, text: str = "", fc: Any = None):
                self.text = text
                self.function_call = fc
        
        class MockCandidate:
            def __init__(self, parts: list[Any]):
                class MockContent:
                    def __init__(self, p: list[Any]):
                        self.parts = p
                self.content = MockContent(parts)
            
        class MockResponse:
            def __init__(self, text: str, fcs: list[Any]):
                parts = []
                for fc in fcs:
                    parts.append(MockPart(fc=fc))
                if text and not fcs:
                    parts.append(MockPart(text=text))
                elif not parts:
                    parts.append(MockPart(text=text))
                self.candidates = [MockCandidate(parts)]
                self.text = text
                self.function_calls = fcs

        tool_msgs = [m for m in messages if isinstance(m, dict) and m.get("role") == "tool"]
        tool_names_called = [m.get("tool_name") for m in tool_msgs]

        def _parse_content(content: Any) -> Any:
            if isinstance(content, str):
                try:
                    return json.loads(content)
                except Exception:
                    return content
            return content

        def _get_items(content: Any) -> list[Any]:
            parsed = _parse_content(content)
            if isinstance(parsed, list):
                return parsed
            if isinstance(parsed, dict):
                d = parsed.get("data", parsed)
                if isinstance(d, list):
                    return d
                if isinstance(d, dict):
                    if "data" in d and isinstance(d["data"], list):
                        return d["data"]
                    return [d]
                return [parsed]
            return []

        def _get_data_dict(content: Any) -> dict[str, Any]:
            parsed = _parse_content(content)
            if isinstance(parsed, dict):
                d = parsed.get("data", parsed)
                if isinstance(d, dict):
                    return d
                return parsed
            return {}

        def _get_field(item: Any, key: str, default: Any = None) -> Any:
            if isinstance(item, dict):
                return item.get(key, default)
            return getattr(item, key, default)

        if "Supervisor" in system_prompt:
            if any(k in user_text for k in ["loan", "emi", "credit", "borrow"]):
                resp_text = "CreditAgent"
            elif any(k in user_text for k in ["fraud", "block", "freeze", "dispute", "stolen", "lost", "compromised", "unauthorized", "didn't make"]):
                resp_text = "RiskAgent"
            elif any(k in user_text for k in ["balance", "transaction", "address", "account", "transfer", "bill", "utility", "pay"]):
                resp_text = "CustomerAgent"
            else:
                resp_text = "CustomerAgent"
        elif "Customer Agent" in system_prompt:
            if any(k in user_text for k in ["balance", "transaction", "last"]):
                if "get_accounts" not in tool_names_called:
                    func_calls = [MockFunctionCallWrapper("get_accounts", {})]
                elif any(k in user_text for k in ["transaction", "last"]) and "get_transactions" not in tool_names_called:
                    acc_id = None
                    for tm in tool_msgs:
                        if tm.get("tool_name") == "get_accounts":
                            items = _get_items(tm.get("content"))
                            if items:
                                acc_id = _get_field(items[0], "id")
                                break
                    if acc_id:
                        func_calls = [MockFunctionCallWrapper("get_transactions", {"account_id": str(acc_id), "limit": 3})]
                
                if not func_calls:
                    acc_info = ""
                    for tm in tool_msgs:
                        if tm.get("tool_name") == "get_accounts":
                            items = _get_items(tm.get("content"))
                            if items:
                                acc = items[0]
                                bal = float(_get_field(acc, "balance", 0))
                                num = str(_get_field(acc, "account_number", "4021"))
                                acc_info = f"Your current balance is **₹{bal:,.2f}** (Account ending in **{num[-4:]}**).\n\n"
                                break

                    tx_info = ""
                    for tm in tool_msgs:
                        if tm.get("tool_name") == "get_transactions":
                            items = _get_items(tm.get("content"))
                            if items:
                                txs = items[:3]
                                tx_info = "### Recent Transactions:\n" + "\n".join(
                                    f"- **{_get_field(t, 'merchant', 'Vendor')}**: ₹{abs(float(_get_field(t, 'amount', 0))):,.2f} ({str(_get_field(t, 'category', 'General')).title()})"
                                    for t in txs
                                )
                                break
                    
                    if acc_info or tx_info:
                        resp_text = (acc_info + tx_info).strip()
                    else:
                        resp_text = "Your current balance is **₹1,24,500.00**.\n\n### Recent Transactions:\n- **Fresh Supermarket**: ₹1,250.00 (Groceries)\n- **Cloud Services**: ₹8,400.00 (Business)\n- **Coffee Roast**: ₹350.00 (Dining)"
            elif any(k in user_text for k in ["transfer", "send", "wire", "remit"]):
                if "get_accounts" not in tool_names_called:
                    func_calls = [MockFunctionCallWrapper("get_accounts", {})]
                else:
                    bal_str = "₹12,95,000.00"
                    last4 = "4521"
                    for tm in tool_msgs:
                        if tm.get("tool_name") == "get_accounts":
                            items = _get_items(tm.get("content"))
                            if items:
                                acc = items[0]
                                bal = float(_get_field(acc, "balance", 0))
                                num = str(_get_field(acc, "account_number", "4521"))
                                bal_str = f"₹{bal:,.2f}"
                                last4 = str(num)[-4:]
                                break
                    resp_text = (
                        f"### Fund Transfer Service\n\n"
                        f"- **Source Account:** Checking ending in **{last4}**\n"
                        f"- **Available Balance:** **{bal_str}**\n\n"
                        f"Please provide the transfer details to proceed:\n"
                        f"1. **Recipient Name or UPI ID** (e.g. *Rohit Sharma* or *`rohit@meridian`*)\n"
                        f"2. **Transfer Amount** (up to available {bal_str})\n\n"
                        f"*Meridian enforces Human-in-the-Loop authorization. You will be prompted with a two-phase confirmation block prior to final settlement.*"
                    )
            elif any(k in user_text for k in ["bill", "utility", "pay"]):
                if "get_accounts" not in tool_names_called:
                    func_calls = [MockFunctionCallWrapper("get_accounts", {})]
                elif "get_transactions" not in tool_names_called:
                    acc_id = None
                    for tm in tool_msgs:
                        if tm.get("tool_name") == "get_accounts":
                            items = _get_items(tm.get("content"))
                            if items:
                                acc_id = _get_field(items[0], "id")
                                break
                    if acc_id:
                        func_calls = [MockFunctionCallWrapper("get_transactions", {"account_id": str(acc_id), "limit": 3})]
                else:
                    bal_str = "₹12,95,000.00"
                    last4 = "4521"
                    for tm in tool_msgs:
                        if tm.get("tool_name") == "get_accounts":
                            items = _get_items(tm.get("content"))
                            if items:
                                acc = items[0]
                                bal = float(_get_field(acc, "balance", 0))
                                num = str(_get_field(acc, "account_number", "4521"))
                                bal_str = f"₹{bal:,.2f}"
                                last4 = str(num)[-4:]
                                break
                    resp_text = (
                        f"### Upcoming & Recurring Utility Bills\n\n"
                        f"**Debit Account:** Account ending in **{last4}** (Available Balance: **{bal_str}**)\n\n"
                        f"| Biller / Service | Category | Amount Due | Due Date | Status |\n"
                        f"| :--- | :--- | :--- | :--- | :--- |\n"
                        f"| **Tata Power / Electricity** | Electricity | ₹2,450.00 | In 3 Days | Pending |\n"
                        f"| **Airtel Fiber Broadband** | Internet | ₹1,199.00 | In 5 Days | Auto-Debit |\n"
                        f"| **Municipal Water Board** | Water | ₹450.00 | In 7 Days | Pending |\n\n"
                        f"✅ Your balance of **{bal_str}** is sufficient to cover all scheduled utilities.\n\n"
                        f"Would you like to initiate payment for any of these bills?"
                    )
            elif any(k in user_text for k in ["block", "freeze", "lost", "stolen", "card"]):
                if "get_cards" not in tool_names_called:
                    func_calls = [MockFunctionCallWrapper("get_cards", {})]
                elif "propose_card_block" not in tool_names_called:
                    card_id = None
                    for tm in tool_msgs:
                        if tm.get("tool_name") == "get_cards":
                            items = _get_items(tm.get("content"))
                            if items:
                                card_id = _get_field(items[0], "id")
                                break
                    if card_id:
                        func_calls = [MockFunctionCallWrapper("propose_card_block", {"card_id": str(card_id), "reason": "Customer reported card lost/stolen"})]
                
                if not func_calls:
                    act_id = "pending"
                    card_desc = "debit card"
                    for tm in tool_msgs:
                        if tm.get("tool_name") == "get_cards":
                            items = _get_items(tm.get("content"))
                            if items:
                                last4 = _get_field(items[0], "last4")
                                if last4:
                                    card_desc = f"debit card ending in **{last4}**"
                        if tm.get("tool_name") == "propose_card_block":
                            c_dict = _get_data_dict(tm.get("content"))
                            act_id = str(c_dict.get("action_id", "pending"))
                    resp_text = f"⚠️ **Card Freeze Proposed**\n\nI have created a pending action to freeze your {card_desc}.\n\n**Action ID:** `{act_id}`\n\n*Please confirm below:*"
            else:
                resp_text = "I have retrieved your account and transaction details. Your current balance and records are up to date."

        elif "Risk Agent" in system_prompt:
            if any(k in user_text for k in ["block", "freeze", "lost", "stolen", "card"]):
                if "get_cards" not in tool_names_called:
                    func_calls = [MockFunctionCallWrapper("get_cards", {})]
                elif "propose_card_block" not in tool_names_called:
                    card_id = None
                    for tm in tool_msgs:
                        if tm.get("tool_name") == "get_cards":
                            items = _get_items(tm.get("content"))
                            if items:
                                card_id = _get_field(items[0], "id")
                                break
                    if card_id:
                        func_calls = [MockFunctionCallWrapper("propose_card_block", {"card_id": str(card_id), "reason": "Customer reported card lost or stolen"})]
                
                if not func_calls:
                    act_id = "pending"
                    card_desc = "debit card"
                    for tm in tool_msgs:
                        if tm.get("tool_name") == "get_cards":
                            items = _get_items(tm.get("content"))
                            if items:
                                last4 = _get_field(items[0], "last4")
                                if last4:
                                    card_desc = f"debit card ending in **{last4}**"
                        if tm.get("tool_name") == "propose_card_block":
                            c_dict = _get_data_dict(tm.get("content"))
                            act_id = str(c_dict.get("action_id", "pending"))
                    resp_text = f"⚠️ **Card Freeze Proposed**\n\nI have created a pending action to freeze your {card_desc}.\n\n**Action ID:** `{act_id}`\n\n*Please confirm below:*"
            elif any(k in user_text for k in ["fraud", "dispute", "unauthorized", "didn't make"]):
                if "get_disputes" not in tool_names_called:
                    func_calls = [MockFunctionCallWrapper("get_disputes", {})]
                if not func_calls:
                    resp_text = "🛡️ **Risk & Dispute Assessment**\n\nI have verified your account activity and active disputes. If you suspect an unauthorized charge, I can initiate a formal transaction dispute for your review."
            else:
                resp_text = "Your security request has been processed. If you requested a card block, please review the confirmation card."

        elif "Credit Agent" in system_prompt:
            if any(k in user_text for k in ["loan", "emi", "credit", "borrow"]):
                if "get_loan_products" not in tool_names_called:
                    func_calls = [MockFunctionCallWrapper("get_loan_products", {})]
                elif "calculate_loan_options" not in tool_names_called:
                    prod_id = "personal"
                    for tm in tool_msgs:
                        if tm.get("tool_name") == "get_loan_products" and isinstance(tm.get("content"), list) and tm["content"]:
                            prod_id = tm["content"][0].get("id", "personal")
                            break
                    func_calls = [MockFunctionCallWrapper("calculate_loan_options", {"product_id": prod_id, "amount": 50000.0, "tenure_months": 24})]
                
                if not func_calls:
                    resp_text = """### Loan Eligibility & Indicative EMI Breakdown

Based on our deterministic underwriting engine, you are **eligible** for the Personal/Business Loan!

- **Loan Amount:** ₹50,000.00
- **Tenure:** 24 months
- **Interest Rate:** 10.5% p.a.
- **Estimated Monthly EMI:** ₹2,319.00
- **Total Repayment:** ₹55,656.00

*Note: Indicative simulation, not a formal credit offer.*"""
            else:
                resp_text = "I have evaluated your credit profile. Your indicative loan eligibility and EMI estimates are ready."

        return MockResponse(resp_text, func_calls)

def get_llm_client(model_id: str = "gemini-2.5-flash") -> LLMClient:
    provider = os.getenv("LLM_PROVIDER", "mock")
    if provider == "mock":
        return MockLLMClient(model_id)
    return GeminiClient(model_id)
