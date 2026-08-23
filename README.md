# Multi-Agent Customer Support System

A production-ready, multi-agent AI customer support system built with LangGraph, Anthropic Claude, and Weaviate. Multiple specialist AI agents work together to handle customer tickets — each with their own domain knowledge base — with automatic escalation to human reviewers when confidence is low.

---

## Live Demo

| Interface | URL |
|---|---|
| Customer Chat | `https://your-app.streamlit.app` |
| Staff Panel | `https://your-app.streamlit.app/staff_panel` |

**Staff Panel Demo Credentials:**
- Username: `demo` | Password: `demo123`

---

## What Makes This Unique

Most AI support systems use a single agent to handle everything. This system uses a **supervisor pattern** with domain-specialist agents — each with its own isolated knowledge base:

| Feature | Standard Chatbot | This System |
|---|---|---|
| Single agent | ✅ | ❌ |
| Domain specialist agents | ❌ | ✅ 3 agents |
| Isolated knowledge bases | ❌ | ✅ per domain |
| Confidence scoring | ❌ | ✅ |
| Human escalation | ❌ | ✅ automatic |
| Cloud database for tickets | ❌ | ✅ Supabase |
| Staff authentication | ❌ | ✅ |

---

## Architecture

```
Customer sends a ticket
        │
        ▼
┌─────────────────────┐
│   Supervisor Agent  │  ← Anthropic Claude classifies ticket
│   (LangGraph node)  │    billing / technical / general
└────────┬────────────┘
         │
   ┌─────┴──────┬──────────┐
   ▼            ▼          ▼
Billing      Technical   General
Agent         Agent       Agent
   │            │          │
   ▼            ▼          ▼
Weaviate     Weaviate   Weaviate
(billing     (tech      (general
 docs)        docs)      docs)
   │
   ▼
Confidence check
   │
   ├── High confidence → Answer customer
   └── Low confidence → Escalate to human
                              │
                              ▼
                         Supabase DB
                    (stores escalated tickets)
                              │
                              ▼
                       Staff Panel UI
                    (review & resolve)
```

---

## LangGraph State Graph

```
START
  ↓
supervisor_node     ← classifies ticket category
  ↓
(conditional edge)
  ↓
billing_node / technical_node / general_node
  ↓
(conditional edge — confident or escalate?)
  ↓
answer customer / escalation_node
  ↓
END
```

---

## Tech Stack

| Component | Tool | Purpose |
|---|---|---|
| Agent orchestration | LangGraph | State graph, conditional routing, supervisor pattern |
| LLM | Anthropic Claude (Haiku) | Ticket classification, answer generation, confidence scoring |
| Knowledge base | Weaviate Cloud | Vector search over domain-specific support documents |
| Embeddings | sentence-transformers | Local CPU-based embeddings (all-MiniLM-L6-v2) |
| Escalation storage | Supabase (PostgreSQL) | Cloud database for escalated tickets |
| Customer UI | Streamlit | Chat interface with conversation memory |
| Staff UI | Streamlit + streamlit-authenticator | Authenticated staff panel for ticket review |
| Deployment | Streamlit Cloud | Free public deployment |

**100% Free APIs and hosting**

---

## 💬 Example Queries to Try

### Billing Questions
- "My payment failed yesterday"
- "I want to request a refund for my purchase"
- "My subscription was charged twice this month"
- "What payment methods do you accept?"
- "How do I get an invoice for my purchase?"

### Technical Questions
- "The app keeps crashing when I open it"
- "I am getting error code 500"
- "I cannot log into my account"
- "The app is running very slowly"
- "How do I update the app to the latest version?"

### General Questions
- "What are your customer support working hours?"
- "How do I contact support?"
- "How do I delete my account?"
- "Where is your company located?"

### Escalation Test
- "I need to cancel my enterprise contract and get a full refund for 3 years"
- "Someone hacked my account and deleted all my data"

