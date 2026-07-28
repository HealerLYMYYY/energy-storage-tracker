"""Macro & Supply Chain — Industry-level Data"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from utils.data_manager import get_industry_data


def show_industry():
    st.markdown('<h1>Macro & Supply Chain</h1>', unsafe_allow_html=True)
    st.caption("Global PV · ESS · Li-ion Battery Shipment & Cost Trends")

    region = st.selectbox("Region", ["全球", "北美", "中国", "欧洲", "亚太", "拉美", "中东非"], key="ind_region",
                          label_visibility="collapsed")

    pv_data = get_industry_data("光伏", region)
    ess_data = get_industry_data("储能", region)
    lith_data = get_industry_data("锂电池", region)

    pv_2025 = next((d["metric_value"] for d in pv_data if d["period"] == "2025" and "光伏出货" in d["metric_name"]), 0)
    ess_2025 = next((d["metric_value"] for d in ess_data if d["period"] == "2025" and "储能出货" in d["metric_name"]), 0)
    lith_2025 = next((d["metric_value"] for d in lith_data if d["period"] == "2025" and "锂电池出货" in d["metric_name"]), 0)
    cost_2025 = next((d["metric_value"] for d in ess_data if d["period"] == "2025" and d["metric_name"] == "系统成本"), 0)

    k1, k2, k3, k4 = st.columns(4)
    with k1: st.metric("PV Shipment", f"{pv_2025} GW")
    with k2: st.metric("ESS Shipment", f"{ess_2025} GWh")
    with k3: st.metric("LiB Shipment", f"{lith_2025} GWh")
    with k4: st.metric("System Cost", f"¥{cost_2025:.2f}/Wh")

    st.divider()

    years = ["2020", "2021", "2022", "2023", "2024", "2025"]

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<h3>PV + ESS Shipment Growth</h3>', unsafe_allow_html=True)
        pv_vals = [next((d["metric_value"] for d in pv_data if d["period"] == y and "光伏出货" in d["metric_name"]), None) for y in years]
        ess_vals = [next((d["metric_value"] for d in ess_data if d["period"] == y and "储能出货" in d["metric_name"]), None) for y in years]
        fig = go.Figure(data=[
            go.Bar(name="PV (GW)", x=years, y=pv_vals, marker_color="rgba(201,169,110,0.8)"),
            go.Bar(name="ESS (GWh)", x=years, y=ess_vals, marker_color="rgba(91,141,184,0.8)")
        ])
        fig.update_layout(barmode="group", margin=dict(l=20, r=20, t=10, b=20),
                          plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                          font=dict(color="#8b949e"), legend=dict(font=dict(color="#8b949e")))
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    with col2:
        st.markdown('<h3>LiB Shipment & Lithium Carbonate Price</h3>', unsafe_allow_html=True)
        lith_vals = [next((d["metric_value"] for d in lith_data if d["period"] == y and "锂电池出货" in d["metric_name"]), None) for y in years]
        price_vals = [next((d["metric_value"] for d in lith_data if d["period"] == y and "碳酸锂" in d["metric_name"]), None) for y in years]
        fig2 = go.Figure(data=[
            go.Bar(name="LiB (GWh)", x=years, y=lith_vals, marker_color="rgba(91,141,184,0.8)")
        ])
        fig2.add_trace(go.Scatter(x=years, y=price_vals, name="Li2CO3 Price (RMB 10k/t)",
                                  yaxis="y2", line=dict(color="#c9a96e", width=2.5), mode="lines+markers"))
        fig2.update_layout(yaxis2=dict(overlaying="y", side="right"),
                           margin=dict(l=20, r=20, t=10, b=20),
                           plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                           font=dict(color="#8b949e"), legend=dict(font=dict(color="#8b949e")))
        st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})

    col3, col4 = st.columns(2)
    with col3:
        st.markdown('<h3>System Cost Deflation</h3>', unsafe_allow_html=True)
        cost_vals = [next((d["metric_value"] for d in ess_data if d["period"] == y and d["metric_name"] == "系统成本"), None) for y in years]
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=years, y=cost_vals, name="System Cost (RMB/Wh)",
                                  line=dict(color="#c9a96e", width=2.5), mode="lines+markers",
                                  fill="tozeroy", fillcolor="rgba(201,169,110,0.08)", marker=dict(size=8)))
        fig3.update_layout(margin=dict(l=20, r=20, t=10, b=20),
                           plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                           font=dict(color="#8b949e"))
        st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': False})

    with col4:
        st.markdown('<h3>Regional ESS Mix · 2025E</h3>', unsafe_allow_html=True)
        region_data = {"N. America": 95, "China": 130, "Europe": 55, "APAC": 18, "LATAM": 7, "MEA": 5}
        fig4 = px.pie(values=list(region_data.values()), names=list(region_data.keys()),
                      color_discrete_sequence=["#c9a96e", "#5b8db8", "#b8956a", "#7aa3c4", "#8b7355", "#4a6d8c"])
        fig4.update_layout(margin=dict(l=20, r=20, t=10, b=20),
                           paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#8b949e"))
        st.plotly_chart(fig4, use_container_width=True, config={'displayModeBar': False})

    st.markdown('<h3>Industry Data Table</h3>', unsafe_allow_html=True)
    all_ind = get_industry_data(region=region)
    if all_ind:
        df = pd.DataFrame(all_ind)
        display = df.rename(columns={"category": "Category", "metric_name": "Metric", "metric_value": "Value",
                                     "unit": "Unit", "period": "Period", "region": "Region"})
        cols = [c for c in ["Category", "Metric", "Value", "Unit", "Period", "Region"] if c in display.columns]
        st.dataframe(display[cols], use_container_width=True, hide_index=True)
