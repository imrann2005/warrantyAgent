from typing import TypedDict, List

class WarrantyAgentState(TypedDict):
    """Represents the state of our warranty agent."""
    user_query: str
    product_id: str | None
    customer_id: str | None
    order_id: str | None
    product_name: str | None
    intent: str
    warranty_details: dict | None
    claim_status: str | None
    chat_history: List[tuple[str, str]]
    response: str