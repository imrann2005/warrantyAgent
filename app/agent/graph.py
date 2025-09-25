from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.pydantic_v1 import BaseModel, Field

# Import state and all necessary services
from app.agent.state import WarrantyAgentState
from app.services import database
from app.services import rag # RAG service for FAQs

# --- 1. Define Pydantic Schemas for LLM Tool Calling ---
# These schemas describe the agent's specific data-lookup capabilities to the LLM.

class FetchOrderWarranty(BaseModel):
    """Gets warranty details using customer ID, order ID, and product name."""
    customer_id: str = Field(description="The customer's identifier, like 'CUST1001'")
    order_id: str = Field(description="The unique identifier for the order, like 'ORD98765'")
    product_name: str = Field(description="The name of the product to check, like 'QuantumBook Pro 15'")

class FetchDetailsBySN(BaseModel):
    """Gets warranty details using a unique product serial number."""
    serial_number: str = Field(description="The product's serial number, which typically starts with 'SN'")


# --- 2. Define Graph Nodes ---

def route_intent_node(state: WarrantyAgentState):
    """
    Uses an LLM with tool-calling to identify the user's intent and extract entities.
    This replaces the previous regex-based logic.
    """
    print("---NODE: Routing Intent with LLM---")
    query = state['user_query']
    
    # Initialize the LLM and bind our tools to it
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    tools = [FetchOrderWarranty, FetchDetailsBySN]
    llm_with_tools = llm.bind_tools(tools)
    
    # Invoke the LLM with the user's query
    response = llm_with_tools.invoke(query)
    
    # Check if the LLM decided to call a tool
    if not response.tool_calls:
        # If no tool is called, it's a general question for the RAG system
        print("---LLM Route: Defaulting to FAQ RAG.---")
        state['intent'] = 'answer_faq'
    else:
        # The LLM chose a tool; extract the details
        tool_call = response.tool_calls[0]
        tool_name = tool_call['name']
        tool_args = tool_call['args']
        
        if tool_name == "FetchOrderWarranty":
            print(f"---LLM Route: Matched FetchOrderWarranty with args: {tool_args}---")
            state['intent'] = 'fetch_order_warranty'
            state.update(tool_args) # Directly update state from tool arguments
        elif tool_name == "FetchDetailsBySN":
            print(f"---LLM Route: Matched FetchDetailsBySN with args: {tool_args}---")
            state['intent'] = 'fetch_details'
            state['product_id'] = tool_args['serial_number']
        else:
            state['intent'] = 'answer_faq' # Fallback
            
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
    """
    This node now uses the RAG service to answer general questions.
    """
    print("---NODE: Answering FAQ via RAG---")
    response = rag.query_faq_rag(state['user_query'])
    state['response'] = response
    return state


# --- 3. Define Edge Logic ---
def decide_next_node(state: WarrantyAgentState):
    """Conditional logic to decide the next step."""
    return state.get("intent", 'answer_faq')


# --- 4. Assemble the Graph ---
workflow = StateGraph(WarrantyAgentState)

workflow.add_node("router", route_intent_node) # Uses the new LLM router
workflow.add_node("fetch_order_warranty", fetch_order_warranty_node)
workflow.add_node("fetch_details", fetch_details_node)
workflow.add_node("answer_faq", answer_faq_node) # Uses the RAG-powered FAQ node

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