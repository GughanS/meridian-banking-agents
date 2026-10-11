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

        if "Supervisor" in system_prompt:
            if any(k in user_text for k in ["loan", "emi", "credit", "borrow"]):
                resp_text = "CreditAgent"
            elif any(k in user_text for k in ["fraud", "block", "freeze", "dispute", "stolen", "lost", "compromised", "unauthorized", "didn't make"]):
                resp_text = "RiskAgent"
            elif any(k in user_text for k in ["balance", "transaction", "address", "account", "transfer"]):
                resp_text = "CustomerAgent"
            else:
                resp_text = "CustomerAgent"
        elif "Customer Agent" in system_prompt:
            resp_text = "I have retrieved your account and transaction details. Your current balance and records are up to date."
        elif "Risk Agent" in system_prompt:
            resp_text = "Your card management request has been processed. If you requested a card block, please review the confirmation card."
        elif "Credit Agent" in system_prompt:
            resp_text = "I have evaluated your credit profile. Your indicative loan eligibility and EMI estimates are ready."

        class MockPart:
            def __init__(self, text: str, fc: Any = None):
                self.text = text
                self.function_call = fc
        
        class MockCandidate:
            def __init__(self, text: str):
                self.content = types.Content(role="model", parts=[MockPart(text)])
            
        class MockResponse:
            def __init__(self, text: str):
                self.candidates = [MockCandidate(text)]
                self.text = text
                self.function_calls = func_calls
            
        return MockResponse(resp_text)

def get_llm_client(model_id: str = "gemini-2.5-flash") -> LLMClient:
    provider = os.getenv("LLM_PROVIDER", "mock")
    if provider == "mock":
        return MockLLMClient(model_id)
    return GeminiClient(model_id)
