"""企业详情页 - 量本利分析 + 舆情"""
import streamlit as st
import pandas as pd
from utils.data_manager import get_competitors, get_shipment, get_cost, get_financial
from utils.visualization import company_trend_chart, ship_stack_chart, cost_price_chart, qtr_bar_chart


def show_company():
    competitors = get_competitors()
    comp_names = {c["name"]: c for c in competitors}

    if "selected_company" not in st.session_state:
        st.session_state.selected_company = competitors[0]["name"]

    # 公司选择器
    cols = st.columns(9)
    for i, c in enumerate(competitors):
        with cols[i]:
            if st.button(c["name"], key=f"comp_{c['cid']}",
                         use_container_width=True,
                         type="primary" if c["name"] == st.session_state.selected_company else "secondary",
                         help=c["ticker"]):
                st.session_state.selected_company = c["name"]
                st.rerun()

    comp = comp_names[st.session_state.selected_company]
    cid = comp["cid"]

    ship_data = get_shipment(cid)
    cost_data = get_cost(cid)
    fin_data = get_financial(cid)
    periods = ["2022", "2023", "2024", "2025"]

    st.divider()

    # 头部信息
    s25 = ship_data.get("2025", {})
    co25 = cost_data.get("2025", {})
    f25 = fin_data.get("2025", {})

    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:16px;margin-bottom:20px">
        <div style="width:48px;height:48px;border-radius:12px;background:{comp['color']};display:flex;align-items:center;justify-content:center;color:white;font-size:1.2rem;font-weight:700">{comp['name'][0]}</div>
        <div>
            <h2 style="margin:0">{comp['name']} <span style="font-size:0.8rem;color:#6b7280">{comp['ticker']}</span></h2>
            <p style="margin:0;color:#6b7280;font-size:0.85rem">{comp['company_type']} | 2025出货 {s25.get('total','-'):.1f} GWh | 营收 {f25.get('revenue','-'):.1f} 亿元</p>
        </div>
    </div>""", unsafe_allow_html=True)

    # KPI 卡片
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("出货量 (2025)", f"{s25.get('total','-'):.1f} GWh")
    with k2:
        st.metric("国内毛利率", f"{co25.get('domestic_margin','-'):.1f}%" if co25.get("domestic_margin") else "N/A")
    with k3:
        st.metric("海外毛利率", f"{co25.get('export_margin','-'):.1f}%" if co25.get("export_margin") else "N/A")
    with k4:
        st.metric("净利润", f"{f25.get('net_profit','-'):.1f} 亿" if f25.get("net_profit") is not None else "N/A")

    st.divider()

    # 标签页
    tab1, tab2, tab3 = st.tabs(["📊 量本利分析", "📰 舆情监控", "📋 数据明细"])

    with tab1:
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("出货量趋势")
            fig = company_trend_chart(ship_data, periods, comp["color"], "出货量(GWh)", "total")
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("出货量拆分")
            # 地域拆分
            dom = [ship_data.get(y, {}).get("domestic", 0) or 0 for y in periods]
            exp = [ship_data.get(y, {}).get("export", 0) or 0 for y in periods]
            import plotly.graph_objects as go
            fig2 = go.Figure(data=[
                go.Bar(name="国内", x=periods, y=dom, marker_color="rgba(255,123,0,0.7)"),
                go.Bar(name="海外", x=periods, y=exp, marker_color="rgba(84,184,107,0.7)")
            ])
            fig2.update_layout(barmode="stack", margin=dict(l=20, r=20, t=10, b=20),
                               plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig2, use_container_width=True)

        with col_b:
            st.subheader("成本-单价-毛利")
            fig3 = cost_price_chart(cost_data, periods, comp["color"])
            st.plotly_chart(fig3, use_container_width=True)

            st.subheader("Q1-Q4 营收拆分")
            fig4 = qtr_bar_chart([comp], {cid: fin_data}, "rv", "2025")
            st.plotly_chart(fig4, use_container_width=True)

    with tab2:
        st.subheader(f"🔍 {comp['name']} · 舆情监控")
        st.markdown(f"**监控关键词**: {comp['keywords']}")

        col_l, col_m, col_r = st.columns(3)
        with col_l:
            st.link_button("🔗 Google News", f"https://news.google.com/search?q={comp['name']}+储能&hl=zh-CN",
                           use_container_width=True)
        with col_m:
            st.link_button("🔗 百度搜索", f"https://www.baidu.com/s?wd={comp['name']}+储能",
                           use_container_width=True)
        with col_r:
            st.link_button("🔗 东方财富", f"https://so.eastmoney.com/news/s?keyword={comp['name']}",
                           use_container_width=True)

        st.info("💡 点击上方链接跳转到外部搜索页面获取最新舆情数据。如需内置舆情聚合，需要配置新闻 API。")

    with tab3:
        st.subheader("财务数据明细")

        # 出货量表
        st.markdown("**出货量 (GWh)**")
        ship_rows = []
        for y in periods:
            d = ship_data.get(y, {})
            ship_rows.append({
                "年度": y, "总出货": d.get("total"), "国内": d.get("domestic"),
                "海外": d.get("export"), "户用储能": d.get("residential"),
                "大储": d.get("utility"), "工商业储能": d.get("commercial")
            })
        st.dataframe(pd.DataFrame(ship_rows), use_container_width=True, hide_index=True)

        # 成本表
        st.markdown("**成本与单价 (¥/Wh)**")
        cost_rows = []
        for y in periods:
            d = cost_data.get(y, {})
            cost_rows.append({
                "年度": y, "系统成本": d.get("system_cost"), "国内单价": d.get("domestic_price"),
                "国内毛利率(%)": d.get("domestic_margin"), "海外单价": d.get("export_price"),
                "海外毛利率(%)": d.get("export_margin")
            })
        st.dataframe(pd.DataFrame(cost_rows), use_container_width=True, hide_index=True)

        # 财务表
        st.markdown("**财务数据 (亿元)**")
        fin_rows = []
        for y in periods:
            d = fin_data.get(y, {})
            fin_rows.append({
                "年度": y, "营收": d.get("revenue"), "毛利率(%)": d.get("gross_margin"),
                "净利润": d.get("net_profit"), "净利率(%)": d.get("net_margin"),
                "Q1营收": d.get("rv_q1"), "Q2营收": d.get("rv_q2"),
                "Q3营收": d.get("rv_q3"), "Q4营收": d.get("rv_q4"),
            })
        st.dataframe(pd.DataFrame(fin_rows), use_container_width=True, hide_index=True)
