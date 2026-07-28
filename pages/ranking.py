"""Industry Rankings — Infolink Global ESS Integrator Ranking"""

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
        g = ((r["year_2025"] or 0) - (r["year_2024"] or 0)) / (r["year_2024"] or 1) * 100 if r["year_2024"] else 999
        rank_str = f"#{i+1}"
        rows.append({
            "Rank": rank_str, "Company": r["company_name"],
            "2024 (GWh)": f'{r["year_2024"]:.1f}', "2025E (GWh)": f'{r["year_2025"]:.1f}',
            "Growth": f'{g:.1f}%' if g < 999 else "NEW",
            "Americas": f'{r["americas"]:.1f}', "EMEA": f'{r["emea"]:.1f}',
            "China": f'{r["china"]:.1f}', "APAC": f'{r["asia_pacific"]:.1f}',
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown('<h3>Regional Shipment Mix · 2025E</h3>', unsafe_allow_html=True)
    regions = {"Americas": 0, "EMEA": 0, "China": 0, "APAC": 0}
    for r in rankings:
        regions["Americas"] += r["americas"] or 0
        regions["EMEA"] += r["emea"] or 0
        regions["China"] += r["china"] or 0
        regions["APAC"] += r["asia_pacific"] or 0

    fig_pie = px.pie(values=list(regions.values()), names=list(regions.keys()),
                     color_discrete_sequence=["#c9a96e", "#5b8db8", "#b8956a", "#7aa3c4"])
    fig_pie.update_layout(margin=dict(l=20, r=20, t=10, b=20),
                          paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#8b949e"))
    st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})
