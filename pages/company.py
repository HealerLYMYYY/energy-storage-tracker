"""Company Deep Dive — Volume / Cost / Profit"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.data_manager import get_competitors, get_shipment, get_cost, get_financial
from utils.visualization import company_trend_chart, cost_price_chart, qtr_bar_chart


def show_company():
    competitors = get_competitors()
    if "selected_company" not in st.session_state:
        st.session_state.selected_company = competitors[0]["name"]

    comp_map = {c["name"]: c for c in competitors}

    st.markdown('<h1>Company Intelligence</h1>', unsafe_allow_html=True)

    # ——— Company selector tabs ———
    cols = st.columns(9)
    for i, c in enumerate(competitors):
        with cols[i]:
            is_active = c["name"] == st.session_state.selected_company
            style = "background:#c9a96e;color:#0d1117;" if is_active else "background:transparent;color:#8b949e;"
            if st.button(c["name"], key=f"comp_{c['cid']}", use_container_width=True,
                         type="primary" if is_active else "secondary"):
                st.session_state.selected_company = c["name"]
                st.rerun()

    comp = comp_map[st.session_state.selected_company]
    cid = comp["cid"]
    ship_data = get_shipment(cid)
    cost_data = get_cost(cid)
    fin_data = get_financial(cid)
    periods = ["2022", "2023", "2024", "2025"]

    s25 = ship_data.get("2025", {})
    co25 = cost_data.get("2025", {})
    f25 = fin_data.get("2025", {})

    st.divider()

    # ——— Company Header ———
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:16px;margin-bottom:20px;">
        <div style="width:44px;height:44px;border:1px solid #21262d;border-radius:4px;background:#161b22;
                    display:flex;align-items:center;justify-content:center;color:{comp['color']};font-size:1.1rem;font-weight:600;">{comp['name'][0]}</div>
        <div>
            <div style="font-size:1.1rem;font-weight:600;color:#e6edf3;">{comp['name']}<span style="font-size:0.7rem;color:#8b949e;margin-left:10px;">{comp['ticker']}</span></div>
            <div style="font-size:0.7rem;color:#8b949e;">{comp['company_type']} · {comp['description'][:60]}...</div>
        </div>
    </div>""", unsafe_allow_html=True)

    k1, k2, k3, k4 = st.columns(4)
    with k1: st.metric("Shipment 2025E", f"{s25.get('total','—'):.1f} GWh")
    with k2: st.metric("Domestic GM", f"{co25.get('domestic_margin','—'):.1f}%" if co25.get("domestic_margin") else "N/A")
    with k3: st.metric("Export GM", f"{co25.get('export_margin','—'):.1f}%" if co25.get("export_margin") else "N/A")
    with k4: st.metric("Net Profit", f"{f25.get('net_profit','—'):.1f} bn" if f25.get("net_profit") is not None else "N/A")

    st.divider()

    tab1, tab2, tab3 = st.tabs(["VOLUME · COST · PROFIT", "SENTIMENT", "DATA TABLES"])

    with tab1:
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown('<h3>Shipment Trajectory</h3>', unsafe_allow_html=True)
            fig = company_trend_chart(ship_data, periods, comp["color"], "GWh", "total")
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

            st.markdown('<h3>Regional Split</h3>', unsafe_allow_html=True)
            dom = [ship_data.get(y, {}).get("domestic", 0) or 0 for y in periods]
            exp = [ship_data.get(y, {}).get("export", 0) or 0 for y in periods]
            fig2 = go.Figure(data=[
                go.Bar(name="Domestic", x=periods, y=dom, marker_color="rgba(201,169,110,0.85)"),
                go.Bar(name="Export", x=periods, y=exp, marker_color="rgba(91,141,184,0.85)")
            ])
            fig2.update_layout(barmode="stack", margin=dict(l=20, r=20, t=10, b=20),
                               plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                               font=dict(color="#8b949e"), legend=dict(font=dict(color="#8b949e")))
            st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})

        with col_b:
            st.markdown('<h3>Cost / Price / Margin</h3>', unsafe_allow_html=True)
            fig3 = cost_price_chart(cost_data, periods, comp["color"])
            st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': False})

            st.markdown('<h3>Quarterly Revenue · 2025E</h3>', unsafe_allow_html=True)
            fig4 = qtr_bar_chart([comp], {cid: fin_data}, "rv", "2025")
            st.plotly_chart(fig4, use_container_width=True, config={'displayModeBar': False})

    with tab2:
        st.markdown('<h3>Sentiment & News</h3>', unsafe_allow_html=True)
        st.markdown(f"**Keywords**: {comp['keywords']}")
        cl, cm, cr = st.columns(3)
        with cl: st.link_button("Google News", f"https://news.google.com/search?q={comp['name']}+energy+storage&hl=en", use_container_width=True)
        with cm: st.link_button("Baidu Search", f"https://www.baidu.com/s?wd={comp['name']}+储能", use_container_width=True)
        with cr: st.link_button("Eastmoney", f"https://so.eastmoney.com/news/s?keyword={comp['name']}", use_container_width=True)

    with tab3:
        st.markdown('<h3>Shipment Data (GWh)</h3>', unsafe_allow_html=True)
        ship_rows = [{"Year": y, "Total": ship_data.get(y, {}).get("total"), "Domestic": ship_data.get(y, {}).get("domestic"),
                      "Export": ship_data.get(y, {}).get("export"), "Residential": ship_data.get(y, {}).get("residential"),
                      "Utility-scale": ship_data.get(y, {}).get("utility"), "C&I": ship_data.get(y, {}).get("commercial")} for y in periods]
        st.dataframe(pd.DataFrame(ship_rows), use_container_width=True, hide_index=True)

        st.markdown('<h3>Cost & Pricing (RMB/Wh)</h3>', unsafe_allow_html=True)
        cost_rows = [{"Year": y, "System Cost": cost_data.get(y, {}).get("system_cost"), "Domestic ASP": cost_data.get(y, {}).get("domestic_price"),
                      "Domestic GM%": cost_data.get(y, {}).get("domestic_margin"), "Export ASP": cost_data.get(y, {}).get("export_price"),
                      "Export GM%": cost_data.get(y, {}).get("export_margin")} for y in periods]
        st.dataframe(pd.DataFrame(cost_rows), use_container_width=True, hide_index=True)

        st.markdown('<h3>Financials (RMB bn)</h3>', unsafe_allow_html=True)
        fin_rows = [{"Year": y, "Revenue": fin_data.get(y, {}).get("revenue"), "Gross Margin%": fin_data.get(y, {}).get("gross_margin"),
                     "Net Profit": fin_data.get(y, {}).get("net_profit"), "Net Margin%": fin_data.get(y, {}).get("net_margin"),
                     "Q1 Rev": fin_data.get(y, {}).get("rv_q1"), "Q2 Rev": fin_data.get(y, {}).get("rv_q2"),
                     "Q3 Rev": fin_data.get(y, {}).get("rv_q3"), "Q4 Rev": fin_data.get(y, {}).get("rv_q4")} for y in periods]
        st.dataframe(pd.DataFrame(fin_rows), use_container_width=True, hide_index=True)
