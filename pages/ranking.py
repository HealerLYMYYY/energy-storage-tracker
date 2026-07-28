"""Industry Rankings — Infolink Global ESS Integrator Ranking · 2026E Edition"""

import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_manager import get_rankings
from utils.visualization import ranking_chart


def show_ranking():
    st.markdown('<h1>Industry Rankings</h1>', unsafe_allow_html=True)
    st.caption("Infolink Global ESS Integrator Ranking · DC + AC Combined (GWh)")

    rankings = get_rankings()
    if not rankings:
        st.info("No ranking data available")
        return

    fig = ranking_chart(rankings)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    st.markdown('<h3>Detailed Ranking Data</h3>', unsafe_allow_html=True)
    rows = []
    for i, r in enumerate(rankings):
        g_25 = ((r.get("year_2025") or 0) - (r.get("year_2024") or 0)) / (r.get("year_2024") or 1) * 100 if r.get("year_2024") else 999
        g_26 = ((r.get("year_2026") or 0) - (r.get("year_2025") or 0)) / (r.get("year_2025") or 1) * 100 if r.get("year_2025") else 999
        rank_str = f"#{i+1}"

        row = {
            "Rank": rank_str, "Company": r["company_name"],
            "2024 (GWh)": f'{r.get("year_2024", 0):.1f}',
            "2025 (GWh)": f'{r.get("year_2025", 0):.1f}',
            "Growth 25": f'{g_25:.1f}%' if g_25 < 999 else "NEW",
        }

        # Add 2026E column if available
        if r.get("year_2026") is not None:
            row["2026E (GWh)"] = f'{r.get("year_2026", 0):.1f}'
            row["Growth 26"] = f'{g_26:.1f}%' if g_26 < 999 else "NEW"

        row.update({
            "Americas": f'{r.get("americas", 0):.1f}',
            "EMEA": f'{r.get("emea", 0):.1f}',
            "China": f'{r.get("china", 0):.1f}',
            "APAC": f'{r.get("asia_pacific", 0):.1f}',
        })
        rows.append(row)
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown('<h3>Regional Shipment Mix · 2026E</h3>', unsafe_allow_html=True)
    regions = {"Americas": 0, "EMEA": 0, "China": 0, "APAC": 0}
    for r in rankings:
        regions["Americas"] += r.get("americas") or 0
        regions["EMEA"] += r.get("emea") or 0
        regions["China"] += r.get("china") or 0
        regions["APAC"] += r.get("asia_pacific") or 0

    fig_pie = px.pie(values=list(regions.values()), names=list(regions.keys()),
                     color_discrete_sequence=["#c9a96e", "#5b8db8", "#b8956a", "#7aa3c4"])
    fig_pie.update_layout(margin=dict(l=20, r=20, t=10, b=20),
                          paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#8b949e"))
    st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})
