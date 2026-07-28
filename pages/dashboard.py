"""Dashboard - 光储行业总览"""
import streamlit as st
import pandas as pd
from utils.data_manager import get_competitors, get_all_shipments, get_financial
from utils.visualization import ship_trend_chart, ship_stack_chart, fin_bar_chart, qtr_bar_chart


def show_dashboard():
    st.title("📊 光储行业竞对追踪")
    st.caption("出货量 · 成本 · 利润 | 9家核心竞对实时监控")

    competitors = get_competitors()
    all_ship = get_all_shipments()
    periods = ["2022", "2023", "2024", "2025"]

    # 构建数据映射
    ship_map = {}
    fin_map = {}
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

    # Hero KPI
    total_2025 = sum(ship_map.get(c["cid"], {}).get("2025", {}).get("total", 0) or 0 for c in competitors)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("行业总出货 (2025)", f"{total_2025:.0f} GWh")
    with col2:
        st.metric("追踪企业", "9 家")
    with col3:
        st.metric("覆盖区域", "6 大洲")
    with col4:
        st.metric("数据年度", "2022-2025")

    st.divider()

    # 公司卡片
    st.subheader("📋 竞对公司概览")
    cols = st.columns(5)
    for i, c in enumerate(competitors[:5]):
        with cols[i]:
            s25 = ship_map.get(c["cid"], {}).get("2025", {})
            s24 = ship_map.get(c["cid"], {}).get("2024", {})
            g = ((s25.get("total", 0) or 0) - (s24.get("total", 0) or 0)) / (s24.get("total", 1) or 1) * 100
            st.markdown(f"""
            <div style="border:1px solid #e5e7eb;border-radius:10px;padding:12px;cursor:pointer;
                        border-top:3px solid {c['color']}">
                <div style="font-weight:600;font-size:0.9rem">{c['name']}</div>
                <div style="font-size:0.7rem;color:#6b7280">{c['ticker']}</div>
                <div style="font-size:0.8rem;margin-top:6px">出货: {s25.get('total','-'):.1f} GWh</div>
                <div style="font-size:0.7rem;color:{'#10b981' if g>0 else '#ef4444'}">{'↑' if g>0 else '↓'}{abs(g):.0f}%</div>
            </div>""", unsafe_allow_html=True)

    cols2 = st.columns(4)
    for i, c in enumerate(competitors[5:]):
        with cols2[i]:
            s25 = ship_map.get(c["cid"], {}).get("2025", {})
            st.markdown(f"""
            <div style="border:1px solid #e5e7eb;border-radius:10px;padding:12px;cursor:pointer;
                        border-top:3px solid {c['color']}">
                <div style="font-weight:600;font-size:0.9rem">{c['name']}</div>
                <div style="font-size:0.7rem;color:#6b7280">{c['ticker']}</div>
                <div style="font-size:0.8rem;margin-top:6px">出货: {s25.get('total','-'):.1f} GWh</div>
            </div>""", unsafe_allow_html=True)

    st.divider()

    # 图表区
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("📦 出货量趋势 (GWh)")
        top5 = [c for c in competitors if c["cid"] in ["catl", "byd", "hb", "hc", "tesla"]]
        fig = ship_trend_chart(top5, ship_map, periods)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.subheader("🌍 国内 vs 海外出货 (2025)")
        fig = ship_stack_chart(competitors, ship_map, "2025", "region")
        st.plotly_chart(fig, use_container_width=True)

    col_c, col_d = st.columns(2)
    with col_c:
        st.subheader("🏗️ 应用场景分布 (2025)")
        fig = ship_stack_chart(competitors, ship_map, "2025", "app")
        st.plotly_chart(fig, use_container_width=True)

    with col_d:
        st.subheader("💰 Q1-Q4 营收拆分 (2025)")
        fig = qtr_bar_chart(competitors, fin_map, "rv", "2025")
        st.plotly_chart(fig, use_container_width=True)

    # 竞争态势矩阵
    st.subheader("📊 竞争态势矩阵 (2025)")
    matrix_data = []
    for c in competitors:
        s = ship_map.get(c["cid"], {}).get("2025", {})
        co = get_financial(c["cid"]).get("2025", {})
        matrix_data.append({
            "公司": c["name"],
            "出货(GWh)": f'{s.get("total","-"):.1f}',
            "营收(亿)": f'{co.get("revenue","-"):.1f}' if co.get("revenue") else "-",
            "毛利率(%)": f'{co.get("gross_margin","-"):.1f}' if co.get("gross_margin") else "-",
            "净利(亿)": f'{co.get("net_profit","-"):.1f}' if co.get("net_profit") else "-",
            "净利率(%)": f'{co.get("net_margin","-"):.1f}' if co.get("net_margin") else "-",
        })
    st.dataframe(pd.DataFrame(matrix_data), use_container_width=True, hide_index=True)
