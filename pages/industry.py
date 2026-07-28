"""Macro & Supply Chain — Industry-level Data · 2026E Edition"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from utils.data_manager import get_industry_data
from utils.visualization import hex_to_rgba, FORECAST_PERIOD

FORECAST_BAR_ALPHA = 0.50


def show_industry():
    st.markdown('<h1>Macro & Supply Chain</h1>', unsafe_allow_html=True)
    st.caption("Global PV · ESS · Li-ion Battery Shipment & Cost Trends · 2026E Forecast")

    region = st.selectbox("Region", ["全球", "北美", "中国", "欧洲", "亚太", "拉美", "中东非"], key="ind_region",
                          label_visibility="collapsed")

    pv_data = get_industry_data("光伏", region)
    ess_data = get_industry_data("储能", region)
    lith_data = get_industry_data("锂电池", region)

    # KPI: use latest available (prefer 2026E)
    pv_2026 = next((d["metric_value"] for d in pv_data if d["period"] == "2026E" and "光伏出货" in d["metric_name"]), 0)
    ess_2026 = next((d["metric_value"] for d in ess_data if d["period"] == "2026E" and "储能出货" in d["metric_name"]), 0)
    lith_2026 = next((d["metric_value"] for d in lith_data if d["period"] == "2026E" and "锂电池出货" in d["metric_name"]), 0)
    cost_2026 = next((d["metric_value"] for d in ess_data if d["period"] == "2026E" and d["metric_name"] == "系统成本"), 0)

    # Fallback to 2025 if no 2026E data
    if not pv_2026:
        pv_2026 = next((d["metric_value"] for d in pv_data if d["period"] == "2025" and "光伏出货" in d["metric_name"]), 0)
    if not ess_2026:
        ess_2026 = next((d["metric_value"] for d in ess_data if d["period"] == "2025" and "储能出货" in d["metric_name"]), 0)
    if not lith_2026:
        lith_2026 = next((d["metric_value"] for d in lith_data if d["period"] == "2025" and "锂电池出货" in d["metric_name"]), 0)
    if not cost_2026:
        cost_2026 = next((d["metric_value"] for d in ess_data if d["period"] == "2025" and d["metric_name"] == "系统成本"), 0)

    has_2026 = any(d["period"] == "2026E" for d in ess_data)

    k1, k2, k3, k4 = st.columns(4)
    with k1: st.metric("PV Shipment 2026E", f"{pv_2026} GW")
    with k2: st.metric("ESS Shipment 2026E", f"{ess_2026} GWh")
    with k3: st.metric("LiB Shipment 2026E", f"{lith_2026} GWh")
    with k4: st.metric("System Cost 2026E", f"¥{cost_2026:.2f}/Wh")

    st.divider()

    years = ["2020", "2021", "2022", "2023", "2024", "2025"]
    if has_2026:
        years.append("2026E")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<h3>PV + ESS Shipment Growth</h3>', unsafe_allow_html=True)
        pv_vals = [next((d["metric_value"] for d in pv_data if d["period"] == y and "光伏出货" in d["metric_name"]), None) for y in years]
        ess_vals = [next((d["metric_value"] for d in ess_data if d["period"] == y and "储能出货" in d["metric_name"]), None) for y in years]

        # Split into historical + forecast bars
        hist_years = [y for y in years if y != "2026E"]
        fcst_years = [y for y in years if y == "2026E"]

        fig = go.Figure()
        # Historical bars
        pv_hist = [pv_vals[i] for i, y in enumerate(years) if y != "2026E"]
        ess_hist = [ess_vals[i] for i, y in enumerate(years) if y != "2026E"]
        fig.add_trace(go.Bar(name="PV (GW)", x=hist_years, y=pv_hist, marker_color="rgba(201,169,110,0.8)"))
        fig.add_trace(go.Bar(name="ESS (GWh)", x=hist_years, y=ess_hist, marker_color="rgba(91,141,184,0.8)"))

        # Forecast bars (lighter)
        if fcst_years:
            pv_fcst = [pv_vals[i] for i, y in enumerate(years) if y == "2026E"]
            ess_fcst = [ess_vals[i] for i, y in enumerate(years) if y == "2026E"]
            fig.add_trace(go.Bar(name="PV (GW) 2026E", x=fcst_years, y=pv_fcst,
                                 marker_color=f"rgba(201,169,110,{FORECAST_BAR_ALPHA})",
                                 marker_line=dict(width=1.5, color="rgba(201,169,110,0.5)")))
            fig.add_trace(go.Bar(name="ESS (GWh) 2026E", x=fcst_years, y=ess_fcst,
                                 marker_color=f"rgba(91,141,184,{FORECAST_BAR_ALPHA})",
                                 marker_line=dict(width=1.5, color="rgba(91,141,184,0.5)")))

        fig.update_layout(barmode="group", margin=dict(l=20, r=20, t=10, b=20),
                          plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                          font=dict(color="#8b949e"), legend=dict(font=dict(color="#8b949e")))
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    with col2:
        st.markdown('<h3>LiB Shipment & Lithium Carbonate Price</h3>', unsafe_allow_html=True)
        lith_vals = [next((d["metric_value"] for d in lith_data if d["period"] == y and "锂电池出货" in d["metric_name"]), None) for y in years]
        price_vals = [next((d["metric_value"] for d in lith_data if d["period"] == y and "碳酸锂" in d["metric_name"]), None) for y in years]

        fig2 = go.Figure()
        # Historical LiB bars
        lith_hist = [lith_vals[i] for i, y in enumerate(years) if y != "2026E"]
        fig2.add_trace(go.Bar(name="LiB (GWh)", x=hist_years, y=lith_hist, marker_color="rgba(91,141,184,0.8)"))

        # Forecast LiB bars
        if fcst_years:
            lith_fcst = [lith_vals[i] for i, y in enumerate(years) if y == "2026E"]
            fig2.add_trace(go.Bar(name="LiB (GWh) 2026E", x=fcst_years, y=lith_fcst,
                                  marker_color=f"rgba(91,141,184,{FORECAST_BAR_ALPHA})",
                                  marker_line=dict(width=1.5, color="rgba(91,141,184,0.5)")))

        # Price line — split historical + forecast
        price_hist = [price_vals[i] for i, y in enumerate(years) if y != "2026E"]
        fig2.add_trace(go.Scatter(x=hist_years, y=price_hist, name="Li₂CO₃ Price",
                                  yaxis="y2", line=dict(color="#c9a96e", width=2.5), mode="lines+markers"))
        if fcst_years:
            price_fcst = [price_vals[i] for i, y in enumerate(years) if y == "2026E"]
            fcst_x = [hist_years[-1]] + fcst_years if hist_years else fcst_years
            fcst_y = [price_hist[-1]] + price_fcst if price_hist else price_fcst
            fig2.add_trace(go.Scatter(x=fcst_x, y=fcst_y, name="Li₂CO₃ Price (E)",
                                      yaxis="y2", line=dict(color="#c9a96e", width=2.5, dash="dash"),
                                      mode="lines+markers",
                                      marker=dict(size=5, color="rgba(201,169,110,0.5)")))

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
        # Historical cost line
        cost_hist = [cost_vals[i] for i, y in enumerate(years) if y != "2026E"]
        fig3.add_trace(go.Scatter(x=hist_years, y=cost_hist, name="System Cost",
                                  line=dict(color="#c9a96e", width=2.5), mode="lines+markers",
                                  fill="tozeroy", fillcolor="rgba(201,169,110,0.08)", marker=dict(size=8)))

        # Forecast cost line
        if fcst_years:
            cost_fcst = [cost_vals[i] for i, y in enumerate(years) if y == "2026E"]
            fcst_x = [hist_years[-1]] + fcst_years if hist_years else fcst_years
            fcst_y = [cost_hist[-1]] + cost_fcst if cost_hist else cost_fcst
            fig3.add_trace(go.Scatter(x=fcst_x, y=fcst_y, name="System Cost (E)",
                                      line=dict(color="#c9a96e", width=2.5, dash="dash"),
                                      mode="lines+markers",
                                      marker=dict(size=8, color="rgba(201,169,110,0.5)"),
                                      fill="tozeroy", fillcolor="rgba(201,169,110,0.03)"))

        fig3.update_layout(margin=dict(l=20, r=20, t=10, b=20),
                           plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                           font=dict(color="#8b949e"))
        st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': False})

    with col4:
        st.markdown('<h3>Regional ESS Mix · 2026E</h3>', unsafe_allow_html=True)
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
