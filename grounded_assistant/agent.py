"""
Level 9: RAG & Grounding — Grounded Assistant

THE PROBLEM WITH LLMs:
  LLMs have a "knowledge cutoff" — they don't know recent events.
  Ask "Who won the election yesterday?" → Wrong or outdated answer!

THE SOLUTION: GROUNDING
  Give the LLM access to REAL, UP-TO-DATE information.

TWO APPROACHES IN ADK:

  ┌────────────────────────────────────────────────────────┐
  │  APPROACH 1: Google Search Grounding (Built-in)        │
  │                                                        │
  │  from google.adk.tools import google_search            │
  │  Agent(tools=[google_search])                          │
  │                                                        │
  │  ✅ Gemini automatically searches Google               │
  │  ✅ Returns source citations                           │
  │  ❌ Can't be mixed with custom tools                   │
  └────────────────────────────────────────────────────────┘

  ┌────────────────────────────────────────────────────────┐
  │  APPROACH 2: Local Knowledge Base (RAG Pattern)        │
  │                                                        │
  │  def search_knowledge_base(query) -> dict:             │
  │      # Search your own docs/database                   │
  │      return matching_results                           │
  │                                                        │
  │  ✅ Full control over your data                        │
  │  ✅ Can be mixed with other tools                      │
  │  ✅ Works with private/company data                    │
  └────────────────────────────────────────────────────────┘

THIS EXERCISE SHOWS BOTH APPROACHES:
  - Agent 1: Pure Google Search grounding (live web results)
  - Agent 2: Local knowledge base + Google Search (combined)

Try these:
  ✅ "What is the latest news about Google?"    → Live Google Search
  ✅ "What is our company refund policy?"       → Local knowledge base
  ✅ "What is our leave policy?"                → Local knowledge base
  ✅ "Compare our product prices with Tesla"    → BOTH sources combined!
"""

import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from google.adk.agents import Agent
from google.adk.tools.google_search_agent_tool import GoogleSearchAgentTool, create_google_search_agent

MODEL = os.getenv("MODEL", "gemini-2.5-flash")


# ══════════════════════════════════════════════════════════════
# LOCAL KNOWLEDGE BASE (simulates a company's internal docs)
# ══════════════════════════════════════════════════════════════
# In production, this would be a vector database (Pinecone, Weaviate,
# Vertex AI Vector Search, etc.). Here we use a simple in-memory list.

COMPANY_KNOWLEDGE = [
    {
        "id": "doc_001",
        "title": "Refund Policy",
        "category": "policy",
        "content": (
            "Acme Corp Refund Policy:\n"
            "- Full refund within 30 days of purchase\n"
            "- 50% refund between 30-60 days\n"
            "- No refund after 60 days\n"
            "- Digital products: refund within 7 days only\n"
            "- Contact support@acmecorp.com for all refund requests"
        ),
    },
    {
        "id": "doc_002",
        "title": "Leave Policy",
        "category": "hr",
        "content": (
            "Acme Corp Leave Policy:\n"
            "- Annual leave: 20 days/year\n"
            "- Sick leave: 10 days/year (doctor's note after 3 consecutive days)\n"
            "- Maternity: 26 weeks paid\n"
            "- Paternity: 2 weeks paid\n"
            "- Bereavement: 5 days\n"
            "- Work from home: up to 3 days/week with manager approval"
        ),
    },
    {
        "id": "doc_003",
        "title": "Product Catalog",
        "category": "sales",
        "content": (
            "Acme Corp Products:\n"
            "1. CloudSuite - Cloud collaboration platform - ₹999/user/month\n"
            "2. DataPro - Data analytics platform - ₹2499/user/month\n"
            "3. SecureShield - Cybersecurity suite - ₹1499/endpoint/month\n"
            "4. AIAssist - AI-powered customer support - ₹3999/month\n"
            "All products include 24/7 support and 99.9% uptime SLA"
        ),
    },
    {
        "id": "doc_004",
        "title": "Company Overview",
        "category": "general",
        "content": (
            "Acme Corp - Founded 2015 in Bangalore, India\n"
            "- 500+ employees across India, US, Singapore\n"
            "- Series C funded ($50M)\n"
            "- Customers: 200+ enterprises including Reliance, HDFC, Infosys\n"
            "- Mission: Making enterprise software simple and affordable"
        ),
    },
]


def search_knowledge_base(query: str) -> dict:
    """Search the company's internal knowledge base for relevant information.

    This simulates a RAG (Retrieval-Augmented Generation) pipeline:
    1. Takes a user query
    2. Searches through company documents
    3. Returns the most relevant matches

    In production, this would use vector embeddings and similarity search.
    Here we use simple keyword matching for demonstration.

    Args:
        query: The search query (e.g. "refund policy", "product pricing").

    Returns:
        A dictionary with matching documents and their content.
    """
    query_lower = query.lower()
    results = []

    for doc in COMPANY_KNOWLEDGE:
        # Simple keyword matching (in production: vector similarity)
        title_match = any(
            word in doc["title"].lower() for word in query_lower.split()
        )
        content_match = any(
            word in doc["content"].lower() for word in query_lower.split()
        )

        if title_match or content_match:
            results.append({
                "document_id": doc["id"],
                "title": doc["title"],
                "category": doc["category"],
                "content": doc["content"],
                "source": "Acme Corp Internal Knowledge Base",
            })

    if results:
        print(f"📚 Knowledge base: Found {len(results)} matching documents")
        return {
            "found": True,
            "total_results": len(results),
            "documents": results,
        }
    else:
        print(f"📚 Knowledge base: No results for '{query}'")
        return {
            "found": False,
            "total_results": 0,
            "documents": [],
            "suggestion": "No internal documents found. You may want to search the web.",
        }


# ══════════════════════════════════════════════════════════════
# THE GROUNDED AGENT — Google Search + Local Knowledge
# ══════════════════════════════════════════════════════════════
# google_search (built-in) can't be mixed with custom tools.
# GoogleSearchAgentTool wraps it in a sub-agent, solving this!

search_tool = GoogleSearchAgentTool(
    agent=create_google_search_agent(model=MODEL),
)

root_agent = Agent(
    name="grounded_assistant",
    model=MODEL,
    description="A grounded assistant with access to Google Search and internal knowledge base.",
    instruction=(
        "You are a helpful assistant for Acme Corp that provides FACTUAL, "
        "SOURCE-BACKED answers.\n\n"
        "YOU HAVE TWO INFORMATION SOURCES:\n\n"
        "1. **Internal Knowledge Base** (search_knowledge_base tool):\n"
        "   - Use for company-specific questions: policies, products, HR, etc.\n"
        "   - ALWAYS cite the document title and ID.\n\n"
        "2. **Google Search** (google_search_agent tool):\n"
        "   - Use for real-world, current events, external information.\n"
        "   - Pass a search query as the 'request' argument.\n\n"
        "RULES:\n"
        "- For company questions → search internal knowledge base FIRST.\n"
        "- For external/current events → use the google_search_agent tool.\n"
        "- ALWAYS cite your sources (document ID or web URL).\n"
        "- If no reliable source found, say 'I don't have verified information.'\n"
        "- NEVER make up facts that aren't in your sources.\n"
    ),
    tools=[search_knowledge_base, search_tool],
)
