import operator
from collections.abc import Sequence
from typing import Annotated, TypedDict
from uuid import UUID


class AgentState(TypedDict):
    messages: Annotated[Sequence[dict], operator.add]
    next_agent: str | None
    customer_id: UUID
    session_id: UUID
