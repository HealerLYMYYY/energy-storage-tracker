"""对比分析页"""
import streamlit as st
import pandas as pd
from utils.data_manager import get_competitors, get_shipment, get_cost, get_financial
from utils.visualization import ship_trend_chart, fin_bar_chart, cost_margin_scatter, qtr_bar_chart


def show_compare():
    st.title("📈 竞对对比分析")
    st.caption("多维度横向对比核心竞对")

    competitors = get_competitors()
    ids = ["catl", "byd", "hb", "hc", "tesla"]
    top5 = [c for c in competitors if c["cid"] in ids]
    periods = ["2022", "2023", "2024", "2025"]

    ship_map, cost_map, fin_map = {}, {}, {}
    for c in top5:
        ship_map[c["cid"]] = get_shipment(c["cid"])
        cost_map[c["cid"]] = get_cost(c["cid"])
        fin_map[c["cid"]] = get_financial(c["cid"])

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📦 出货量对比")
        fig = ship_trend_chart(top5, ship_map, periods)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("💰 营收对比 (2024 vs 2025)")
        fig = fin_bar_chart(top5, fin_map, "revenue", "2024", "2025")
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("🎯 成本-毛利散点矩阵")
        fig = cost_margin_scatter(top5, cost_map, fin_map)
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        st.subheader("📊 海外占比 vs 海外毛利")
        import plotly.graph_objects as go
        xs, ys, names, colors = [], [], [], []
        for c in top5:
            s = ship_map[c["cid"]].get("2025", {})
            co = cost_map[c["cid"]].get("2025", {})
            t = s.get("total", 0) or 1
            ex_ratio = (s.get("export", 0) or 0) / t * 100
            em = co.get("export_margin") or 0
            if em > 0:
                xs.append(ex_ratio); ys.append(em)
                names.append(c["name"]); colors.append(c["color"])
        fig_s = go.Figure()
        fig_s.add_trace(go.Scatter(x=xs, y=ys, mode="markers+text", text=names,
                                   textposition="top center", marker=dict(size=14, color=colors)))
        fig_s.update_layout(xaxis_title="海外占比(%)", yaxis_title="海外毛利率(%)",
                            margin=dict(l=20, r=20, t=10, b=20),
                            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_s, use_container_width=True)

    st.subheader("📋 Q1-Q4 季度营收拆分 (2025)")
    fig = qtr_bar_chart(top5, fin_map, "rv", "2025")
    st.plotly_chart(fig, use_container_width=True)

    # 竞争态势表
    st.subheader("📊 竞争态势矩阵 (2025)")
    matrix = []
    for c in top5:
        s = ship_map[c["cid"]].get("2025", {})
        co = cost_map[c["cid"]].get("2025", {})
        f = fin_map[c["cid"]].get("2025", {})
        matrix.append({
            "公司": c["name"], "出货(GWh)": f'{s.get("total","-"):.1f}',
            "成本(¥/Wh)": f'{co.get("system_cost","-"):.3f}' if co.get("system_cost") else "-",
            "国内毛利": f'{co.get("domestic_margin","-"):.1f}%' if co.get("domestic_margin") else "-",
            "海外毛利": f'{co.get("export_margin","-"):.1f}%' if co.get("export_margin") else "-",
            "营收(亿)": f'{f.get("revenue","-"):.1f}' if f.get("revenue") else "-",
            "净利(亿)": f'{f.get("net_profit","-"):.1f}' if f.get("net_profit") is not None else "-",
            "净利率": f'{f.get("net_margin","-"):.1f}%' if f.get("net_margin") else "-",
        })
    st.dataframe(pd.DataFrame(matrix), use_container_width=True, hide_index=True)
