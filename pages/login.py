"""Login — Institutional Grade"""

import streamlit as st
from utils.auth import authenticate, init_auth


def show_login():
    init_auth()
    if st.session_state.authenticated:
        return

    st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { display: flex; align-items: center; justify-content: center; }
    .login-card { max-width: 380px; margin: 12vh auto 0; }
    </style>""", unsafe_allow_html=True)

    st.markdown("""
    <div class="login-card">
        <div style="text-align:center;margin-bottom:28px;">
            <div style="font-size:2rem;color:#c9a96e;margin-bottom:4px;">◈</div>
            <div style="font-size:1.1rem;font-weight:600;color:#e6edf3;letter-spacing:0.03em;">Energy Storage CI</div>
            <div style="font-size:0.65rem;color:#8b949e;text-transform:uppercase;letter-spacing:0.1em;margin-top:4px;">Competitive Intelligence Platform</div>
        </div>
    </div>""", unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")

            if submitted:
                if not username or not password:
                    st.error("Please enter credentials")
                else:
                    user = authenticate(username, password)
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.user = user
                        st.rerun()
                    else:
                        st.error("Invalid credentials")

    st.markdown("""<div style="text-align:center;font-size:0.6rem;color:#30363d;margin-top:24px;text-transform:uppercase;letter-spacing:0.08em;">
    Authorized Personnel Only · Default: admin / admin123</div>""", unsafe_allow_html=True)
