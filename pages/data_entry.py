"""Data Entry · 2026E Edition — Forecast Data Input"""

import streamlit as st
import pandas as pd
from utils.data_manager import get_competitors, save_shipment, save_cost, save_financial, get_shipment, get_cost, get_financial
from utils.auth import check_permission


def show_data_entry():
    st.markdown('<h1>Data Operations</h1>', unsafe_allow_html=True)
    st.caption("Enter / update shipment, cost, and financial data · 2026E Forecast Ready")

    if not check_permission("editor"):
        st.warning("Editor or Admin permissions required")
        return

    competitors = get_competitors()
    comp_names = {c["name"]: c for c in competitors}

    col1, col2, col3 = st.columns(3)
    with col1:
        selected_name = st.selectbox("Company", list(comp_names.keys()), key="entry_comp", label_visibility="collapsed")
    with col2:
        period = st.selectbox("Period", [
            "2022", "2023", "2024", "2025",
            "2026E  ← FORECAST",
        ], key="entry_period", label_visibility="collapsed")
    with col3:
        data_type = st.selectbox("Data Type", ["Shipment", "Cost / Pricing", "Financials"], key="entry_type", label_visibility="collapsed")

    # Normalize period
    actual_period = "2026E" if "2026E" in period else period
    is_forecast = (actual_period == "2026E")

    comp = comp_names[selected_name]
    cid = comp["cid"]
    existing_ship = get_shipment(cid).get(actual_period, {})
    existing_cost = get_cost(cid).get(actual_period, {})
    existing_fin = get_financial(cid).get(actual_period, {})

    # ——— Forecast Banner ———
    if is_forecast:
        st.markdown(f"""
        <div style="background:rgba(201,169,110,0.08);border:1px solid rgba(201,169,110,0.25);border-radius:6px;
                    padding:10px 16px;margin-bottom:12px;">
            <span style="color:#c9a96e;font-size:0.85rem;">▨ <strong>2026E Forecast Entry</strong></span>
            <span style="color:#8b949e;font-size:0.72rem;margin-left:8px;">
                Data will render with dashed lines and lighter fills in all charts
            </span>
        </div>""", unsafe_allow_html=True)

    if data_type == "Shipment":
        with st.form("shipment_form"):
            st.markdown(f'<h3>{comp["name"]} · {actual_period} · Shipment Data</h3>', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                total = st.number_input("Total (GWh)", value=existing_ship.get("total") or 0.0, step=0.1, format="%.3f")
                domestic = st.number_input("Domestic (GWh)", value=existing_ship.get("domestic") or 0.0, step=0.1, format="%.3f")
            with c2:
                export = st.number_input("Export (GWh)", value=existing_ship.get("export") or 0.0, step=0.1, format="%.3f")
                residential = st.number_input("Residential (GWh)", value=existing_ship.get("residential") or 0.0, step=0.1, format="%.3f")
            with c3:
                utility = st.number_input("Utility-scale (GWh)", value=existing_ship.get("utility") or 0.0, step=0.1, format="%.3f")
                commercial = st.number_input("C&I (GWh)", value=existing_ship.get("commercial") or 0.0, step=0.1, format="%.3f")
            if st.form_submit_button("Save Shipment Data", use_container_width=True, type="primary"):
                ok, msg = save_shipment(cid, actual_period, {"total": total, "domestic": domestic, "export": export, "residential": residential, "utility": utility, "commercial": commercial})
                st.success(msg) if ok else st.error(msg)

    elif data_type == "Cost / Pricing":
        with st.form("cost_form"):
            st.markdown(f'<h3>{comp["name"]} · {actual_period} · Cost & Pricing</h3>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                sc = st.number_input("System Cost (RMB/Wh)", value=existing_cost.get("system_cost") or 0.0, step=0.001, format="%.3f")
                dp = st.number_input("Domestic ASP (RMB/Wh)", value=existing_cost.get("domestic_price") or 0.0, step=0.001, format="%.3f")
                dm = st.number_input("Domestic GM (%)", value=existing_cost.get("domestic_margin") or 0.0, step=0.1, format="%.1f")
            with c2:
                ep = st.number_input("Export ASP (RMB/Wh)", value=existing_cost.get("export_price") or 0.0, step=0.001, format="%.3f")
                em = st.number_input("Export GM (%)", value=existing_cost.get("export_margin") or 0.0, step=0.1, format="%.1f")
            if st.form_submit_button("Save Cost Data", use_container_width=True, type="primary"):
                ok, msg = save_cost(cid, actual_period, {"system_cost": sc if sc > 0 else None, "domestic_price": dp if dp > 0 else None, "domestic_margin": dm, "export_price": ep if ep > 0 else None, "export_margin": em})
                st.success(msg) if ok else st.error(msg)

    elif data_type == "Financials":
        with st.form("fin_form"):
            st.markdown(f'<h3>{comp["name"]} · {actual_period} · Financials</h3>', unsafe_allow_html=True)

            # Annual totals
            c1, c2 = st.columns(2)
            with c1:
                revenue = st.number_input("Revenue (RMB bn)", value=existing_fin.get("revenue") or 0.0, step=0.01, format="%.2f")
                gross_margin = st.number_input("Gross Margin (%)", value=existing_fin.get("gross_margin") or 0.0, step=0.1, format="%.1f")
                net_profit = st.number_input("Net Profit (RMB bn)", value=existing_fin.get("net_profit") or 0.0, step=0.01, format="%.2f")
                net_margin = st.number_input("Net Margin (%)", value=existing_fin.get("net_margin") or 0.0, step=0.1, format="%.1f")

            # Quarterly breakdown — only relevant for 2026E
            with c2:
                if is_forecast:
                    st.markdown('<span style="color:#c9a96e;font-size:0.7rem;text-transform:uppercase;">Quarterly Forecast</span>', unsafe_allow_html=True)
                rv_q1 = st.number_input("Q1 Revenue", value=existing_fin.get("rv_q1") or 0.0, step=0.01, format="%.2f")
                rv_q2 = st.number_input("Q2 Revenue", value=existing_fin.get("rv_q2") or 0.0, step=0.01, format="%.2f")
                rv_q3 = st.number_input("Q3 Revenue", value=existing_fin.get("rv_q3") or 0.0, step=0.01, format="%.2f")
                rv_q4 = st.number_input("Q4 Revenue", value=existing_fin.get("rv_q4") or 0.0, step=0.01, format="%.2f")

            if st.form_submit_button("Save Financial Data", use_container_width=True, type="primary"):
                ok, msg = save_financial(cid, actual_period, {"revenue": revenue, "gross_margin": gross_margin, "net_profit": net_profit, "net_margin": net_margin, "rv_q1": rv_q1, "rv_q2": rv_q2, "rv_q3": rv_q3, "rv_q4": rv_q4})
                st.success(msg) if ok else st.error(msg)

    st.divider()
    with st.expander("CSV Batch Import"):
        st.markdown("Format: `cid,period,total_gwh,domestic_gwh,export_gwh`")
        st.markdown("Use `2026E` as period for forecast data.")
        uploaded = st.file_uploader("Upload CSV", type="csv")
        if uploaded:
            try:
                df = pd.read_csv(uploaded)
                st.dataframe(df.head(10), use_container_width=True)
                if st.button("Confirm Import"):
                    count = 0
                    for _, row in df.iterrows():
                        if "cid" in df.columns and "period" in df.columns and "total_gwh" in df.columns:
                            save_shipment(row["cid"], str(row["period"]), {"total": row.get("total_gwh"), "domestic": row.get("domestic_gwh"), "export": row.get("export_gwh")})
                            count += 1
                    st.success(f"Imported {count} records")
            except Exception as e:
                st.error(f"Import failed: {e}")
