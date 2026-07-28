"""Sentiment Monitor"""

import streamlit as st
from utils.data_manager import get_competitors


def show_sentiment():
    st.markdown('<h1>Sentiment Monitor</h1>', unsafe_allow_html=True)
    st.caption("Industry keywords: PV · ESS · LiB · NEV · AIDC · Tenders · Project Announcements")

    competitors = get_competitors()

    st.markdown('<h3>Peer News Search</h3>', unsafe_allow_html=True)
    cols = st.columns(3)
    for i, c in enumerate(competitors):
        with cols[i % 3]:
            st.markdown(f"""
            <div style="background:#161b22;border:1px solid #21262d;border-radius:4px;padding:14px;margin-bottom:8px;
                        border-left:3px solid {c['color']}">
                <div style="font-size:0.85rem;font-weight:600;color:#e6edf3;">{c['name']}</div>
                <div style="font-size:0.65rem;color:#8b949e;margin:4px 0;">{c['keywords'][:55]}...</div>
            </div>""", unsafe_allow_html=True)
            st.link_button(f"Search {c['name']}",
                           f"https://news.google.com/search?q={c['name']}+energy+storage&hl=en",
                           use_container_width=True, key=f"sent_{c['cid']}")

    st.divider()
    st.markdown('<h3>Industry News Aggregators</h3>', unsafe_allow_html=True)
    ca, cb, cc = st.columns(3)
    with ca: st.link_button("Google News · ESS", "https://news.google.com/search?q=energy+storage+battery&hl=en", use_container_width=True)
    with cb: st.link_button("BloombergNEF", "https://about.bnef.com/", use_container_width=True)
    with cc: st.link_button("Wood Mackenzie", "https://www.woodmac.com/", use_container_width=True)
    cd, ce = st.columns(2)
    with cd: st.link_button("CNESA", "http://en.cnesa.org/", use_container_width=True)
    with ce: st.link_button("Infolink", "https://www.infolink-group.com/", use_container_width=True)
