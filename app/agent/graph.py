import re
from langgraph.graph import StateGraph, END

# Import state and database services
from app.agent.state import WarrantyAgentState
from app.services import database

# --- Node Definitions ---
def route_intent_node(state: WarrantyAgentState):
    """Determines user intent from the query."""
    print("---NODE: Routing Intent---")
    query = state['user_query']
    
    cust_match = re.search(r"customer (\w+@?\w+\.?\w+)|cust_id (\w+)", query, re.IGNORECASE)
    order_match = re.search(r"order_id (\w+)", query, re.IGNORECASE)
    prod_match = re.search(r"product ([\w\s]+)", query, re.IGNORECASE)
    sn_match = re.search(r"SN\w+", query)

    if cust_match and order_match and prod_match:
        state['intent'] = 'fetch_order_warranty'
        state['customer_id'] = cust_match.group(1) or cust_match.group(2)
        state['order_id'] = order_match.group(1).strip()
        state['product_name'] = prod_match.group(1).strip()
    elif sn_match:
        state['intent'] = 'fetch_details'
        state['product_id'] = sn_match.group(0)
    else:
        state['intent'] = 'answer_faq'
    return state

def fetch_order_warranty_node(state: WarrantyAgentState):
    """Node that calls the database service for order-based warranty lookup."""
    print("---NODE: Fetching Order Warranty---")
    details = database.get_warranty_status_from_order(
        state['customer_id'], state['order_id'], state['product_name']
    )
    if details['status'] == 'Error':
        state['response'] = details['message']
    else:
        state['response'] = f"The warranty is {details['status']}. It expires on {details['expiry_date']}."
    return state

def fetch_details_node(state: WarrantyAgentState):
    """Node for serial number lookup."""
    print("---NODE: Fetching Details by SN---")
    details = database.fetch_warranty_details_by_sn(state['product_id'])
    state['response'] = details['message']
    return state

def answer_faq_node(state: WarrantyAgentState):
    """Fallback node for general questions."""
    print("---NODE: Answering FAQ---")
    state['response'] = "I can help with warranty status. Please provide a serial number, or a customer ID, order ID, and product name."
    return state

# --- Edge Logic ---
def decide_next_node(state: WarrantyAgentState):
    """Conditional logic to decide the next step."""
    return state.get("intent", 'answer_faq')

# --- Graph Assembly ---
workflow = StateGraph(WarrantyAgentState)
workflow.add_node("router", route_intent_node)
workflow.add_node("fetch_order_warranty", fetch_order_warranty_node)
workflow.add_node("fetch_details", fetch_details_node)
workflow.add_node("answer_faq", answer_faq_node)
workflow.set_entry_point("router")
workflow.add_conditional_edges(
    "router",
    decide_next_node,
    {
        "fetch_order_warranty": "fetch_order_warranty",
        "fetch_details": "fetch_details",
        "answer_faq": "answer_faq",
    }
)
workflow.add_edge("fetch_order_warranty", END)
workflow.add_edge("fetch_details", END)
workflow.add_edge("answer_faq", END)
app = workflow.compile()
