"""仪表盘 — 机构级总览 · 2026E 季度化"""

import streamlit as st
import pandas as pd
from utils.data_manager import (get_competitors, get_all_shipments, get_financial, get_cost,
                                get_shipment_quarters)
from utils.visualization import (ship_trend_chart, ship_stack_chart, quarterly_stack_chart)


def _card(name, ticker, value, delta, color):
    delta_color = color if delta and delta > 0 else "#6b7280"
    delta_str = f"{delta:+.1f}%" if delta else "—"
    value_str = f"{value:.1f}" if value else "—"
    return f"""
    <div style="background:#FFFFFF;border:1px solid #e5e7eb;border-radius:8px;padding:14px 8px;text-align:center;
                border-top:3px solid {color};min-height:110px;display:flex;flex-direction:column;justify-content:center;">
        <div style="font-size:0.78rem;font-weight:600;color:#1a1a2e;">{name}</div>
        <div style="font-size:0.6rem;color:#9ca3af;margin-top:2px;">{ticker}</div>
        <div style="font-size:1.05rem;font-weight:600;color:#1a1a2e;margin-top:8px;font-family:'JetBrains Mono',monospace;">
            {value_str}</div>
        <div style="font-size:0.6rem;color:#9ca3af;margin-top:2px;">GWh (2026E)</div>
        <div style="font-size:0.65rem;color:{delta_color};margin-top:2px;font-weight:500;">{delta_str}</div>
    </div>"""


def show_dashboard():
    st.markdown('<h1>竞争情报仪表盘</h1>', unsafe_allow_html=True)
    st.caption("光储行业 · 出货量 · 成本 · 利润 · 9 家重点公司 · 2022–2026E")

    competitors = get_competitors()
    all_ship = get_all_shipments()
    periods = ["2022", "2023", "2024", "2025", "2026E"]

    ship_map, fin_map, cost_map = {}, {}, {}
    for c in competitors:
        ship_map[c["cid"]] = {}
        fin_map[c["cid"]] = {}
        cost_map[c["cid"]] = {}
    for s in all_ship:
        ship_map[s["cid"]][s["period"]] = {
            "total": s["total_gwh"], "domestic": s["domestic_gwh"], "export": s["export_gwh"],
            "residential": s["residential_gwh"], "utility": s["utility_gwh"], "commercial": s["commercial_gwh"]
        }
    for c in competitors:
        fin_map[c["cid"]] = get_financial(c["cid"])
        cost_map[c["cid"]] = get_cost(c["cid"])

    # 季度数据（2026）
    ship_q_map = {c["cid"]: get_shipment_quarters(c["cid"], "2026") for c in competitors}
    rv_q_map, np_q_map = {}, {}
    for c in competitors:
        f26 = fin_map[c["cid"]].get("2026E", {})
        rv_q_map[c["cid"]] = {f"Q{i}": f26.get(f"rv_q{i}") for i in range(1, 5)}
        np_q_map[c["cid"]] = {f"Q{i}": f26.get(f"np_q{i}") for i in range(1, 5)}

    # ——— KPI 行 ———
    total_2026 = sum(ship_map.get(c["cid"], {}).get("2026E", {}).get("total", 0) or 0 for c in competitors)
    total_2025 = sum(ship_map.get(c["cid"], {}).get("2025", {}).get("total", 0) or 0 for c in competitors)
    yoy = (total_2026 - total_2025) / total_2025 * 100 if total_2025 else 0

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("全球储能出货量 2026E", f"{total_2026:.0f} GWh", f"{yoy:.1f}% 同比")
    with k2:
        st.metric("覆盖公司", "9 家", "6 大市场")
    with k3:
        st.metric("数据区间", "2022–2026E", "2026 按季度追踪")
    with k4:
        st.metric("数据来源", "年报", "行业数据")

    st.divider()

    # ——— 同业卡片 ———
    st.markdown('<h3>同业公司 · 2026E</h3>', unsafe_allow_html=True)
    # 9 家公司分 3 行展示，每行 3 个，避免过窄导致文字拥挤
    for row in range(3):
        cols = st.columns(3)
        for i in range(3):
            idx = row * 3 + i
            if idx >= len(competitors):
                break
            c = competitors[idx]
            with cols[i]:
                s26 = ship_map.get(c["cid"], {}).get("2026E", {})
                s25 = ship_map.get(c["cid"], {}).get("2025", {})
                v26 = s26.get("total")
                v25 = s25.get("total", 0) or 0
                delta = (v26 - v25) / v25 * 100 if v26 and v25 else 0
                st.markdown(_card(c["name"], c["ticker"], v26, delta, c["color"]), unsafe_allow_html=True)

    st.divider()

    # ——— 图表行 1：年度趋势 + 结构 ———
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('<h3>出货量趋势（2026E 为季度加总）</h3>', unsafe_allow_html=True)
        top5 = [c for c in competitors if c["cid"] in ["catl", "byd", "hb", "hc", "tesla"]]
        fig = ship_trend_chart(top5, ship_map, periods)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    with col_b:
        st.markdown('<h3>国内 vs 海外出货 · 2026E</h3>', unsafe_allow_html=True)
        fig = ship_stack_chart(competitors, ship_map, "2026E", "region")
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # ——— 图表行 2：2026E 季度堆积（核心） ———
    st.markdown('<h3>2026E 季度出货量</h3>', unsafe_allow_html=True)
    top5_cids = {"catl", "byd", "hb", "hc", "tesla"}
    top5 = [c for c in competitors if c["cid"] in top5_cids]
    fig_q = quarterly_stack_chart(top5, ship_q_map, "GWh")
    st.plotly_chart(fig_q, use_container_width=True, config={'displayModeBar': False})

    col_c, col_d = st.columns(2)
    with col_c:
        st.markdown('<h3>2026E 季度营收（亿元）</h3>', unsafe_allow_html=True)
        fig_rv = quarterly_stack_chart(top5, rv_q_map, "亿元")
        st.plotly_chart(fig_rv, use_container_width=True, config={'displayModeBar': False})

    with col_d:
        st.markdown('<h3>2026E 季度净利润（亿元）</h3>', unsafe_allow_html=True)
        fig_np = quarterly_stack_chart(top5, np_q_map, "亿元")
        st.plotly_chart(fig_np, use_container_width=True, config={'displayModeBar': False})

    # ——— 竞争矩阵 ———
    st.markdown('<h3>竞争定位矩阵 · 2026E</h3>', unsafe_allow_html=True)
    matrix_data = []
    for c in competitors:
        s = ship_map.get(c["cid"], {}).get("2026E", {})
        co = fin_map.get(c["cid"], {}).get("2026E", {})
        matrix_data.append({
            "公司": c["name"],
            "出货量 (GWh)": f'{s.get("total","—"):.1f}' if s.get("total") else "—",
            "营收 (亿元)": f'{co.get("revenue","—"):.1f}' if co.get("revenue") else "—",
            "毛利率 (%)": f'{co.get("gross_margin","—"):.1f}' if co.get("gross_margin") else "—",
            "净利润 (亿元)": f'{co.get("net_profit","—"):.1f}' if co.get("net_profit") is not None else "—",
            "净利率 (%)": f'{co.get("net_margin","—"):.1f}' if co.get("net_margin") else "—",
        })
    st.dataframe(pd.DataFrame(matrix_data), use_container_width=True, hide_index=True)
