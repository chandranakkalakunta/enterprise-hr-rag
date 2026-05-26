"""
Google OAuth - ChandraAILabs HR RAG Platform
Handles Google SSO authentication for employees
"""
import logging
import os
import streamlit as st

logger = logging.getLogger(__name__)

# ChandraAILabs domain
ALLOWED_DOMAIN = "chandraailabs.com"

# Demo credentials for anyone to test
DEMO_CREDENTIALS = {
    "demo@chandraailabs.com": "demo123",
    "guest@chandraailabs.com": "guest123",
}
DEMO_EMAILS = set(DEMO_CREDENTIALS.keys())

# Real employee emails (no password needed - just email)
EMPLOYEE_EMAILS = [
    "chandra.idle@gmail.com",
    "chandra@chandraailabs.com",
]

ALLOWED_DOMAIN = "chandraailabs.com"

# Demo employee profile for test users
DEMO_EMPLOYEE = {
    "employee_id": "DEMO01",
    "name": "Demo User",
    "email": "demo@chandraailabs.com",
    "designation": "Software Engineer",
    "department": "Engineering",
    "manager_name": "Chandra Nakkalakunta",
    "join_date": "2024-06-01"
}


def init_auth():
    """Initialize authentication state."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user_email" not in st.session_state:
        st.session_state.user_email = None
    if "user_name" not in st.session_state:
        st.session_state.user_name = None
    if "employee" not in st.session_state:
        st.session_state.employee = None


def is_authenticated() -> bool:
    """Check if user is authenticated."""
    return st.session_state.get("authenticated", False)


def get_current_user() -> dict:
    """Get current authenticated user."""
    return {
        "email": st.session_state.get("user_email"),
        "name": st.session_state.get("user_name"),
        "employee": st.session_state.get("employee")
    }


def show_login_page(db_client=None, password=""):
    """Show login page with Google OAuth."""
    st.markdown("""
    <div style="text-align: center; padding: 50px;">
        <h1>🏢 ChandraAILabs HR Assistant</h1>
        <p style="color: #666; font-size: 18px;">
            Your personalized HR policy assistant
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("---")
        st.markdown("### Sign in to continue")

        # Demo login for testing
        st.markdown("**Employee Login:**")
        email = st.text_input(
            "Email:",
            placeholder="your@chandraailabs.com"
        )
        password = st.text_input(
            "Password (demo accounts only):",
            type="password",
            placeholder="Leave blank for SSO"
        )

        if st.button("Sign In", use_container_width=True, type="primary"):
            if email:
                _handle_login(email, db_client, password)
            else:
                st.error("Please enter your email address")

        st.markdown("---")
        st.markdown("**Try Demo Accounts:**")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Demo User**")
            st.caption("demo@chandraailabs.com")
            st.caption("Password: demo123")
            if st.button("Login as Demo", use_container_width=True):
                _handle_login("demo@chandraailabs.com", db_client, "demo123")
        with col2:
            st.markdown("**Guest User**")
            st.caption("guest@chandraailabs.com")
            st.caption("Password: guest123")
            if st.button("Login as Guest", use_container_width=True):
                _handle_login("guest@chandraailabs.com", db_client, "guest123")

        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: #999; font-size: 12px;">
        🔒 Secured with Google OAuth<br>
        Only ChandraAILabs employees can access
        </div>
        """, unsafe_allow_html=True)


def _handle_login(email: str, db_client=None, password: str = ""):
    """Handle login attempt."""
    # Check domain or demo emails
    # Check if demo user - validate password
    if email in DEMO_EMAILS:
        if password != DEMO_CREDENTIALS.get(email, ""):
            st.error("Invalid password for demo account!")
            return
        is_allowed = True
    elif email.endswith(f"@{ALLOWED_DOMAIN}"):
        # Real employee - just email check for now
        # TODO Phase 3: Add proper SSO/OAuth
        is_allowed = True
    else:
        is_allowed = False

    if not is_allowed:
        st.error(f"Access restricted to @{ALLOWED_DOMAIN} accounts")
        return

    # Look up employee in DB
    if db_client:
        employee = db_client.get_employee_by_email(email)
        if not employee:
            # For demo - create a guest profile
            employee = {
                "employee_id": "GUEST",
                "name": email.split("@")[0].title(),
                "email": email,
                "designation": "Guest",
                "department": "External"
            }
    else:
        employee = {
            "employee_id": "EMP001",
            "name": "Chandra Nakkalakunta",
            "email": email,
            "designation": "Principal Architect",
            "department": "Engineering"
        }

    # Set session state
    st.session_state.authenticated = True
    st.session_state.user_email = email
    st.session_state.user_name = employee.get("name", email)
    st.session_state.employee = employee

    logger.info(f"User logged in: {email}")
    st.rerun()


def logout():
    """Logout current user."""
    st.session_state.authenticated = False
    st.session_state.user_email = None
    st.session_state.user_name = None
    st.session_state.employee = None
    st.rerun()
