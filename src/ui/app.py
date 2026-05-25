"""
Streamlit UI - ChandraAILabs HR RAG Platform
Employee-facing chat with Google OAuth + Personal RAG
"""
import streamlit as st
import os
import sys
import logging

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../generation"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../retrieval"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../ingestion"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../database"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../auth"))

logging.basicConfig(level=logging.WARNING)

st.set_page_config(
    page_title="ChandraAILabs HR Assistant",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    .personal-badge {
        background: #E8F8E8;
        border: 1px solid #1E6B3C;
        border-radius: 5px;
        padding: 3px 8px;
        font-size: 12px;
        color: #1E6B3C;
        margin: 2px;
        display: inline-block;
    }
    .user-info {
        background: #F0F7FF;
        border-radius: 8px;
        padding: 10px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ── Initialize Auth ────────────────────────────────────────
from google_oauth import init_auth, is_authenticated, show_login_page, logout, get_current_user
init_auth()

# ── Initialize DB ──────────────────────────────────────────
@st.cache_resource(show_spinner="Connecting to HR Database...")
def get_db_client():
    try:
        from hr_db_client import HRDBClient
        return HRDBClient(
            project_id=os.environ.get("PROJECT_ID", "hr-rag-dev"),
            instance_name=os.environ.get("DB_INSTANCE_NAME", "hr-rag-db"),
            db_name=os.environ.get("DB_NAME", "hr_db"),
            db_user=os.environ.get("DB_USER", "hr_admin"),
            db_password=os.environ.get("DB_PASSWORD", "ChandraAILabs2024!"),
            region=os.environ.get("REGION", "asia-south1")
        )
    except Exception as e:
        st.warning(f"HR Database not available: {e}")
        return None

# ── Initialize RAG Engine ──────────────────────────────────
@st.cache_resource(show_spinner="Initializing HR Assistant...")
def get_rag_engine():
    from rag_engine import RAGEngine
    api_key = os.environ.get("GEMINI_API_KEY", "")
    project_id = os.environ.get("PROJECT_ID", "hr-rag-dev")
    environment = os.environ.get("ENVIRONMENT", "dev")
    return RAGEngine(
        project_id=project_id,
        gemini_api_key=api_key,
        environment=environment
    )

@st.cache_resource(show_spinner="Initializing Personal Assistant...")
def get_personal_rag():
    try:
        from personal_rag import PersonalRAG
        api_key = os.environ.get("GEMINI_API_KEY", "")
        project_id = os.environ.get("PROJECT_ID", "hr-rag-dev")
        return PersonalRAG(
            project_id=project_id,
            gemini_api_key=api_key
        )
    except Exception as e:
        st.warning(f"Personal RAG not available: {e}")
        return None

# ── Show Login if not authenticated ───────────────────────
if not is_authenticated():
    db = get_db_client()
    show_login_page(db_client=db)
    st.stop()

# ── Main App (authenticated) ───────────────────────────────
user = get_current_user()
employee = user.get("employee", {})
user_name = user.get("name", "Employee")
first_name = user_name.split()[0] if user_name else "there"

# ── Header ─────────────────────────────────────────────────
st.markdown(f"""
<div class="main-header">
    <h1>🏢 ChandraAILabs HR Assistant</h1>
    <p>Welcome back, {first_name}! How can I help you today?</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────
with st.sidebar:
    # User profile
    st.markdown(f"""
    <div class="user-info">
        <b>👤 {user_name}</b><br>
        <small>{employee.get("designation", "")}</small><br>
        <small>{employee.get("department", "")} | {employee.get("employee_id", "")}</small>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Sign Out", use_container_width=True):
        logout()

    st.divider()

    st.markdown("### 💬 Try asking:")
    personal_questions = [
        "How many leaves do I have?",
        "What is my performance rating?",
        "What is my CTC?",
        "Who is my manager?",
    ]
    policy_questions = [
        "What is the WFH policy?",
        "How do I apply for leave?",
        "What is the PIP process?",
        "What certifications are supported?",
    ]

    st.markdown("**Personal queries:**")
    for q in personal_questions:
        if st.button(q, key=f"p_{q}", use_container_width=True):
            st.session_state.pending_query = q

    st.markdown("**Policy queries:**")
    for q in policy_questions:
        if st.button(q, key=f"pol_{q}", use_container_width=True):
            st.session_state.pending_query = q

    st.divider()
    st.markdown("### 📚 Available Policies")
    policies = [
        "📅 Leave Policy",
        "🚀 Onboarding",
        "✅ Code of Conduct",
        "🏠 Remote Work",
        "⭐ Performance",
        "💰 Compensation",
        "✈️ Travel & Expense",
        "📖 Training",
        "🤝 Grievance",
        "🔒 IT Security"
    ]
    for p in policies:
        st.markdown(f"- {p}")

# ── Chat Interface ─────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": f"Hello {first_name}! I am your personal HR assistant. I can answer questions about HR policies AND your personal HR data like leave balance, performance rating, and more!",
        "sources": [],
        "intent": "greeting"
    }]

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            for source in message["sources"]:
                badge_class = "personal-badge" if source == "HR Database" else "source-badge"
                icon = "👤" if source == "HR Database" else "📄"
                st.markdown(
                    f'<span class="{badge_class}">{icon} {source}</span>',
                    unsafe_allow_html=True
                )

# Handle pending query
query = st.chat_input(f"Ask me anything, {first_name}...")

if not query and "pending_query" in st.session_state:
    query = st.session_state.pop("pending_query")

if query:
    st.session_state.messages.append({
        "role": "user",
        "content": query,
        "sources": []
    })

    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Searching HR policies..."):
            try:
                from query_router import QueryRouter
                router = QueryRouter()
                intent = router.detect_intent(query)
            except Exception as e:
                intent = "policy"

        sources = []
        intent_label = intent
        answer = ""

        try:
            if intent in ["personal", "hybrid"]:
                personal_rag = get_personal_rag()
                if personal_rag and employee.get("email"):
                    rag_engine = get_rag_engine() if intent == "hybrid" else None
                    result = personal_rag.query(
                        question=query,
                        employee_email=employee.get("email", ""),
                        policy_rag_engine=rag_engine
                    )
                    answer = result.get("answer", "")
                    sources = result.get("sources", [])
                    intent_label = result.get("intent", "personal")
                    st.markdown(answer)
                else:
                    engine = get_rag_engine()
                    answer_placeholder = st.empty()
                    full_answer = ""
                    for chunk in engine.query_stream(query):
                        full_answer += chunk
                        answer_placeholder.markdown(full_answer + "▌")
                    answer_placeholder.markdown(full_answer)
                    answer = full_answer
                    sources = ["HR Policies"]
            else:
                engine = get_rag_engine()
                answer_placeholder = st.empty()
                full_answer = ""
                for chunk in engine.query_stream(query):
                    full_answer += chunk
                    answer_placeholder.markdown(full_answer + "▌")
                answer_placeholder.markdown(full_answer)
                answer = full_answer
                sources = ["HR Policies"]

        except Exception as e:
            answer = "Sorry, I encountered an error. Please try again."
            sources = []
            intent_label = "error"
            st.markdown(answer)

        if sources:
            for source in sources:
                badge_class = "personal-badge" if source == "HR Database" else "source-badge"
                icon = "👤" if source == "HR Database" else "📄"
                st.markdown(
                    f'<span class="{badge_class}">{icon} {source}</span>',
                    unsafe_allow_html=True
                )

        # Show intent badge
        intent_colors = {
            "personal": "🟢 Personal Query",
            "hybrid": "🔵 Hybrid Query",
            "policy": "📋 Policy Query"
        }
        st.caption(intent_colors.get(intent_label, "📋 Policy Query"))

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
        "intent": intent_label
    })
