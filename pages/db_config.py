"""数据库配置 — 数据存储方式说明"""

import streamlit as st
from utils.database import export_all_csv, git_commit_and_push
from utils.auth import check_permission


def show_db_config():
    st.markdown('<h1>数据存储配置</h1>', unsafe_allow_html=True)

    if not check_permission("admin"):
        st.error("需要管理员权限")
        return

    # 当前状态
    st.markdown('<h3>当前存储方式：GitHub CSV 持久化</h3>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("数据格式", "CSV 文件")
    with col2:
        st.metric("存储位置", "GitHub 仓库 data/ 目录")

    st.markdown("""
    **工作原理：**
    1. 在「数据录入」页面修改数据后，系统自动将数据导出为 CSV 文件
    2. CSV 文件自动 commit + push 到 GitHub 仓库
    3. Streamlit Cloud 重启时从 CSV 重新加载数据，永不丢失
    4. GitHub 提供完整的历史版本追溯
    """)

    st.divider()

    # 手动同步
    st.markdown('<h3>手动操作</h3>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("导出 CSV", use_container_width=True):
            try:
                export_all_csv()
                st.success("CSV 文件已导出到 data/ 目录")
            except Exception as e:
                st.error(f"导出失败: {e}")
    with col2:
        if st.button("同步到 GitHub", use_container_width=True):
            ok, msg = git_commit_and_push("手动同步")
            if ok:
                st.success(msg)
            else:
                st.error(msg)

    st.divider()

    # 说明
    st.markdown('<h3>本地维护（可选）</h3>', unsafe_allow_html=True)
    st.markdown("""
    你也可以直接在本地编辑 `data/` 目录下的 CSV 文件：
    - `data/competitors.csv` — 竞对公司信息
    - `data/shipment_data.csv` — 出货量数据
    - `data/cost_data.csv` — 成本数据
    - `data/financial_data.csv` — 财务数据
    - `data/industry_data.csv` — 行业数据
    - `data/ranking_data.csv` — 排名数据

    编辑后用 GitHub 推送即可。
    """)
