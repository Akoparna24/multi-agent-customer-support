import streamlit as st
import streamlit_authenticator as stauth
from src.escalation import get_escalated_tickets, resolve_ticket

st.set_page_config(
    page_title="Staff Panel",
    page_icon="🔧",
    layout="wide"
)

# ── Authentication ────────────────────────────────────────────────────────────
credentials = {
    "usernames": {
        "demo": {
            "name":     "Demo Staff",
            "password": stauth.Hasher.hash("demo123")
        },
        "admin": {
            "name":     "Admin",
            "password": stauth.Hasher.hash("admin123")
        }
    }
}

authenticator = stauth.Authenticate(
    credentials=credentials,
    cookie_name="support_staff",
    cookie_key="abc123xyz",
    cookie_expiry_days=1
)

authenticator.login(location="main")

if st.session_state["authentication_status"] is None:
    st.info("👆 Please enter your staff credentials to continue.")
    st.markdown("---")
    st.markdown("**Demo credentials:**")
    st.markdown("- Username: `demo` | Password: `demo123`")
    st.stop()

if st.session_state["authentication_status"] is False:
    st.error("Incorrect username or password.")
    st.markdown("**Demo credentials:**")
    st.markdown("- Username: `demo` | Password: `demo123`")
    st.stop()

# ── Staff Panel — only visible after login ────────────────────────────────────
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🔧 Staff Panel — Escalated Tickets")
with col2:
    authenticator.logout(location="main")

st.caption(f"Logged in as: **{st.session_state['name']}**")
st.divider()

if st.button("🔄 Refresh"):
    st.rerun()

pending = get_escalated_tickets()

if not pending:
    st.success("✅ No pending escalated tickets!")
else:
    st.markdown(f"**{len(pending)} pending ticket(s)**")
    st.divider()

    for t in pending:
        with st.container():
            col1, col2 = st.columns([4, 1])

            with col1:
                st.markdown(f"### 🎫 Ticket ID: `{t['id']}`")
                st.markdown(f"**Domain:** {t['domain'].capitalize()}")
                st.markdown(f"**Customer message:** {t['ticket']}")
                st.markdown(f"**Reason escalated:** {t['reason']}")
                st.markdown(f"**Time:** {t['timestamp']}")

            with col2:
                st.write("")
                st.write("")
                if st.button("✅ Resolve", key=f"resolve_{t['id']}"):
                    resolve_ticket(t["id"])
                    st.success("Resolved!")
                    st.rerun()

            st.divider()