"""数据录入页"""
import streamlit as st
from utils.data_manager import get_competitors, save_shipment, save_cost, save_financial, get_shipment, get_cost, get_financial
from utils.auth import check_permission


def show_data_entry():
    st.title("📝 数据录入")
    st.caption("录入/更新竞对公司出货量、成本、利润数据")

    if not check_permission("editor"):
        st.warning("您没有编辑权限，请联系管理员")
        return

    competitors = get_competitors()
    comp_names = {c["name"]: c for c in competitors}

    # 选择公司和周期
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_name = st.selectbox("选择公司", list(comp_names.keys()), key="entry_comp")
    with col2:
        period = st.selectbox("选择周期", ["2022", "2023", "2024", "2025", "2026E", "2025Q1", "2025Q2", "2025Q3", "2025Q4"], key="entry_period")
    with col3:
        data_type = st.selectbox("数据类型", ["出货量", "成本/单价", "财务数据"], key="entry_type")

    comp = comp_names[selected_name]
    cid = comp["cid"]

    # 加载现有数据
    existing_ship = get_shipment(cid).get(period, {})
    existing_cost = get_cost(cid).get(period, {})
    existing_fin = get_financial(cid).get(period, {})

    if data_type == "出货量":
        with st.form("shipment_form"):
            st.subheader(f"📦 {comp['name']} - {period} 出货量数据")
            c1, c2, c3 = st.columns(3)
            with c1:
                total = st.number_input("总出货量 (GWh)", value=existing_ship.get("total") or 0.0, step=0.1, format="%.3f")
                domestic = st.number_input("国内出货 (GWh)", value=existing_ship.get("domestic") or 0.0, step=0.1, format="%.3f")
            with c2:
                export = st.number_input("海外出货 (GWh)", value=existing_ship.get("export") or 0.0, step=0.1, format="%.3f")
                residential = st.number_input("户用储能 (GWh)", value=existing_ship.get("residential") or 0.0, step=0.1, format="%.3f")
            with c3:
                utility = st.number_input("大储 (GWh)", value=existing_ship.get("utility") or 0.0, step=0.1, format="%.3f")
                commercial = st.number_input("工商业储能 (GWh)", value=existing_ship.get("commercial") or 0.0, step=0.1, format="%.3f")

            if st.form_submit_button("💾 保存出货量数据", use_container_width=True, type="primary"):
                success, msg = save_shipment(cid, period, {
                    "total": total, "domestic": domestic, "export": export,
                    "residential": residential, "utility": utility, "commercial": commercial
                })
                st.success(msg) if success else st.error(msg)

    elif data_type == "成本/单价":
        with st.form("cost_form"):
            st.subheader(f"💰 {comp['name']} - {period} 成本/单价数据")
            c1, c2 = st.columns(2)
            with c1:
                sc = st.number_input("系统成本 (¥/Wh)", value=existing_cost.get("system_cost") or 0.0, step=0.001, format="%.3f")
                dp = st.number_input("国内单价 (¥/Wh)", value=existing_cost.get("domestic_price") or 0.0, step=0.001, format="%.3f")
                dm = st.number_input("国内毛利率 (%)", value=existing_cost.get("domestic_margin") or 0.0, step=0.1, format="%.1f")
            with c2:
                ep = st.number_input("海外单价 (¥/Wh)", value=existing_cost.get("export_price") or 0.0, step=0.001, format="%.3f")
                em = st.number_input("海外毛利率 (%)", value=existing_cost.get("export_margin") or 0.0, step=0.1, format="%.1f")

            if st.form_submit_button("💾 保存成本数据", use_container_width=True, type="primary"):
                success, msg = save_cost(cid, period, {
                    "system_cost": sc if sc > 0 else None,
                    "domestic_price": dp if dp > 0 else None,
                    "domestic_margin": dm, "export_price": ep if ep > 0 else None,
                    "export_margin": em
                })
                st.success(msg) if success else st.error(msg)

    elif data_type == "财务数据":
        with st.form("fin_form"):
            st.subheader(f"📈 {comp['name']} - {period} 财务数据")
            c1, c2 = st.columns(2)
            with c1:
                revenue = st.number_input("营收 (亿元)", value=existing_fin.get("revenue") or 0.0, step=0.01, format="%.2f")
                gross_margin = st.number_input("毛利率 (%)", value=existing_fin.get("gross_margin") or 0.0, step=0.1, format="%.1f")
                net_profit = st.number_input("净利润 (亿元)", value=existing_fin.get("net_profit") or 0.0, step=0.01, format="%.2f")
                net_margin = st.number_input("净利率 (%)", value=existing_fin.get("net_margin") or 0.0, step=0.1, format="%.1f")
            with c2:
                rv_q1 = st.number_input("Q1营收", value=existing_fin.get("rv_q1") or 0.0, step=0.01, format="%.2f")
                rv_q2 = st.number_input("Q2营收", value=existing_fin.get("rv_q2") or 0.0, step=0.01, format="%.2f")
                rv_q3 = st.number_input("Q3营收", value=existing_fin.get("rv_q3") or 0.0, step=0.01, format="%.2f")
                rv_q4 = st.number_input("Q4营收", value=existing_fin.get("rv_q4") or 0.0, step=0.01, format="%.2f")

            if st.form_submit_button("💾 保存财务数据", use_container_width=True, type="primary"):
                success, msg = save_financial(cid, period, {
                    "revenue": revenue, "gross_margin": gross_margin,
                    "net_profit": net_profit, "net_margin": net_margin,
                    "rv_q1": rv_q1, "rv_q2": rv_q2, "rv_q3": rv_q3, "rv_q4": rv_q4
                })
                st.success(msg) if success else st.error(msg)

    # 批量导入提示
    st.divider()
    with st.expander("📥 CSV 批量导入"):
        st.markdown("""
        **CSV 导入模板格式：**
        ```
        cid,period,total_gwh,domestic_gwh,export_gwh
        catl,2025Q3,35.0,10.0,25.0
        byd,2025Q3,18.0,12.0,6.0
        ```

        上传 CSV 文件后，系统会自动识别并导入数据。具体模板见 `data/template.csv`。
        """)
        uploaded = st.file_uploader("上传 CSV", type="csv")
        if uploaded:
            import pandas as pd
            try:
                df = pd.read_csv(uploaded)
                st.dataframe(df.head(10), use_container_width=True)
                if st.button("确认导入"):
                    count = 0
                    for _, row in df.iterrows():
                        if "cid" in df.columns and "period" in df.columns:
                            if "total_gwh" in df.columns:
                                save_shipment(row["cid"], str(row["period"]), {
                                    "total": row.get("total_gwh"), "domestic": row.get("domestic_gwh"),
                                    "export": row.get("export_gwh")
                                })
                                count += 1
                    st.success(f"成功导入 {count} 条记录")
            except Exception as e:
                st.error(f"导入失败: {e}")
