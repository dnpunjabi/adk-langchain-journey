"""
LangChain Level 9: RAG (Retrieval Augmented Generation)

ADK Equivalent: `KnowledgeBase` + `search_knowledge` internal tool
LangChain Concept: `VectorStores`, `Embeddings`, and `create_retrieval_chain`

EXPLANATION:
In ADK, we created a `KnowledgeBase` object and easily attached it to the agent.
In LangChain, building RAG requires assembling several specific components:

1. **Loader/Splitter**: Read the file and split it into chunks.
2. **Embeddings Model**: A model that turns text chunks into number arrays (vectors).
3. **VectorStore**: A database that holds those vectors and allows similarity search.
4. **Retriever**: A wrapper around the VectorStore that plugs into an LCEL chain.
5. **Retrieval Chain**: An LCEL setup that takes a query, fetches docs, injects them 
                      into the prompt, and sends them to the LLM.

Below, we build a pure LangChain implementation of querying local documents.
"""

import os
from dotenv import load_dotenv

# LangChain Imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.vectorstores import InMemoryVectorStore

# LangChain provides powerful helper functions specifically for building RAG chains
# (Note: In this tutorial we use pure LCEL instead of create_retrieval_chain to show the raw mechanics)

load_dotenv()

# --- 1. Create Mock Documents ---
# In reality, you would use PyPDFLoader or TextLoader to load these files.
KNOWLEDGE_DOCS = [
    Document(
        page_content="Acme Corp Return Policy: We accept returns within 30 days of purchase.", 
        metadata={"source": "policy.txt"}
    ),
    Document(
        page_content="Acme Corp Warranty: All electronics come with a 1-year limited warranty.", 
        metadata={"source": "warranty.txt"}
    ),
    Document(
        page_content="Acme Corp CEO is Jane Doe. She founded the company in 2021.", 
        metadata={"source": "about.txt"}
    )
]

def setup_rag_chain():
    """Builds the entire RAG pipeline and returns the execution chain."""
    
    # --- 2. Initialize Embeddings ---
    # This specifically uses Gemini's text embedding model to convert text to vectors
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    
    # --- 3. Build Vector Store & Retriever ---
    # We use InMemoryVectorStore to keep things lightweight (no FAISS/Chroma installs needed)
    vectorstore = InMemoryVectorStore.from_documents(
        documents=KNOWLEDGE_DOCS,
        embedding=embeddings
    )
    
    # The retriever just exposes a .invoke(query) method to find similar docs
    retriever = vectorstore.as_retriever(search_kwargs={"k": 2}) # Get top 2 matches
    
    # --- 4. Initialize Chat Model ---
    llm = ChatGoogleGenerativeAI(model=os.getenv("MODEL", "gemini-2.5-flash"), temperature=0.0)
    
    # --- 5. Build the Generate Prompt ---
    # We must include a `{context}` variable where the retrieved docs will be injected
    system_prompt = (
        "You are an assistant for question-answering tasks. "
        "Use the following pieces of retrieved context to answer the question. "
        "If you don't know the answer, say that you don't know.\n\n"
        "Context: {context}"
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}")
    ])
    
    # --- 6. Assemble the Chain ---
    # --- 6. The Pure LCEL RAG Approach ---
    # Instead of using opaque helper functions, we will do it manually.
    # It demonstrates EXACTLY what RAG is:
    
    # We return the retriever, prompt, and llm so we can run them in sequence.
    return retriever, prompt, llm

def run_level(query: str):
    """Executes Level 9 logic for the Streamlit UI."""
    retriever, prompt, llm = setup_rag_chain()
    
    # 1. RETRIEVE the relevant documents
    docs = retriever.invoke(query)
    
    # FORMAT the documents into a single string
    context_text = "\n\n".join([doc.page_content for doc in docs])
    
    # 2. GENERATE the response
    chain = prompt | llm
    response = chain.invoke({"context": context_text, "input": query})
    
    return {
        "answer": response.content,
        "context": docs
    }

if __name__ == "__main__":
    print("🤖 LangChain RAG Tester (Level 9)\n")
    
    query = "What is the return policy for electronics?"
    print(f"User: {query}")
    
    result = run_level(query)
    
    print("\n✅ Answer:")
    print(result["answer"])
    
    print("\n📚 Sourced from:")
    for i, doc in enumerate(result["context"]):
        print(f"[{i+1}] {doc.metadata['source']}: {doc.page_content[:50]}...")
