"""数据录入 · 2026E 预测版"""

import streamlit as st
import pandas as pd
from utils.data_manager import get_competitors, save_shipment, save_cost, save_financial, get_shipment, get_cost, get_financial
from utils.auth import check_permission


def show_data_entry():
    st.markdown('<h1>数据操作</h1>', unsafe_allow_html=True)
    st.caption("录入 / 更新 出货量、成本、财务数据 · 支持 2026E 预测数据")

    if not check_permission("editor"):
        st.warning("需要编辑员或管理员权限")
        return

    competitors = get_competitors()
    comp_names = {c["name"]: c for c in competitors}

    col1, col2, col3 = st.columns(3)
    with col1:
        selected_name = st.selectbox("公司", list(comp_names.keys()), key="entry_comp", label_visibility="collapsed")
    with col2:
        period = st.selectbox("周期", [
            "2022", "2023", "2024", "2025",
            "2026E  ← 预测",
        ], key="entry_period", label_visibility="collapsed")
    with col3:
        data_type = st.selectbox("数据类型", ["出货量", "成本 / 价格", "财务"], key="entry_type", label_visibility="collapsed")

    # 标准化 period
    actual_period = "2026E" if "2026E" in period else period
    is_forecast = (actual_period == "2026E")

    comp = comp_names[selected_name]
    cid = comp["cid"]
    existing_ship = get_shipment(cid).get(actual_period, {})
    existing_cost = get_cost(cid).get(actual_period, {})
    existing_fin = get_financial(cid).get(actual_period, {})

    # ——— 预测提示 ———
    if is_forecast:
        st.markdown(f"""
        <div style="background:rgba(201,169,110,0.08);border:1px solid rgba(201,169,110,0.25);border-radius:6px;
                    padding:10px 16px;margin-bottom:12px;">
            <span style="color:#c9a96e;font-size:0.85rem;">▨ <strong>2026E 预测录入</strong></span>
            <span style="color:#8b949e;font-size:0.72rem;margin-left:8px;">
                数据将在所有图表中以虚线和浅色填充/柱状图显示
            </span>
        </div>""", unsafe_allow_html=True)

    if data_type == "出货量":
        with st.form("shipment_form"):
            st.markdown(f'<h3>{comp["name"]} · {actual_period} · 出货量数据</h3>', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                total = st.number_input("总量 (GWh)", value=existing_ship.get("total") or 0.0, step=0.1, format="%.3f")
                domestic = st.number_input("国内 (GWh)", value=existing_ship.get("domestic") or 0.0, step=0.1, format="%.3f")
            with c2:
                export = st.number_input("海外 (GWh)", value=existing_ship.get("export") or 0.0, step=0.1, format="%.3f")
                residential = st.number_input("户用 (GWh)", value=existing_ship.get("residential") or 0.0, step=0.1, format="%.3f")
            with c3:
                utility = st.number_input("大储 (GWh)", value=existing_ship.get("utility") or 0.0, step=0.1, format="%.3f")
                commercial = st.number_input("工商业 (GWh)", value=existing_ship.get("commercial") or 0.0, step=0.1, format="%.3f")
            if st.form_submit_button("保存出货量", use_container_width=True, type="primary"):
                ok, msg = save_shipment(cid, actual_period, {"total": total, "domestic": domestic, "export": export, "residential": residential, "utility": utility, "commercial": commercial})
                st.success(msg) if ok else st.error(msg)

    elif data_type == "成本 / 价格":
        with st.form("cost_form"):
            st.markdown(f'<h3>{comp["name"]} · {actual_period} · 成本与价格</h3>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                sc = st.number_input("系统成本 (元/Wh)", value=existing_cost.get("system_cost") or 0.0, step=0.001, format="%.3f")
                dp = st.number_input("国内均价 (元/Wh)", value=existing_cost.get("domestic_price") or 0.0, step=0.001, format="%.3f")
                dm = st.number_input("国内毛利率 (%)", value=existing_cost.get("domestic_margin") or 0.0, step=0.1, format="%.1f")
            with c2:
                ep = st.number_input("海外均价 (元/Wh)", value=existing_cost.get("export_price") or 0.0, step=0.001, format="%.3f")
                em = st.number_input("海外毛利率 (%)", value=existing_cost.get("export_margin") or 0.0, step=0.1, format="%.1f")
            if st.form_submit_button("保存成本数据", use_container_width=True, type="primary"):
                ok, msg = save_cost(cid, actual_period, {"system_cost": sc if sc > 0 else None, "domestic_price": dp if dp > 0 else None, "domestic_margin": dm, "export_price": ep if ep > 0 else None, "export_margin": em})
                st.success(msg) if ok else st.error(msg)

    elif data_type == "财务":
        with st.form("fin_form"):
            st.markdown(f'<h3>{comp["name"]} · {actual_period} · 财务数据</h3>', unsafe_allow_html=True)

            # 年度汇总
            c1, c2 = st.columns(2)
            with c1:
                revenue = st.number_input("营收 (亿元)", value=existing_fin.get("revenue") or 0.0, step=0.01, format="%.2f")
                gross_margin = st.number_input("毛利率 (%)", value=existing_fin.get("gross_margin") or 0.0, step=0.1, format="%.1f")
                net_profit = st.number_input("净利润 (亿元)", value=existing_fin.get("net_profit") or 0.0, step=0.01, format="%.2f")
                net_margin = st.number_input("净利率 (%)", value=existing_fin.get("net_margin") or 0.0, step=0.1, format="%.1f")

            # 季度拆分 —— 仅 2026E 显示
            with c2:
                if is_forecast:
                    st.markdown('<span style="color:#c9a96e;font-size:0.7rem;text-transform:uppercase;">季度预测</span>', unsafe_allow_html=True)
                rv_q1 = st.number_input("Q1 营收", value=existing_fin.get("rv_q1") or 0.0, step=0.01, format="%.2f")
                rv_q2 = st.number_input("Q2 营收", value=existing_fin.get("rv_q2") or 0.0, step=0.01, format="%.2f")
                rv_q3 = st.number_input("Q3 营收", value=existing_fin.get("rv_q3") or 0.0, step=0.01, format="%.2f")
                rv_q4 = st.number_input("Q4 营收", value=existing_fin.get("rv_q4") or 0.0, step=0.01, format="%.2f")

            if st.form_submit_button("保存财务数据", use_container_width=True, type="primary"):
                ok, msg = save_financial(cid, actual_period, {"revenue": revenue, "gross_margin": gross_margin, "net_profit": net_profit, "net_margin": net_margin, "rv_q1": rv_q1, "rv_q2": rv_q2, "rv_q3": rv_q3, "rv_q4": rv_q4})
                st.success(msg) if ok else st.error(msg)

    st.divider()
    with st.expander("CSV 批量导入"):
        st.markdown("格式：`cid,period,total_gwh,domestic_gwh,export_gwh`")
        st.markdown("预测数据请使用 `2026E` 作为周期。")
        uploaded = st.file_uploader("上传 CSV", type="csv")
        if uploaded:
            try:
                df = pd.read_csv(uploaded)
                st.dataframe(df.head(10), use_container_width=True)
                if st.button("确认导入"):
                    count = 0
                    for _, row in df.iterrows():
                        if "cid" in df.columns and "period" in df.columns and "total_gwh" in df.columns:
                            save_shipment(row["cid"], str(row["period"]), {"total": row.get("total_gwh"), "domestic": row.get("domestic_gwh"), "export": row.get("export_gwh")})
                            count += 1
                    st.success(f"已导入 {count} 条记录")
            except Exception as e:
                st.error(f"导入失败: {e}")
