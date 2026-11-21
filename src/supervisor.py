import anthropic
from rich.console import Console
from src.config import ANTHROPIC_API_KEY

console = Console()

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
MODEL = "claude-haiku-4-5"

def build_prompt(ticket: str) -> str:
    """The classifier prompt. Shared by the app and the evaluation script."""
    return f"""You are a customer support ticket classifier.

Classify the following customer ticket into exactly one of these categories:
- billing: payment issues, refunds, invoices, subscription charges, pricing
- technical: app bugs, crashes, errors, login issues, performance problems
- general: working hours, contact info, company info, account settings, policies

Customer ticket: {ticket}

Reply with ONLY one word — either 'billing', 'technical', or 'general'.
No explanation, no punctuation, just the single category word."""


def classify_ticket_raw(ticket: str) -> tuple[str, int, int]:
    """
    Same call as classify_ticket, but returns the model's raw reply plus token
    counts, without hiding invalid replies. Used by evals/run_baseline.py.
    """
    response = client.messages.create(
        model=MODEL,
        max_tokens=10,
        messages=[{"role": "user", "content": build_prompt(ticket)}]
    )
    return (
        response.content[0].text,
        response.usage.input_tokens,
        response.usage.output_tokens,
    )


def classify_ticket(ticket: str) -> str:
    """
    Classify a support ticket into billing, technical, or general.
    Returns one of: 'billing', 'technical', 'general'
    """
    raw, _, _ = classify_ticket_raw(ticket)
    category = raw.strip().lower()

    # Validate — default to general if unexpected response
    if category not in ["billing", "technical", "general"]:
        category = "general"

    console.print(f"Ticket classified as: {category}")
    return category

def supervisor_node(state: dict) -> dict:
    """LangGraph node — classifies ticket."""
    category = classify_ticket(state["ticket"])
    return {"category": category}