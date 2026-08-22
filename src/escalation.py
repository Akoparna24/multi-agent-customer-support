import os
import json
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv
from rich.console import Console

load_dotenv()
console = Console()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

def escalate_ticket(ticket: str, domain: str, context: list, reason: str = "") -> dict:
    """Save a ticket to Supabase for human review."""

    escalated = {
        "id":        datetime.now().strftime("%Y%m%d%H%M%S"),
        "ticket":    ticket,
        "domain":    domain,
        "reason":    reason,
        "context":   json.dumps(context),
        "status":    "pending",
        "timestamp": datetime.now().isoformat(),
    }

    supabase.table("escalated_tickets").insert(escalated).execute()
    console.print(f"Ticket escalated to Supabase — ID: {escalated['id']}")
    return escalated


def get_escalated_tickets() -> list:
    """Return all pending escalated tickets from Supabase."""
    response = supabase.table("escalated_tickets")\
        .select("*")\
        .eq("status", "pending")\
        .execute()
    return response.data


def resolve_ticket(ticket_id: str) -> bool:
    """Mark a ticket as resolved in Supabase."""
    supabase.table("escalated_tickets")\
        .update({"status": "resolved"})\
        .eq("id", ticket_id)\
        .execute()
    console.print(f"Ticket {ticket_id} resolved!")
    return True

def escalation_node(state: dict) -> dict:
    """LangGraph node — escalates low confidence tickets."""
    escalate_ticket(
        ticket=state["ticket"],
        domain=state["category"],
        context=state["context"],
        reason=f"Low confidence: {state['confidence']}"
    )
    return {
        "answer":    "Your ticket has been escalated to our human support team. We will get back to you within 24 hours.",
        "escalated": True,
    }