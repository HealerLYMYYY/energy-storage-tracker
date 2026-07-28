"""登录页面"""
import streamlit as st
from utils.auth import authenticate, init_auth


def show_login():
    init_auth()
    if st.session_state.authenticated:
        return

    st.markdown("""
    <style>
    .login-box { max-width:420px; margin:8vh auto 0; }
    .login-box h1 { font-size:1.8rem; font-weight:700; color:#1a1a2e; margin-bottom:0.2rem; text-align:center; }
    </style>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="login-box"><h1>🔋 光储竞对追踪</h1>', unsafe_allow_html=True)
        st.caption("Energy Storage Competitor Intelligence Platform")

        _, col, _ = st.columns([1, 2, 1])
        with col:
            with st.form("login_form"):
                username = st.text_input("用户名", placeholder="请输入用户名")
                password = st.text_input("密码", type="password", placeholder="请输入密码")
                if st.form_submit_button("🔐 登 录", use_container_width=True, type="primary"):
                    if not username or not password:
                        st.error("请输入用户名和密码")
                    else:
                        user = authenticate(username, password)
                        if user:
                            st.session_state.authenticated = True
                            st.session_state.user = user
                            st.rerun()
                        else:
                            st.error("用户名或密码错误")

        st.markdown("""<div style="text-align:center;color:#9ca3af;font-size:0.75rem;margin-top:1rem">
        默认管理员: admin / admin123</div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
