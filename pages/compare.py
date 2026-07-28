"""Peer Comparison — Cross-sectional Analysis · 2026E Edition"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.data_manager import get_competitors, get_shipment, get_cost, get_financial
from utils.visualization import ship_trend_chart, fin_bar_chart, cost_margin_scatter, qtr_bar_chart


def show_compare():
    st.markdown('<h1>Peer Comparison</h1>', unsafe_allow_html=True)
    st.caption("Cross-sectional analysis of core peers across volume, cost, and profit dimensions")

    competitors = get_competitors()
    ids = ["catl", "byd", "hb", "hc", "tesla"]
    top5 = [c for c in competitors if c["cid"] in ids]
    periods = ["2022", "2023", "2024", "2025", "2026E"]

    ship_map, cost_map, fin_map = {}, {}, {}
    for c in top5:
        ship_map[c["cid"]] = get_shipment(c["cid"])
        cost_map[c["cid"]] = get_cost(c["cid"])
        fin_map[c["cid"]] = get_financial(c["cid"])

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<h3>Shipment Comparison</h3>', unsafe_allow_html=True)
        fig = ship_trend_chart(top5, ship_map, periods)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    with col2:
        st.markdown('<h3>Revenue · 2025 vs 2026E</h3>', unsafe_allow_html=True)
        fig = fin_bar_chart(top5, fin_map, "revenue", "2025", "2026E")
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    col3, col4 = st.columns(2)
    with col3:
        st.markdown('<h3>Cost-Margin Positioning · 2026E</h3>', unsafe_allow_html=True)
        fig = cost_margin_scatter(top5, cost_map, fin_map, "2026E")
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    with col4:
        st.markdown('<h3>Export Ratio vs. Export Margin · 2026E</h3>', unsafe_allow_html=True)
        xs, ys, names, colors = [], [], [], []
        for c in top5:
            s = ship_map[c["cid"]].get("2026E", {})
            co = cost_map[c["cid"]].get("2026E", {})
            t = s.get("total", 0) or 1
            ex_ratio = (s.get("export", 0) or 0) / t * 100
            em = co.get("export_margin") or 0
            if em > 0:
                xs.append(ex_ratio); ys.append(em)
                names.append(c["name"]); colors.append(c["color"])
        fig_s = go.Figure()
        fig_s.add_trace(go.Scatter(x=xs, y=ys, mode="markers+text", text=names,
                                   textposition="top center", marker=dict(size=14, color=colors)))
        fig_s.update_layout(xaxis_title="Export Ratio (%)", yaxis_title="Export GM (%)",
                            margin=dict(l=20, r=20, t=10, b=20),
                            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                            font=dict(color="#8b949e"))
        st.plotly_chart(fig_s, use_container_width=True, config={'displayModeBar': False})

    st.markdown('<h3>Quarterly Revenue Composition · 2026E</h3>', unsafe_allow_html=True)
    fig = qtr_bar_chart(top5, fin_map, "rv", "2026E")
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    st.markdown('<h3>Competitive Matrix · 2026E</h3>', unsafe_allow_html=True)
    matrix = []
    for c in top5:
        s = ship_map[c["cid"]].get("2026E", {})
        co = cost_map[c["cid"]].get("2026E", {})
        f = fin_map[c["cid"]].get("2026E", {})
        matrix.append({
            "Company": c["name"],
            "Shipment (GWh)": f'{s.get("total","—"):.1f}' if s.get("total") else "—",
            "Sys. Cost (RMB/Wh)": f'{co.get("system_cost","—"):.3f}' if co.get("system_cost") else "—",
            "Domestic GM": f'{co.get("domestic_margin","—"):.1f}%' if co.get("domestic_margin") else "—",
            "Export GM": f'{co.get("export_margin","—"):.1f}%' if co.get("export_margin") else "—",
            "Revenue (bn)": f'{f.get("revenue","—"):.1f}' if f.get("revenue") else "—",
            "Net Profit (bn)": f'{f.get("net_profit","—"):.1f}' if f.get("net_profit") is not None else "—",
            "Net Margin": f'{f.get("net_margin","—"):.1f}%' if f.get("net_margin") else "—",
        })
    st.dataframe(pd.DataFrame(matrix), use_container_width=True, hide_index=True)
