"""行业排名页 - Infolink 全球储能系统集成商排名"""
import streamlit as st
import pandas as pd
from utils.data_manager import get_rankings
from utils.visualization import ranking_chart


def show_ranking():
    st.title("🏆 行业排名")
    st.caption("Infolink 全球储能系统集成商排名 | 2024→2025 直流+交流侧合计 (GWh)")

    rankings = get_rankings()

    if not rankings:
        st.info("暂无排名数据")
        return

    # 排名图表
    fig = ranking_chart(rankings)
    st.plotly_chart(fig, use_container_width=True)

    # 排名表格
    st.subheader("📋 详细排名数据")
    rows = []
    for i, r in enumerate(rankings):
        g = ((r["year_2025"] or 0) - (r["year_2024"] or 0)) / (r["year_2024"] or 1) * 100 if r["year_2024"] else 999
        rank_icon = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"#{i+1}"
        rows.append({
            "排名": rank_icon,
            "公司": r["company_name"],
            "2024 (GWh)": f'{r["year_2024"]:.1f}',
            "2025 (GWh)": f'{r["year_2025"]:.1f}',
            "增速": f'{g:.1f}%' if g < 999 else "NEW",
            "美洲": f'{r["americas"]:.1f}',
            "EMEA": f'{r["emea"]:.1f}',
            "中国": f'{r["china"]:.1f}',
            "亚太": f'{r["asia_pacific"]:.1f}',
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # 区域占比分析
    st.subheader("🌍 区域出货量占比 (2025)")
    regions = {"美洲": 0, "EMEA": 0, "中国": 0, "亚太": 0}
    for r in rankings:
        regions["美洲"] += r["americas"] or 0
        regions["EMEA"] += r["emea"] or 0
        regions["中国"] += r["china"] or 0
        regions["亚太"] += r["asia_pacific"] or 0

    import plotly.express as px
    fig_pie = px.pie(values=list(regions.values()), names=list(regions.keys()),
                     title="区域出货分布", color_discrete_sequence=["#ff7b00", "#54b86b", "#55b8b4", "#6e8efb"])
    fig_pie.update_layout(margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig_pie, use_container_width=True)
