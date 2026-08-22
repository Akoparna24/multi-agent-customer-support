import os
import weaviate
from weaviate.auth import AuthApiKey
from typing import TypedDict
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END

from src.supervisor  import supervisor_node
from src.agents      import billing_node, technical_node, general_node
from src.escalation  import escalation_node

load_dotenv()

# Shared Weaviate client used by agent nodes
weaviate_client = weaviate.connect_to_weaviate_cloud(
    cluster_url=os.getenv("WEAVIATE_URL"),
    auth_credentials=AuthApiKey(os.getenv("WEAVIATE_API_KEY"))
)

# ── State ─────────────────────────────────────────────────────────────────────
class SupportState(TypedDict):
    ticket     : str
    category   : str
    answer     : str
    confidence : float
    escalated  : bool
    agent_used : str
    context    : list

# ── Routing functions ─────────────────────────────────────────────────────────
def route_to_agent(state: SupportState) -> str:
    """Route to the correct agent based on category."""
    return state["category"]

def route_to_answer_or_escalate(state: SupportState) -> str:
    """Route to escalation if confidence is low."""
    if state["escalated"]:
        return "escalation"
    return END

# ── Graph assembly ────────────────────────────────────────────────────────────
def build_graph():
    graph = StateGraph(SupportState)

    # Add nodes
    graph.add_node("supervisor",  supervisor_node)
    graph.add_node("billing",     billing_node)
    graph.add_node("technical",   technical_node)
    graph.add_node("general",     general_node)
    graph.add_node("escalation",  escalation_node)

    # Entry point
    graph.add_edge(START, "supervisor")

    # Supervisor routes to correct agent
    graph.add_conditional_edges(
        "supervisor",
        route_to_agent,
        {
            "billing":   "billing",
            "technical": "technical",
            "general":   "general",
        }
    )

    # Each agent either answers or escalates
    for agent in ["billing", "technical", "general"]:
        graph.add_conditional_edges(
            agent,
            route_to_answer_or_escalate,
            {
                "escalation": "escalation",
                END:          END,
            }
        )

    # Escalation always ends
    graph.add_edge("escalation", END)

    return graph.compile()

# Compiled graph — ready to use
support_graph = build_graph()