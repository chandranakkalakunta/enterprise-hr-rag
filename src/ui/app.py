"""
Streamlit UI — Enterprise HR RAG Platform
Employee-facing chat interface for HR Q&A
"""
import streamlit as st
import os
import sys
import logging
from datetime import datetime

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../generation"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../retrieval"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../ingestion"))

logging.basicConfig(level=logging.WARNING)

# ── Page Config ────────────────────────────────────────────
st.set_page_config(
    page_title="TechCorp HR Assistant",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ─────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1B3A6B 0%, #2E75B6 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
    }
    .source-badge {
        background: #E8F4F8;
        border: 1px solid #2E75B6;
        border-radius: 5px;
        padding: 3px 8px;
        font-size: 12px;
        color: #1B3A6B;
        margin: 2px;
        display: inline-block;
    }
    .metric-card {
        background: #F8F9FA;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ── Initialize RAG Engine ──────────────────────────────────
@st.cache_resource(ttl=3600)
def get_rag_engine():
    """Initialize RAG engine (cached for performance)."""
    from rag_engine import RAGEngine

    api_key = os.environ.get("GEMINI_API_KEY", "")
    project_id = os.environ.get("PROJECT_ID", "hr-rag-dev")
    environment = os.environ.get("ENVIRONMENT", "dev")

    return RAGEngine(
        project_id=project_id,
        gemini_api_key=api_key,
        environment=environment
    )

# ── Header ─────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🏢 TechCorp HR Assistant</h1>
    <p>Ask me anything about HR policies, leave, benefits, and more!</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📚 Available Policies")
    policies = [
        "📅 Leave Policy",
        "🚀 Onboarding Policy",
        "✅ Code of Conduct",
        "🏠 Remote Work Policy",
        "⭐ Performance Management",
        "💰 Compensation & Benefits",
        "✈️ Travel & Expense",
        "📖 Training & Development",
        "🤝 Grievance Redressal",
        "🔒 IT Security Policy"
    ]
    for policy in policies:
        st.markdown(f"- {policy}")

    st.divider()
    st.markdown("### 💡 Sample Questions")
    sample_questions = [
        "How many leave days do I get?",
        "What is the WFH policy?",
        "How do I claim travel expenses?",
        "What is the PIP process?",
        "How to report a grievance?"
    ]
    for q in sample_questions:
        if st.button(q, use_container_width=True, key=q):
            st.session_state.sample_query = q

    st.divider()
    st.markdown("### ℹ️ About")
    st.markdown("""
    Powered by:
    - 🤖 Gemini 2.5 Flash
    - 🔍 Hybrid RAG Search
    - 📊 BM25 + Vector Search
    - ☁️ Google Cloud Platform
    """)

# ── Chat Interface ─────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant",
        "content": "Hello! I am your HR Policy Assistant. Ask me anything about TechCorp India's HR policies!",
        "sources": []
    })

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            st.markdown("**Sources:**")
            for source in message["sources"]:
                st.markdown(
                    f'<span class="source-badge">📄 {source}</span>',
                    unsafe_allow_html=True
                )

# Handle sample question
if "sample_query" in st.session_state:
    query = st.session_state.pop("sample_query")
    st.session_state.pending_query = query

# Chat input
query = st.chat_input("Ask about HR policies...")

if query or st.session_state.get("pending_query"):
    if not query:
        query = st.session_state.pop("pending_query")

    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": query,
        "sources": []
    })

    with st.chat_message("user"):
        st.markdown(query)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Searching HR policies..."):
            result = {}
            try:
                engine = get_rag_engine()
                result = engine.query(query)
                answer = result["answer"]
                sources = result["sources"]
                chunks_used = result["chunks_used"]
            except Exception as e:
                answer = f"Sorry, I encountered an error: {e}"
                sources = []
                chunks_used = 0
                result = {}

        st.markdown(answer)

        if sources:
            st.markdown("**Sources:**")
            for source in sources:
                st.markdown(
                    f'<span class="source-badge">📄 {source}</span>',
                    unsafe_allow_html=True
                )

        # Show metadata
        with st.expander("🔍 Retrieval Details"):
            st.markdown(f"Chunks used: **{chunks_used}**")
            st.markdown(f"Sources: **{len(sources)}**")
            chunks_detail = result.get("chunks", []) if isinstance(result, dict) else []
            for i, chunk in enumerate(chunks_detail[:3]):
                st.markdown(f"**Chunk {i+1}** [{chunk.get('document_id','?')}]")
                st.markdown(f"> {chunk.get('text','')[:150]}...")

    # Save to history
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources
    })
