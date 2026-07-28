"""
光储行业竞对量本利追踪系统 - 主入口
"""

import streamlit as st

st.set_page_config(page_title="光储竞对追踪", page_icon="🔋", layout="wide",
                   initial_sidebar_state="expanded")

from utils.database import init_db
from utils.auth import init_auth, logout

# 顶部导入所有页面函数（避免动态导入在云端失败）
from pages.login import show_login
from pages.dashboard import show_dashboard
from pages.company import show_company
from pages.compare import show_compare
from pages.ranking import show_ranking
from pages.industry import show_industry
from pages.sentiment import show_sentiment
from pages.data_entry import show_data_entry
from pages.accounts import show_accounts


PAGE_FUNCTIONS = {
    "dashboard": show_dashboard,
    "company": show_company,
    "compare": show_compare,
    "ranking": show_ranking,
    "industry": show_industry,
    "sentiment": show_sentiment,
    "data_entry": show_data_entry,
    "accounts": show_accounts,
}


def main():
    init_db()
    init_auth()

    if not st.session_state.authenticated:
        show_login()
        return

    render_sidebar()
    render_content()


def render_sidebar():
    user = st.session_state.user
    with st.sidebar:
        st.markdown("""
        <div style="padding:0.5rem 0 1rem 0">
            <h2 style="margin:0;font-size:1.1rem">🔋 光储竞对追踪</h2>
            <p style="margin:0;color:#6b7280;font-size:0.75rem">Energy Storage Competitor Intel</p>
        </div>""", unsafe_allow_html=True)
        st.divider()

        st.markdown(f"""
        <div style="padding:0.5rem;background:#f8fafc;border-radius:8px;margin-bottom:0.5rem">
            <div style="font-weight:600;font-size:0.85rem">👤 {user['display_name']}</div>
            <div style="font-size:0.7rem;color:#6b7280">
                角色: {'管理员' if user['role']=='admin' else '编辑者' if user['role']=='editor' else '查看者'}
            </div>
        </div>""", unsafe_allow_html=True)
        st.divider()

        nav_items = [
            ("📊", "Dashboard", "dashboard", "仪表盘总览"),
            ("🏢", "企业详情", "company", "企业详情"),
            ("📈", "对比分析", "compare", "对比分析"),
            ("🏆", "行业排名", "ranking", "行业排名"),
            ("🌐", "行业数据", "industry", "行业数据"),
            ("📰", "舆情监控", "sentiment", "舆情监控"),
            ("📝", "数据录入", "data_entry", "数据录入"),
        ]
        if user["role"] == "admin":
            nav_items.append(("👥", "账户管理", "accounts", "账户管理"))

        for icon, label, page, _ in nav_items:
            if st.button(f"{icon} {label}", use_container_width=True,
                         key=f"nav_{page}",
                         help=f"切换到{label}"):
                st.session_state.page = page
                st.rerun()

        st.divider()
        if st.button("🚪 退出登录", use_container_width=True):
            logout()
            st.rerun()

        st.markdown("""<div style="font-size:0.65rem;color:#9ca3af;margin-top:1rem">v2.1 · 光储行业专用</div>""",
                    unsafe_allow_html=True)


def render_content():
    if "page" not in st.session_state:
        st.session_state.page = "dashboard"
    page = st.session_state.page
    show_func = PAGE_FUNCTIONS.get(page, show_dashboard)
    show_func()


if __name__ == "__main__":
    main()