> These last two will be escalated to the human reviewer since the knowledge base does not have enough information to answer them confidently. Check the Staff Panel to see them appear!

---

## Getting Started

### Prerequisites
- Python 3.10+
- Free [Anthropic API key](https://console.anthropic.com)
- Free [Weaviate Cloud](https://console.weaviate.cloud) cluster
- Free [Supabase](https://supabase.com) project

### Installation

```bash
# Clone the repo
git clone https://github.com/Akoparna24/multi-agent-customer-support.git
cd multi-agent-customer-support

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

### Setup

**1. Create `.env` file:**
```
ANTHROPIC_API_KEY=your_anthropic_key
WEAVIATE_URL=your_weaviate_cluster_url
WEAVIATE_API_KEY=your_weaviate_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_secret_key
```

**2. Create Supabase table:**
```sql
CREATE TABLE escalated_tickets (
    id          TEXT PRIMARY KEY,
    ticket      TEXT NOT NULL,
    domain      TEXT NOT NULL,
    reason      TEXT,
    context     TEXT,
    status      TEXT DEFAULT 'pending',
    timestamp   TEXT NOT NULL
);
```

**3. Set up knowledge base:**
```bash
python -c "from src.knowledge_base import get_weaviate_client, create_collections, ingest_documents; c = get_weaviate_client(); create_collections(c); ingest_documents(c); c.close()"
```

**4. Run the app:**
```bash
streamlit run app.py
```

---

## How It Works

### Customer Flow
1. Customer types a support ticket in the chat
2. Anthropic Claude first checks if it is a genuine ticket or casual message
3. If genuine, supervisor agent classifies it into billing / technical / general
4. Specialist agent searches Weaviate for relevant knowledge
5. Claude generates a grounded answer with a confidence score
6. If confidence > 0.5 → customer gets the answer
7. If confidence < 0.5 → ticket escalated to human reviewer

### Staff Flow
1. Staff logs into the Staff Panel with credentials
2. Views all pending escalated tickets
3. Reviews ticket details and context
4. Clicks Resolve to close the ticket

---

## Project Structure

```
multi_agent_customer_support/
├── src/
│   ├── config.py           # Centralized secret management
│   ├── knowledge_base.py   # Weaviate setup and document ingestion
│   ├── agents.py           # Specialist agents + LangGraph nodes
│   ├── supervisor.py       # Supervisor agent + classification
│   ├── graph.py            # LangGraph graph assembly
│   └── escalation.py       # Supabase escalation handler
├── pages/
│   └── staff_panel.py      # Authenticated staff UI
├── data/
│   ├── billing_docs/       # Billing FAQ documents
│   ├── tech_docs/          # Technical support documents
│   └── general_docs/       # General FAQ documents
├── app.py                  # Customer chat UI
├── requirements.txt
└── .env                    # API keys (never pushed to GitHub)
```

---

## Technical Highlights

- Implemented **LangGraph supervisor pattern** to orchestrate domain-specialist agents with conditional routing based on ticket classification
- Designed **domain-isolated Weaviate vector search** per agent — billing agent only searches billing docs, preventing cross-domain retrieval noise
- Built **confidence-based human-in-the-loop escalation** — agents self-assess and route to human reviewers rather than hallucinating low-confidence answers
- Used **Anthropic Claude** for semantic ticket pre-classification, specialist answer generation, and casual message detection in a single pipeline
- Integrated **Supabase PostgreSQL** as a cloud-persistent escalation queue — handles concurrent writes from multiple users without data loss
- Built **role-based UI** with streamlit-authenticator — separate customer chat and authenticated staff panel
- Implemented **conversation memory** by passing chat history as context to each graph invocation

---

## Security

- API keys stored as Streamlit Cloud secrets — never hardcoded
- Staff panel protected with username and password authentication
- `.env` file excluded from GitHub via `.gitignore`
- Supabase RLS can be enabled for row-level data isolation

---

## License

MIT License — free to use and modify.
