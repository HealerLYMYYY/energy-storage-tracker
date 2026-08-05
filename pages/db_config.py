"""数据库配置 — 在线配置 Supabase 连接"""

import streamlit as st
import os
from utils.database import _test_pg_connection, _fix_pg_url, USE_PG, PG_AVAILABLE, PG_ERROR_MSG, get_database_url, reinit_db
from utils.auth import check_permission


def show_db_config():
    st.markdown('<h1>数据库配置</h1>', unsafe_allow_html=True)

    if not check_permission("admin"):
        st.error("需要管理员权限")
        return

    # 当前状态
    st.markdown('<h3>当前状态</h3>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        status = "已连接" if PG_AVAILABLE else "未连接"
        st.metric("PostgreSQL", status)
    with col2:
        mode = "PostgreSQL" if USE_PG else "SQLite"
        st.metric("运行模式", mode)
    with col3:
        db_url = get_database_url()
        url_display = db_url[:50] + "..." if len(db_url) > 50 else db_url or "未配置"
        st.metric("连接字符串", url_display)

    if PG_ERROR_MSG:
        st.error(f"连接错误: {PG_ERROR_MSG}")

    st.divider()

    # 配置表单
    st.markdown('<h3>配置 Supabase 连接</h3>', unsafe_allow_html=True)
    st.markdown("""
    从 Supabase 后台获取连接字符串：
    1. 登录 [supabase.com/dashboard](https://supabase.com/dashboard)
    2. 选择你的项目 → Settings → Database
    3. 复制 Connection string（格式：`postgresql://postgres:密码@db.xxx.supabase.co:5432/postgres`）
    """)

    with st.form("db_config_form"):
        new_url = st.text_input(
            "DATABASE_URL",
            value=get_database_url(),
            type="password",
            help="格式：postgresql://postgres:密码@db.xxx.supabase.co:5432/postgres"
        )
        col1, col2 = st.columns(2)
        with col1:
            test_btn = st.form_submit_button("测试连接", use_container_width=True)
        with col2:
            save_btn = st.form_submit_button("保存配置", use_container_width=True, type="primary")

        if test_btn and new_url:
            with st.spinner("正在测试连接..."):
                fixed_url = _fix_pg_url(new_url)
                ok, err = _test_pg_connection(fixed_url, timeout=10)
                if ok:
                    st.success("连接成功！可以点击保存配置")
                    st.code(fixed_url, language="text")
                else:
                    st.error(f"连接失败: {err}")
                    st.markdown("""
                    **常见错误排查：**
                    - 密码是否正确？（不要带方括号 `[]`）
                    - 是否加了 `?sslmode=require`？
                    - Supabase 项目是否已暂停？
                    """)

        if save_btn and new_url:
            # 保存到环境变量
            os.environ["DATABASE_URL"] = new_url
            # 重新初始化数据库连接
            with st.spinner("正在重新连接数据库..."):
                use_pg, pg_ok, pg_err = reinit_db()
                if use_pg and pg_ok:
                    st.success("已切换至 PostgreSQL 模式！数据将持久化保存到 Supabase。")
                elif pg_err:
                    st.warning(f"PostgreSQL 连接失败 ({pg_err})，已降级至 SQLite 模式。请检查连接字符串。")
                else:
                    st.info("已使用 SQLite 模式。")

    st.divider()

    # 快速配置
    st.markdown('<h3>快速配置</h3>', unsafe_allow_html=True)
    st.markdown("如果你使用的是 Supabase 项目 `hkeigpktrtptgtjvhwyt`，可以直接使用以下模板：")

    quick_url = st.text_input(
        "快速配置",
        value="postgresql://postgres:Liyanming19921210@db.hkeigpktrtptgtjvhwyt.supabase.co:5432/postgres",
        help="点击上方测试连接验证"
    )

    if st.button("使用此配置", use_container_width=True):
        os.environ["DATABASE_URL"] = quick_url
        with st.spinner("正在重新连接数据库..."):
            use_pg, pg_ok, pg_err = reinit_db()
            if use_pg and pg_ok:
                st.success("已切换至 PostgreSQL 模式！")
            elif pg_err:
                st.warning(f"PostgreSQL 连接失败 ({pg_err})，已降级至 SQLite 模式。")
            else:
                st.info("已使用 SQLite 模式。")

    st.divider()

    # 手动配置指南
    with st.expander("手动配置 Streamlit Cloud Secrets（永久生效）"):
        db_url = get_database_url()
        secret_url = db_url or "postgresql://postgres:你的密码@db.hkeigpktrtptgtjvhwyt.supabase.co:5432/postgres?sslmode=require"
        st.markdown(f"""
        1. 打开 [share.streamlit.io](https://share.streamlit.io)
        2. 找到你的应用 → 右下角 **⋮** → **Settings** → **Secrets**
        3. 粘贴以下内容：

        ```toml
        DATABASE_URL = "{secret_url}"
        ```

        4. 保存后应用会自动重新部署
        """)
