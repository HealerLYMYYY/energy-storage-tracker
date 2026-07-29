"""
光储竞争情报系统 - 机构级仪表盘
"""

import streamlit as st

st.set_page_config(page_title="光储竞争情报", page_icon="*", layout="wide",
                   initial_sidebar_state="expanded")

from utils.database import init_db, PG_AVAILABLE, PG_ERROR_MSG, USE_PG
from utils.auth import init_auth, logout

from pages.login import show_login
from pages.dashboard import show_dashboard
from pages.company import show_company
from pages.compare import show_compare
from pages.ranking import show_ranking
from pages.industry import show_industry
from pages.data_entry import show_data_entry
from pages.accounts import show_accounts
from pages.db_config import show_db_config

PAGE_FUNCTIONS = {
    "dashboard": show_dashboard,
    "company": show_company,
    "compare": show_compare,
    "ranking": show_ranking,
    "industry": show_industry,
    "data_entry": show_data_entry,
    "accounts": show_accounts,
    "db_config": show_db_config,
}

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ===== 品牌色系: 主橙 #C9702A (克制琥珀) | 辅助 雾蓝#5A7A96 灰绿#7A9B76 雾紫#8B7DA8 暗红#B85C5C ===== */

/* 根样式 */
* { font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif; }
h1, h2, h3 { font-weight: 600; letter-spacing: -0.01em; }
h1 { font-size: 1.5rem !important; margin-bottom: 0.2rem !important; color: #ECECEC !important; }
h2 { font-size: 1.15rem !important; }
h3 { font-size: 0.95rem !important; text-transform: uppercase; letter-spacing: 0.05em; color: #9a9a9a !important; }

/* 指标卡 */
[data-testid="stMetric"] { background: #1a1e23; border: 1px solid #2a2f36; border-radius: 6px; padding: 14px 18px; }
[data-testid="stMetric"] label { font-size: 0.7rem !important; text-transform: uppercase; letter-spacing: 0.06em; color: #9a9a9a !important; }
[data-testid="stMetric"] [data-testid="stMetricValue"] { font-size: 1.6rem !important; font-weight: 600; color: #ECECEC; font-family: 'JetBrains Mono', monospace; }

/* 侧边栏 */
[data-testid="stSidebar"] { background: #111417; border-right: 1px solid #2a2f36; }
[data-testid="stSidebar"] .stButton > button {
    width: 100%; text-align: left; background: transparent; border: none;
    color: #9a9a9a; font-size: 0.82rem; padding: 8px 14px; border-radius: 4px;
    transition: all 0.15s;
}
[data-testid="stSidebar"] .stButton > button:hover { background: #1a1e23; color: #C9702A; }
[data-testid="stSidebar"] .stButton > button:has(div p:contains(">")) { color: #C9702A; background: rgba(201,112,42,0.08); }

/* 按钮 */
.stButton > button { border-radius: 4px; font-weight: 500; font-size: 0.82rem; letter-spacing: 0.02em; }
.stButton > button[kind="primary"] { background: #C9702A; color: #FFFFFF; border: none; }
.stButton > button[kind="primary"]:hover { background: #b06325; }
.stButton > button[kind="secondary"] { background: #1a1e23; color: #9a9a9a; border: 1px solid #2a2f36; }
.stButton > button[kind="secondary"]:hover { border-color: #C9702A; color: #C9702A; }

/* 数据表 */
[data-testid="stDataFrame"] { font-size: 0.78rem; }
[data-testid="stDataFrame"] th { font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.06em; color: #9a9a9a; background: #111417; border-bottom: 1px solid #2a2f36; }
[data-testid="stDataFrame"] td { border-bottom: 1px solid #1a1e23; color: #d5d5d5; font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; }

/* 分隔线 */
hr { border-color: #2a2f36 !important; margin: 1rem 0 !important; }

/* 输入框 */
input, select, textarea { background: #111417 !important; border: 1px solid #3a4048 !important; color: #ECECEC !important; border-radius: 4px !important; }
input:focus, select:focus { border-color: #C9702A !important; box-shadow: 0 0 0 2px rgba(201,112,42,0.15) !important; }

/* 标签页 */
.stTabs [data-baseweb="tab"] { font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.04em; color: #9a9a9a; }
.stTabs [aria-selected="true"] { color: #C9702A !important; border-bottom-color: #C9702A !important; }

/* 展开器 */
.streamlit-expanderHeader { font-size: 0.8rem; color: #9a9a9a; }

/* 提示框 */
[data-testid="stAlert"] { background: #1a1e23; border: 1px solid #2a2f36; border-radius: 6px; }
</style>
"""


def main():
    try:
        init_db()
    except Exception as e:
        st.error(f"数据库初始化失败: {e}")
        return

    init_auth()

    if not st.session_state.authenticated:
        show_login()
        return

    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

    # 数据库状态提示
    if not PG_AVAILABLE and USE_PG:
        st.warning(f"注意：PostgreSQL 连接失败，已自动降级到本地 SQLite。数据不会跨设备同步。\n\n> 错误：`{PG_ERROR_MSG}`")
    elif not USE_PG:
        st.info("提示：未配置 DATABASE_URL 或连接失败，使用本地 SQLite。配置正确的 Supabase 后可实现数据持久化和多设备同步。")

    render_sidebar()
    render_content()


def render_sidebar():
    user = st.session_state.user
    role_label = {'admin': '管理员', 'editor': '分析师', 'viewer': '访客'}.get(user['role'], '访客')

    with st.sidebar:
        # 品牌
        st.markdown(f"""
        <div style="padding: 12px 8px 16px 8px; border-bottom: 1px solid #2a2f36; margin-bottom: 12px;">
            <div style="font-size: 0.95rem; font-weight: 600; color: #ECECEC; letter-spacing: 0.02em;">
                <span style="color:#C9702A;">■</span> 光储竞争情报</div>
            <div style="font-size: 0.65rem; color: #9a9a9a; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 2px;">Competitive Intelligence</div>
        </div>""", unsafe_allow_html=True)

        # 用户徽章
        st.markdown(f"""
        <div style="padding: 10px 12px; background: #1a1e23; border: 1px solid #2a2f36; border-radius: 4px; margin-bottom: 14px;">
            <div style="font-size: 0.8rem; font-weight: 500; color: #ECECEC;">{user['display_name']}</div>
            <div style="font-size: 0.62rem; color: #C9702A; text-transform: uppercase; letter-spacing: 0.08em;">{role_label}</div>
        </div>""", unsafe_allow_html=True)

        # 导航
        sections = [
            ("分析", [
                ("> 仪表盘", "dashboard"),
                ("  公司视图", "company"),
                ("  同业对比", "compare"),
            ]),
            ("市场情报", [
                ("> 行业排名", "ranking"),
                ("  宏观与产业链", "industry"),
            ]),
            ("数据操作", [
                ("> 数据录入", "data_entry"),
            ]),
        ]
        if user["role"] == "admin":
            sections.append(("管理", [("> 账户管理", "accounts"), ("> 数据库配置", "db_config")]))

        for section_label, items in sections:
            st.markdown(f'<div style="font-size:0.6rem;color:#606060;text-transform:uppercase;letter-spacing:0.1em;padding:12px 8px 4px 8px;">{section_label}</div>', unsafe_allow_html=True)
            for label, page in items:
                is_active = st.session_state.get("page", "dashboard") == page
                if st.button(label, key=f"nav_{page}", use_container_width=True):
                    st.session_state.page = page
                    st.rerun()

        # 底部
        st.markdown(f"""
        <div style="position:fixed;bottom:16px;left:16px;font-size:0.58rem;color:#3a4048;text-transform:uppercase;letter-spacing:0.08em;">
            v3.1 | 2026E | 内部资料
        </div>""", unsafe_allow_html=True)

        st.divider()
        if st.button("退出登录", use_container_width=True):
            logout()
            st.rerun()


def render_content():
    if "page" not in st.session_state:
        st.session_state.page = "dashboard"
    show_func = PAGE_FUNCTIONS.get(st.session_state.page, show_dashboard)
    show_func()


if __name__ == "__main__":
    main()
