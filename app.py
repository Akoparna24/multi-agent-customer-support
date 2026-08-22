import streamlit as st
import os
import anthropic
from dotenv import load_dotenv
from src.graph import support_graph

load_dotenv()

anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def is_support_ticket(message: str, history: str) -> tuple[bool, str]:
    """
    Ask Claude whether this is a support ticket or a casual reply.
    Returns (is_ticket, casual_response)
    """
    prompt = f"""You are a customer support assistant.

Conversation history:
{history}

Latest message from customer: "{message}"

Decide if this is:
A) A genuine support ticket that needs to be routed to a specialist
B) A casual conversational reply (like greetings, thanks, yes/no responses, goodbye)

If A — reply with exactly: TICKET
If B — reply with a short, friendly conversational response (1-2 sentences max)"""

    response = anthropic_client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}]
    )

    reply = response.content[0].text.strip()

    if reply.upper() == "TICKET":
        return True, ""
    return False, reply


st.set_page_config(
    page_title="Customer Support",
    page_icon="💬",
    layout="centered"
)

st.title("💬 Customer Support")
st.caption("Ask me anything about billing, technical issues, or general queries.")

# Initialize chat history
if "messages" not in st.session_state or len(st.session_state.messages) == 0:
    st.session_state.messages = [{
        "role":    "assistant",
        "content": "👋 Welcome to Customer Support! How can I help you today?"
    }]

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Handle user input
if prompt := st.chat_input("Type your question here..."):

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Build conversation history
    history = ""
    for msg in st.session_state.messages[-6:]:
        role = "Customer" if msg["role"] == "user" else "Agent"
        history += f"{role}: {msg['content']}\n"

    # Ask Claude if this is a ticket or casual reply
    is_ticket, casual_reply = is_support_ticket(prompt, history)

    if not is_ticket:
        with st.chat_message("assistant"):
            st.markdown(casual_reply)
        st.session_state.messages.append({
            "role":    "assistant",
            "content": casual_reply
        })
        st.stop()

    # It's a real ticket — run through graph
    full_ticket = f"Conversation history:\n{history}\nLatest message: {prompt}"

    with st.chat_message("assistant"):
        with st.spinner("Looking into this for you..."):
            result = support_graph.invoke({
                "ticket":     full_ticket,
                "category":   "",
                "answer":     "",
                "confidence": 0.0,
                "escalated":  False,
                "agent_used": "",
                "context":    [],
            })

        department = {
            "billing":   "💳 Billing Support",
            "technical": "🔧 Technical Support",
            "general":   "ℹ️ General Support",
        }.get(result["agent_used"], "Support")

        response = f"**{department}**\n\n{result['answer']}"
        st.markdown(response)

    st.session_state.messages.append({
        "role":    "assistant",
        "content": response
    })