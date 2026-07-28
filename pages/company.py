"""公司深度分析 — 量/本/利 · 2026E 预测版"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.data_manager import get_competitors, get_shipment, get_cost, get_financial
from utils.visualization import company_trend_chart, cost_price_chart, qtr_bar_chart, hex_to_rgba, FORECAST_PERIOD


def show_company():
    competitors = get_competitors()
    if "selected_company" not in st.session_state:
        st.session_state.selected_company = competitors[0]["name"]

    comp_map = {c["name"]: c for c in competitors}

    st.markdown('<h1>公司情报</h1>', unsafe_allow_html=True)

    # ——— 公司选择器 ———
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
    periods = ["2022", "2023", "2024", "2025", "2026E"]

    # 2026E 数据
    s26 = ship_data.get("2026E", {})
    co26 = cost_data.get("2026E", {})
    f26 = fin_data.get("2026E", {})

    # 2025 数据用于参考
    s25 = ship_data.get("2025", {})

    st.divider()

    # ——— 公司头部 ———
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:16px;margin-bottom:20px;">
        <div style="width:44px;height:44px;border:1px solid #21262d;border-radius:4px;background:#161b22;
                    display:flex;align-items:center;justify-content:center;color:{comp['color']};font-size:1.1rem;font-weight:600;">{comp['name'][0]}</div>
        <div>
            <div style="font-size:1.1rem;font-weight:600;color:#e6edf3;">{comp['name']}<span style="font-size:0.7rem;color:#8b949e;margin-left:10px;">{comp['ticker']}</span></div>
            <div style="font-size:0.7rem;color:#8b949e;">{comp['company_type']} · {comp['description'][:60]}...</div>
        </div>
    </div>""", unsafe_allow_html=True)

    # ——— KPI 行 (2026E) ———
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        delta_ship = s26.get("total", 0) - s25.get("total", 0) if s26.get("total") and s25.get("total") else None
        st.metric("出货量 2026E", f"{s26.get('total','—'):.1f} GWh" if s26.get("total") else "N/A",
                  f"{delta_ship:+.1f} GWh" if delta_ship else None)
    with k2:
        st.metric("国内毛利率", f"{co26.get('domestic_margin','—'):.1f}%" if co26.get("domestic_margin") else "N/A")
    with k3:
        st.metric("海外毛利率", f"{co26.get('export_margin','—'):.1f}%" if co26.get("export_margin") else "N/A")
    with k4:
        st.metric("净利润", f"{f26.get('net_profit','—'):.1f} 亿元" if f26.get("net_profit") is not None else "N/A")

    st.divider()

    tab1, tab2 = st.tabs(["量·本·利", "数据表"])

    with tab1:
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown('<h3>出货量趋势</h3>', unsafe_allow_html=True)
            fig = company_trend_chart(ship_data, periods, comp["color"], "GWh", "total")
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

            st.markdown('<h3>区域结构</h3>', unsafe_allow_html=True)
            dom = [ship_data.get(y, {}).get("domestic", 0) or 0 for y in periods]
            exp = [ship_data.get(y, {}).get("export", 0) or 0 for y in periods]
            fig2 = go.Figure(data=[
                go.Bar(name="国内", x=periods, y=dom, marker_color="rgba(201,169,110,0.85)"),
                go.Bar(name="海外", x=periods, y=exp, marker_color="rgba(91,141,184,0.85)")
            ])
            fig2.update_layout(barmode="stack", margin=dict(l=20, r=20, t=10, b=20),
                               plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                               font=dict(color="#8b949e"), legend=dict(font=dict(color="#8b949e")))
            st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})

        with col_b:
            st.markdown('<h3>成本 / 价格 / 毛利</h3>', unsafe_allow_html=True)
            fig3 = cost_price_chart(cost_data, periods, comp["color"])
            st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': False})

            st.markdown('<h3>季度收入 · 2026E</h3>', unsafe_allow_html=True)
            fig4 = qtr_bar_chart([comp], {cid: fin_data}, "rv", "2026E")
            st.plotly_chart(fig4, use_container_width=True, config={'displayModeBar': False})

    with tab2:
        # ——— 出货量数据表 ———
        st.markdown('<h3>出货量数据 (GWh)</h3>', unsafe_allow_html=True)
        ship_rows = []
        for y in periods:
            row = {"年份": y, "总量": ship_data.get(y, {}).get("total"),
                   "国内": ship_data.get(y, {}).get("domestic"),
                   "海外": ship_data.get(y, {}).get("export"),
                   "户用": ship_data.get(y, {}).get("residential"),
                   "大储": ship_data.get(y, {}).get("utility"),
                   "工商业": ship_data.get(y, {}).get("commercial")}
            ship_rows.append(row)
        st.dataframe(pd.DataFrame(ship_rows), use_container_width=True, hide_index=True)

        # ——— 成本与价格表 ———
        st.markdown('<h3>成本与价格 (元/Wh)</h3>', unsafe_allow_html=True)
        cost_rows = []
        for y in periods:
            row = {"年份": y, "系统成本": cost_data.get(y, {}).get("system_cost"),
                   "国内均价": cost_data.get(y, {}).get("domestic_price"),
                   "国内毛利率%": cost_data.get(y, {}).get("domestic_margin"),
                   "海外均价": cost_data.get(y, {}).get("export_price"),
                   "海外毛利率%": cost_data.get(y, {}).get("export_margin")}
            cost_rows.append(row)
        st.dataframe(pd.DataFrame(cost_rows), use_container_width=True, hide_index=True)

        # ——— 财务数据表 ———
        # 2025：仅年度汇总；2026E：显示 Q1-Q4 拆分
        st.markdown('<h3>财务数据 (亿元)</h3>', unsafe_allow_html=True)
        fin_rows = []
        for y in periods:
            fd = fin_data.get(y, {})
            if y == "2026E":
                fin_rows.append({
                    "年份": y,
                    "营收": fd.get("revenue"),
                    "毛利率%": fd.get("gross_margin"),
                    "净利润": fd.get("net_profit"),
                    "净利率%": fd.get("net_margin"),
                    "Q1 营收": fd.get("rv_q1"),
                    "Q2 营收": fd.get("rv_q2"),
                    "Q3 营收": fd.get("rv_q3"),
                    "Q4 营收": fd.get("rv_q4"),
                })
            else:
                fin_rows.append({
                    "年份": y,
                    "营收": fd.get("revenue"),
                    "毛利率%": fd.get("gross_margin"),
                    "净利润": fd.get("net_profit"),
                    "净利率%": fd.get("net_margin"),
                })
        st.dataframe(pd.DataFrame(fin_rows), use_container_width=True, hide_index=True)
