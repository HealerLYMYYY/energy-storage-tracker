"""
Energy Storage Competitive Intelligence — Goldman-grade Dashboard
"""

import streamlit as st

st.set_page_config(page_title="Energy Storage CI", page_icon="◈", layout="wide",
                   initial_sidebar_state="expanded")

from utils.database import init_db
from utils.auth import init_auth, logout

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

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ——— Root overrides ——— */
* { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }
h1, h2, h3 { font-weight: 600; letter-spacing: -0.01em; }
h1 { font-size: 1.5rem !important; margin-bottom: 0.2rem !important; }
h2 { font-size: 1.15rem !important; }
h3 { font-size: 0.95rem !important; text-transform: uppercase; letter-spacing: 0.05em; color: #8b949e !important; }

/* ——— Metric cards ——— */
[data-testid="stMetric"] { background: #161b22; border: 1px solid #21262d; border-radius: 6px; padding: 14px 18px; }
[data-testid="stMetric"] label { font-size: 0.7rem !important; text-transform: uppercase; letter-spacing: 0.06em; color: #8b949e !important; }
[data-testid="stMetric"] [data-testid="stMetricValue"] { font-size: 1.6rem !important; font-weight: 600; color: #e6edf3; font-family: 'JetBrains Mono', monospace; }

/* ——— Sidebar ——— */
[data-testid="stSidebar"] { background: #0d1117; border-right: 1px solid #21262d; }
[data-testid="stSidebar"] .stButton > button {
    width: 100%; text-align: left; background: transparent; border: none;
    color: #8b949e; font-size: 0.82rem; padding: 8px 14px; border-radius: 4px;
    transition: all 0.15s;
}
[data-testid="stSidebar"] .stButton > button:hover { background: #161b22; color: #c9a96e; }
[data-testid="stSidebar"] .stButton > button:has(div p:contains("▸")) { color: #c9a96e; background: rgba(201,169,110,0.08); }

/* ——— Buttons ——— */
.stButton > button { border-radius: 4px; font-weight: 500; font-size: 0.82rem; letter-spacing: 0.02em; }
.stButton > button[kind="primary"] { background: #c9a96e; color: #0d1117; border: none; }
.stButton > button[kind="primary"]:hover { background: #d4a853; }

/* ——— DataFrames ——— */
[data-testid="stDataFrame"] { font-size: 0.78rem; }
[data-testid="stDataFrame"] th { font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.06em; color: #8b949e; background: #0d1117; border-bottom: 1px solid #21262d; }
[data-testid="stDataFrame"] td { border-bottom: 1px solid #161b22; color: #c9d1d9; font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; }

/* ——— Dividers ——— */
hr { border-color: #21262d !important; margin: 1rem 0 !important; }

/* ——— Inputs ——— */
input, select, textarea { background: #0d1117 !important; border: 1px solid #30363d !important; color: #e6edf3 !important; border-radius: 4px !important; }
input:focus, select:focus { border-color: #c9a96e !important; box-shadow: 0 0 0 2px rgba(201,169,110,0.15) !important; }

/* ——— Tabs ——— */
.stTabs [data-baseweb="tab"] { font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.04em; color: #8b949e; }
.stTabs [aria-selected="true"] { color: #c9a96e !important; border-bottom-color: #c9a96e !important; }

/* ——— Expander ——— */
.streamlit-expanderHeader { font-size: 0.8rem; color: #8b949e; }
</style>
"""


def main():
    init_db()
    init_auth()

    if not st.session_state.authenticated:
        show_login()
        return

    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
    render_sidebar()
    render_content()


def render_sidebar():
    user = st.session_state.user
    role_label = {'admin': 'ADMINISTRATOR', 'editor': 'ANALYST', 'viewer': 'VIEWER'}.get(user['role'], 'VIEWER')

    with st.sidebar:
        # Brand
        st.markdown(f"""
        <div style="padding: 12px 8px 16px 8px; border-bottom: 1px solid #21262d; margin-bottom: 12px;">
            <div style="font-size: 0.95rem; font-weight: 600; color: #e6edf3; letter-spacing: 0.02em;">◈ Energy Storage CI</div>
            <div style="font-size: 0.65rem; color: #8b949e; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 2px;">Competitive Intelligence</div>
        </div>""", unsafe_allow_html=True)

        # User badge
        st.markdown(f"""
        <div style="padding: 10px 12px; background: #161b22; border: 1px solid #21262d; border-radius: 4px; margin-bottom: 14px;">
            <div style="font-size: 0.8rem; font-weight: 500; color: #e6edf3;">{user['display_name']}</div>
            <div style="font-size: 0.62rem; color: #c9a96e; text-transform: uppercase; letter-spacing: 0.08em;">{role_label}</div>
        </div>""", unsafe_allow_html=True)

        # Navigation
        sections = [
            ("ANALYTICS", [
                ("▸ Dashboard", "dashboard"),
                ("  Company View", "company"),
                ("  Peer Comparison", "compare"),
            ]),
            ("MARKET INTELLIGENCE", [
                ("▸ Industry Rankings", "ranking"),
                ("  Macro & Supply Chain", "industry"),
                ("  Sentiment Monitor", "sentiment"),
            ]),
            ("DATA OPERATIONS", [
                ("▸ Data Entry", "data_entry"),
            ]),
        ]
        if user["role"] == "admin":
            sections.append(("ADMINISTRATION", [("▸ Account Management", "accounts")]))

        for section_label, items in sections:
            st.markdown(f'<div style="font-size:0.6rem;color:#484f58;text-transform:uppercase;letter-spacing:0.1em;padding:12px 8px 4px 8px;">{section_label}</div>', unsafe_allow_html=True)
            for label, page in items:
                is_active = st.session_state.get("page", "dashboard") == page
                btn_style = "color:#c9a96e;background:rgba(201,169,110,0.08);" if is_active else ""
                if st.button(label, key=f"nav_{page}", use_container_width=True):
                    st.session_state.page = page
                    st.rerun()

        # Footer
        st.markdown(f"""
        <div style="position:fixed;bottom:16px;left:16px;font-size:0.58rem;color:#30363d;text-transform:uppercase;letter-spacing:0.08em;">
            v2.2 · CONFIDENTIAL
        </div>""", unsafe_allow_html=True)

        st.divider()
        if st.button("Sign Out", use_container_width=True):
            logout()
            st.rerun()


def render_content():
    if "page" not in st.session_state:
        st.session_state.page = "dashboard"
    show_func = PAGE_FUNCTIONS.get(st.session_state.page, show_dashboard)
    show_func()


if __name__ == "__main__":
    main()
