"""行业数据页 - 光伏/储能/锂电池趋势"""
import streamlit as st
import pandas as pd
from utils.data_manager import get_industry_data
import plotly.graph_objects as go


def show_industry():
    st.title("🌐 光储行业数据")
    st.caption("全球光伏 · 储能 · 锂电池出货量与成本趋势")

    region = st.selectbox("选择区域", ["全球", "北美", "中国", "欧洲", "亚太", "拉美", "中东非"],
                          key="ind_region")

    # KPI 卡片
    pv_data = get_industry_data("光伏", region)
    ess_data = get_industry_data("储能", region)
    lith_data = get_industry_data("锂电池", region)

    pv_2025 = next((d["metric_value"] for d in pv_data if d["period"] == "2025" and d["metric_name"] == "全球光伏出货量"), 0)
    ess_2025 = next((d["metric_value"] for d in ess_data if d["period"] == "2025" and d["metric_name"] == "全球储能出货量"), 0)
    lith_2025 = next((d["metric_value"] for d in lith_data if d["period"] == "2025" and d["metric_name"] == "全球锂电池出货量"), 0)
    cost_2025 = next((d["metric_value"] for d in ess_data if d["period"] == "2025" and d["metric_name"] == "系统成本"), 0)

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("光伏出货", f"{pv_2025} GW")
    with k2:
        st.metric("储能出货", f"{ess_2025} GWh")
    with k3:
        st.metric("锂电池出货", f"{lith_2025} GWh")
    with k4:
        st.metric("系统成本", f"¥{cost_2025:.2f}/Wh")

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("光伏 + 储能出货量")
        years = ["2020", "2021", "2022", "2023", "2024", "2025"]
        pv_vals = [next((d["metric_value"] for d in pv_data if d["period"] == y and d["metric_name"] == "全球光伏出货量"), None) for y in years]
        ess_vals = [next((d["metric_value"] for d in ess_data if d["period"] == y and d["metric_name"] == "全球储能出货量"), None) for y in years]

        fig = go.Figure(data=[
            go.Bar(name="光伏(GW)", x=years, y=pv_vals, marker_color="rgba(255,123,0,0.7)"),
            go.Bar(name="储能(GWh)", x=years, y=ess_vals, marker_color="rgba(84,184,107,0.7)")
        ])
        fig.update_layout(barmode="group", margin=dict(l=20, r=20, t=10, b=20),
                          plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("锂电池出货 + 价格趋势")
        lith_vals = [next((d["metric_value"] for d in lith_data if d["period"] == y and d["metric_name"] == "全球锂电池出货量"), None) for y in years]
        price_vals = [next((d["metric_value"] for d in lith_data if d["period"] == y and d["metric_name"] == "碳酸锂价格"), None) for y in years]

        fig2 = go.Figure(data=[
            go.Bar(name="锂电池出货(GWh)", x=years, y=lith_vals, marker_color="rgba(85,184,180,0.7)"),
        ])
        fig2.add_trace(go.Scatter(x=years, y=price_vals, name="碳酸锂价格(万元/吨)",
                                  yaxis="y2", line=dict(color="#e85d75", width=2.5), mode="lines+markers"))
        fig2.update_layout(yaxis2=dict(overlaying="y", side="right"),
                           margin=dict(l=20, r=20, t=10, b=20),
                           plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("系统成本下降趋势")
        cost_vals = [next((d["metric_value"] for d in ess_data if d["period"] == y and d["metric_name"] == "系统成本"), None) for y in years]
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=years, y=cost_vals, name="系统成本(¥/Wh)",
                                  line=dict(color="#55b8b4", width=2.5), mode="lines+markers",
                                  fill="tozeroy", fillcolor="rgba(85,184,180,0.1)", marker=dict(size=8)))
        fig3.update_layout(margin=dict(l=20, r=20, t=10, b=20),
                           plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.subheader("区域储能出货量占比 (2025)")
        # 模拟区域数据
        region_data = {"北美": 95, "中国": 130, "欧洲": 55, "亚太": 18, "拉美": 7, "中东非": 5}
        import plotly.express as px
        fig4 = px.pie(values=list(region_data.values()), names=list(region_data.keys()),
                      color_discrete_sequence=["#ff7b00", "#54b86b", "#55b8b4", "#6e8efb", "#f5a623", "#e85d75"])
        fig4.update_layout(margin=dict(l=20, r=20, t=10, b=20))
        st.plotly_chart(fig4, use_container_width=True)

    # 数据表
    st.subheader("📋 行业数据明细")
    all_ind = get_industry_data(region=region)
    if all_ind:
        df = pd.DataFrame(all_ind)
        display = df.rename(columns={
            "category": "类别", "metric_name": "指标", "metric_value": "数值",
            "unit": "单位", "period": "期间", "region": "区域"
        })
        cols = [c for c in ["类别", "指标", "数值", "单位", "期间", "区域"] if c in display.columns]
        st.dataframe(display[cols], use_container_width=True, hide_index=True)
