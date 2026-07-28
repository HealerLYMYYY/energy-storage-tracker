"""Dashboard — Institutional Overview"""

import streamlit as st
import pandas as pd
from utils.data_manager import get_competitors, get_all_shipments, get_financial
from utils.visualization import ship_trend_chart, ship_stack_chart, fin_bar_chart, qtr_bar_chart


def show_dashboard():
    st.markdown('<h1>Competitive Intelligence Dashboard</h1>', unsafe_allow_html=True)
    st.caption("Energy Storage · Shipment · Cost · Profit · 9 Peers · 2022–2025")

    competitors = get_competitors()
    all_ship = get_all_shipments()
    periods = ["2022", "2023", "2024", "2025"]

    ship_map, fin_map = {}, {}
    for c in competitors:
        ship_map[c["cid"]] = {}
        fin_map[c["cid"]] = {}
    for s in all_ship:
        ship_map[s["cid"]][s["period"]] = {
            "total": s["total_gwh"], "domestic": s["domestic_gwh"], "export": s["export_gwh"],
            "residential": s["residential_gwh"], "utility": s["utility_gwh"], "commercial": s["commercial_gwh"]
        }
    for c in competitors:
        fin_map[c["cid"]] = get_financial(c["cid"])

    # ——— KPI Row ———
    total_2025 = sum(ship_map.get(c["cid"], {}).get("2025", {}).get("total", 0) or 0 for c in competitors)
    total_2024 = sum(ship_map.get(c["cid"], {}).get("2024", {}).get("total", 0) or 0 for c in competitors)
    yoy = (total_2025 - total_2024) / total_2024 * 100 if total_2024 else 0

    k1, k2, k3, k4 = st.columns(4)
    with k1: st.metric("Global ESS Shipment 2025E", f"{total_2025:.0f} GWh", f"{yoy:.1f}% YoY")
    with k2: st.metric("Coverage Universe", "9 Companies", "6 Markets")
    with k3: st.metric("Data Horizon", "2022–2025", "Quarterly Granularity")
    with k4: st.metric("Data Sources", "Annual Reports", "Industry Trackers")

    st.divider()

    # ——— Peer Cards ———
    st.markdown('<h3>Peer Universe</h3>', unsafe_allow_html=True)
    cols = st.columns(9)
    for i, c in enumerate(competitors):
        with cols[i]:
            s25 = ship_map.get(c["cid"], {}).get("2025", {})
            st.markdown(f"""
            <div style="background:#161b22;border:1px solid #21262d;border-radius:4px;padding:10px 8px;text-align:center;
                        border-top:2px solid {c['color']};">
                <div style="font-size:0.75rem;font-weight:600;color:#e6edf3;">{c['name']}</div>
                <div style="font-size:0.6rem;color:#8b949e;">{c['ticker']}</div>
                <div style="font-size:0.85rem;font-weight:600;color:#c9a96e;margin-top:6px;font-family:'JetBrains Mono',monospace;">
                    {s25.get('total','—'):.1f}</div>
                <div style="font-size:0.55rem;color:#484f58;">GWh (2025E)</div>
            </div>""", unsafe_allow_html=True)

    st.divider()

    # ——— Charts ———
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('<h3>Shipment Trajectory</h3>', unsafe_allow_html=True)
        top5 = [c for c in competitors if c["cid"] in ["catl", "byd", "hb", "hc", "tesla"]]
        fig = ship_trend_chart(top5, ship_map, periods)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    with col_b:
        st.markdown('<h3>Domestic vs. Export Split · 2025E</h3>', unsafe_allow_html=True)
        fig = ship_stack_chart(competitors, ship_map, "2025", "region")
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    col_c, col_d = st.columns(2)
    with col_c:
        st.markdown('<h3>Application Mix · 2025E</h3>', unsafe_allow_html=True)
        fig = ship_stack_chart(competitors, ship_map, "2025", "app")
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    with col_d:
        st.markdown('<h3>Quarterly Revenue Breakdown · 2025E</h3>', unsafe_allow_html=True)
        fig = qtr_bar_chart(competitors, fin_map, "rv", "2025")
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # ——— Competitive Matrix ———
    st.markdown('<h3>Competitive Positioning Matrix · 2025E</h3>', unsafe_allow_html=True)
    matrix_data = []
    for c in competitors:
        s = ship_map.get(c["cid"], {}).get("2025", {})
        co = get_financial(c["cid"]).get("2025", {})
        matrix_data.append({
            "Company": c["name"],
            "Shipment (GWh)": f'{s.get("total","—"):.1f}',
            "Revenue (RMB bn)": f'{co.get("revenue","—"):.1f}' if co.get("revenue") else "—",
            "Gross Margin (%)": f'{co.get("gross_margin","—"):.1f}' if co.get("gross_margin") else "—",
            "Net Profit (RMB bn)": f'{co.get("net_profit","—"):.1f}' if co.get("net_profit") is not None else "—",
            "Net Margin (%)": f'{co.get("net_margin","—"):.1f}' if co.get("net_margin") else "—",
        })
    st.dataframe(pd.DataFrame(matrix_data), use_container_width=True, hide_index=True)
