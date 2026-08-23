import anthropic
from src.knowledge_base import search_documents, embedding_model
from rich.console import Console
from src.config import ANTHROPIC_API_KEY

console = Console()

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
MODEL = "claude-haiku-4-5"
CONFIDENCE_THRESHOLD = 0.5

def run_agent(weaviate_client, ticket: str, domain: str) -> dict:
    """
    Run a specialist agent for a given domain.
    Searches Weaviate, generates answer, returns confidence score.
    """

    # Step 1 — Retrieve relevant chunks from Weaviate
    chunks = search_documents(weaviate_client, ticket, domain=domain, limit=3)

    if not chunks:
        return {
            "answer":     "I could not find relevant information.",
            "confidence": 0.0,
            "domain":     domain,
            "context":    [],
        }

    # Step 2 — Build context from chunks
    context = ""
    for i, chunk in enumerate(chunks, start=1):
        context += f"\n--- Result {i} (score: {chunk['score']}) ---\n"
        context += chunk["content"]
        context += "\n"

    # Step 3 — Generate answer with confidence score
    prompt = f"""You are a {domain} support specialist.

Here is the relevant information from our knowledge base:
{context}

Customer ticket: {ticket}

Instructions:
- Answer the customer's question based ONLY on the context above
- If the context doesn't fully answer the question, say so honestly
- At the end of your response, on a new line write exactly:
  CONFIDENCE: <number between 0.0 and 1.0>
  Where 1.0 means you are fully confident and 0.0 means not confident at all
- Do not mention chunks or scores to the customer"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    raw_answer = response.content[0].text.strip()

    # Step 4 — Parse confidence score from response
    confidence = 0.5  # default
    answer     = raw_answer

    if "CONFIDENCE:" in raw_answer:
        parts      = raw_answer.rsplit("CONFIDENCE:", 1)
        answer     = parts[0].strip()
        try:
            confidence = float(parts[1].strip())
        except ValueError:
            confidence = 0.5

    return {
        "answer":     answer,
        "confidence": confidence,
        "domain":     domain,
        "context":    chunks,
    }

def billing_node(state: dict) -> dict:
    """LangGraph node — handles billing tickets."""
    from src.graph import weaviate_client
    result = run_agent(weaviate_client, state["ticket"], "billing")
    return {
        "answer":     result["answer"],
        "confidence": result["confidence"],
        "agent_used": "billing",
        "context":    result["context"],
        "escalated":  result["confidence"] < CONFIDENCE_THRESHOLD,
    }

def technical_node(state: dict) -> dict:
    """LangGraph node — handles technical tickets."""
    from src.graph import weaviate_client
    result = run_agent(weaviate_client, state["ticket"], "technical")
    return {
        "answer":     result["answer"],
        "confidence": result["confidence"],
        "agent_used": "technical",
        "context":    result["context"],
        "escalated":  result["confidence"] < CONFIDENCE_THRESHOLD,
    }

def general_node(state: dict) -> dict:
    """LangGraph node — handles general tickets."""
    from src.graph import weaviate_client
    result = run_agent(weaviate_client, state["ticket"], "general")
    return {
        "answer":     result["answer"],
        "confidence": result["confidence"],
        "agent_used": "general",
        "context":    result["context"],
        "escalated":  result["confidence"] < CONFIDENCE_THRESHOLD,
    }