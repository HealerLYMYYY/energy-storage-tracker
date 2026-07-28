"""行业排名 — Infolink 全球储能集成商排名 · 2026E 预测版"""

import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_manager import get_rankings
from utils.visualization import ranking_chart


def show_ranking():
    st.markdown('<h1>行业排名</h1>', unsafe_allow_html=True)
    st.caption("Infolink 全球储能系统集成商排名 · 直流 + 交流侧合计 (GWh)")

    rankings = get_rankings()
    if not rankings:
        st.info("暂无排名数据")
        return

    fig = ranking_chart(rankings)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    st.markdown('<h3>详细排名数据</h3>', unsafe_allow_html=True)
    rows = []
    for i, r in enumerate(rankings):
        g_25 = ((r.get("year_2025") or 0) - (r.get("year_2024") or 0)) / (r.get("year_2024") or 1) * 100 if r.get("year_2024") else 999
        g_26 = ((r.get("year_2026") or 0) - (r.get("year_2025") or 0)) / (r.get("year_2025") or 1) * 100 if r.get("year_2025") else 999
        rank_str = f"#{i+1}"

        row = {
            "排名": rank_str, "公司": r["company_name"],
            "2024 (GWh)": f'{r.get("year_2024", 0):.1f}',
            "2025 (GWh)": f'{r.get("year_2025", 0):.1f}',
            "2025 增速": f'{g_25:.1f}%' if g_25 < 999 else "NEW",
        }

        if r.get("year_2026") is not None:
            row["2026E (GWh)"] = f'{r.get("year_2026", 0):.1f}'
            row["2026 增速"] = f'{g_26:.1f}%' if g_26 < 999 else "NEW"

        row.update({
            "美洲": f'{r.get("americas", 0):.1f}',
            "EMEA": f'{r.get("emea", 0):.1f}',
            "中国": f'{r.get("china", 0):.1f}',
            "亚太": f'{r.get("asia_pacific", 0):.1f}',
        })
        rows.append(row)
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown('<h3>区域出货结构 · 2026E</h3>', unsafe_allow_html=True)
    regions = {"美洲": 0, "EMEA": 0, "中国": 0, "亚太": 0}
    for r in rankings:
        regions["美洲"] += r.get("americas") or 0
        regions["EMEA"] += r.get("emea") or 0
        regions["中国"] += r.get("china") or 0
        regions["亚太"] += r.get("asia_pacific") or 0

    fig_pie = px.pie(values=list(regions.values()), names=list(regions.keys()),
                     color_discrete_sequence=["#c9a96e", "#5b8db8", "#b8956a", "#7aa3c4"])
    fig_pie.update_layout(margin=dict(l=20, r=20, t=10, b=20),
                          paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#8b949e"))
    st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})
