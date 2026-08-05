"""数据录入 — 出货量 · 成本 · 财务 · 行业数据 · 排名"""

import streamlit as st
import pandas as pd
from utils.data_manager import (get_competitors, save_shipment, save_cost, save_financial,
                                get_shipment, get_cost, get_financial,
                                save_industry_data, delete_industry_data, get_industry_data, get_industry_categories,
                                save_ranking, delete_ranking, get_rankings)
from utils.auth import check_permission


def show_data_entry():
    st.markdown('<h1>数据操作</h1>', unsafe_allow_html=True)
    st.caption("录入 / 更新 出货量、成本、财务、行业数据、排名")

    if not check_permission("editor"):
        st.warning("需要编辑员或管理员权限")
        return

    competitors = get_competitors()
    comp_names = {c["name"]: c for c in competitors}

    col1, col2, col3 = st.columns(3)
    with col1:
        selected_name = st.selectbox("公司", list(comp_names.keys()), key="entry_comp")
    with col2:
        period = st.selectbox("周期", [
            "2022", "2023", "2024", "2025",
            "2026E  ← 预测",
        ], key="entry_period")
    with col3:
        data_type = st.selectbox("数据类型", [
            "出货量", "成本 / 价格", "财务",
            "行业数据", "行业排名",
        ], key="entry_type")

    actual_period = "2026E" if "2026E" in period else period
    is_forecast = (actual_period == "2026E")

    # ——— 公司相关的数据录入 ———
    if data_type in ("出货量", "成本 / 价格", "财务"):
        comp = comp_names[selected_name]
        cid = comp["cid"]
        existing_ship = get_shipment(cid).get(actual_period, {})
        existing_cost = get_cost(cid).get(actual_period, {})
        existing_fin = get_financial(cid).get(actual_period, {})

        if is_forecast:
            st.markdown(f"""
            <div style="background:rgba(201,112,42,0.06);border:1px solid rgba(201,112,42,0.2);border-radius:6px;
                        padding:10px 16px;margin-bottom:12px;">
                <span style="color:#C9702A;font-size:0.85rem;">▨ <strong>2026E 预测录入</strong></span>
                <span style="color:#6b7280;font-size:0.72rem;margin-left:8px;">
                    数据将在所有图表中以虚线和浅色填充显示
                </span>
            </div>""", unsafe_allow_html=True)

        if data_type == "出货量":
            _show_shipment_form(comp, actual_period, existing_ship, cid)
        elif data_type == "成本 / 价格":
            _show_cost_form(comp, actual_period, existing_cost, cid)
        elif data_type == "财务":
            _show_financial_form(comp, actual_period, existing_fin, cid, is_forecast)

    # ——— 行业数据录入 ———
    elif data_type == "行业数据":
        _show_industry_form()

    # ——— 行业排名录入 ———
    elif data_type == "行业排名":
        _show_ranking_form()

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


# ——— 出货量表单 ———
def _show_shipment_form(comp, actual_period, existing, cid):
    with st.form("shipment_form"):
        st.markdown(f'<h3>{comp["name"]} · {actual_period} · 出货量数据</h3>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            total = st.number_input("总量 (GWh)", value=existing.get("total") or 0.0, step=0.1, format="%.3f")
            domestic = st.number_input("国内 (GWh)", value=existing.get("domestic") or 0.0, step=0.1, format="%.3f")
        with c2:
            export = st.number_input("海外 (GWh)", value=existing.get("export") or 0.0, step=0.1, format="%.3f")
            residential = st.number_input("户用 (GWh)", value=existing.get("residential") or 0.0, step=0.1, format="%.3f")
        with c3:
            utility = st.number_input("大储 (GWh)", value=existing.get("utility") or 0.0, step=0.1, format="%.3f")
            commercial = st.number_input("工商业 (GWh)", value=existing.get("commercial") or 0.0, step=0.1, format="%.3f")
        if st.form_submit_button("保存出货量", use_container_width=True, type="primary"):
            ok, msg = save_shipment(cid, actual_period, {"total": total, "domestic": domestic, "export": export, "residential": residential, "utility": utility, "commercial": commercial})
            st.success(msg) if ok else st.error(msg)


# ——— 成本表单 ———
def _show_cost_form(comp, actual_period, existing, cid):
    with st.form("cost_form"):
        st.markdown(f'<h3>{comp["name"]} · {actual_period} · 成本与价格</h3>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            sc = st.number_input("系统成本 (元/Wh)", value=existing.get("system_cost") or 0.0, step=0.001, format="%.3f")
            dp = st.number_input("国内均价 (元/Wh)", value=existing.get("domestic_price") or 0.0, step=0.001, format="%.3f")
            dm = st.number_input("国内毛利率 (%)", value=existing.get("domestic_margin") or 0.0, step=0.1, format="%.1f")
        with c2:
            ep = st.number_input("海外均价 (元/Wh)", value=existing.get("export_price") or 0.0, step=0.001, format="%.3f")
            em = st.number_input("海外毛利率 (%)", value=existing.get("export_margin") or 0.0, step=0.1, format="%.1f")
        if st.form_submit_button("保存成本数据", use_container_width=True, type="primary"):
            ok, msg = save_cost(cid, actual_period, {"system_cost": sc if sc > 0 else None, "domestic_price": dp if dp > 0 else None, "domestic_margin": dm, "export_price": ep if ep > 0 else None, "export_margin": em})
            st.success(msg) if ok else st.error(msg)


# ——— 财务表单 ———
def _show_financial_form(comp, actual_period, existing, cid, is_forecast):
    with st.form("fin_form"):
        st.markdown(f'<h3>{comp["name"]} · {actual_period} · 财务数据</h3>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            revenue = st.number_input("营收 (亿元)", value=existing.get("revenue") or 0.0, step=0.01, format="%.2f")
            gross_margin = st.number_input("毛利率 (%)", value=existing.get("gross_margin") or 0.0, step=0.1, format="%.1f")
            net_profit = st.number_input("净利润 (亿元)", value=existing.get("net_profit") or 0.0, step=0.01, format="%.2f")
            net_margin = st.number_input("净利率 (%)", value=existing.get("net_margin") or 0.0, step=0.1, format="%.1f")
        with c2:
            if is_forecast:
                st.markdown('<span style="color:#C9702A;font-size:0.7rem;text-transform:uppercase;">季度预测</span>', unsafe_allow_html=True)
            rv_q1 = st.number_input("Q1 营收", value=existing.get("rv_q1") or 0.0, step=0.01, format="%.2f")
            rv_q2 = st.number_input("Q2 营收", value=existing.get("rv_q2") or 0.0, step=0.01, format="%.2f")
            rv_q3 = st.number_input("Q3 营收", value=existing.get("rv_q3") or 0.0, step=0.01, format="%.2f")
            rv_q4 = st.number_input("Q4 营收", value=existing.get("rv_q4") or 0.0, step=0.01, format="%.2f")
        if st.form_submit_button("保存财务数据", use_container_width=True, type="primary"):
            ok, msg = save_financial(cid, actual_period, {"revenue": revenue, "gross_margin": gross_margin, "net_profit": net_profit, "net_margin": net_margin, "rv_q1": rv_q1, "rv_q2": rv_q2, "rv_q3": rv_q3, "rv_q4": rv_q4})
            st.success(msg) if ok else st.error(msg)


# ——— 行业数据录入 ———
def _show_industry_form():
    st.markdown('<h3>行业数据录入</h3>', unsafe_allow_html=True)

    # 模式：新增 or 编辑已有
    mode = st.radio("模式", ["新增数据", "查看 / 编辑 / 删除已有"], horizontal=True, key="ind_mode")

    if mode == "新增数据":
        with st.form("industry_add_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                # 从已有数据提取可选类别
                cats = get_industry_categories()
                cat_options = sorted(set(c["category"] for c in cats)) if cats else ["光伏", "储能", "锂电池"]
                category = st.selectbox("类别", cat_options, key="ind_cat") if cat_options else st.text_input("类别", key="ind_cat_text")
                if not cat_options:
                    category = st.text_input("类别", key="ind_cat_text")
                metric_name = st.text_input("指标名称", placeholder="如: 全球储能出货量", key="ind_metric")
            with c2:
                metric_value = st.number_input("数值", step=0.01, format="%.2f", key="ind_value")
                unit = st.text_input("单位", placeholder="GWh / GW / ¥/Wh / 万元/吨", key="ind_unit")
            with c3:
                period = st.selectbox("周期", ["2020", "2021", "2022", "2023", "2024", "2025", "2026E"], key="ind_period")
                region = st.text_input("区域", value="全球", key="ind_region")
            notes = st.text_input("备注 (可选)", placeholder="数据来源或说明", key="ind_notes")

            if st.form_submit_button("保存行业数据", use_container_width=True, type="primary"):
                if not category or not metric_name or not unit:
                    st.error("类别、指标名称和单位不能为空")
                elif metric_value == 0.0:
                    st.error("请输入有效数值")
                else:
                    ok, msg = save_industry_data(category, metric_name, metric_value, unit, period, region, notes or None)
                    st.success(msg) if ok else st.error(msg)

    else:
        # 查看已有数据，支持编辑和删除
        existing = get_industry_data()
        if not existing:
            st.info("暂无行业数据，请先新增。")
            return

        # 按类别分组展示
        st.markdown("点击行末按钮编辑或删除对应记录：")
        df = pd.DataFrame(existing)
        # 只显示关键列
        display_cols = [c for c in ["id", "category", "metric_name", "period", "region", "metric_value", "unit"] if c in df.columns]
        st.dataframe(df[display_cols], use_container_width=True, hide_index=True)

        # 删除
        st.markdown("---")
        st.markdown('<span style="font-size:0.75rem;color:#6b7280;">删除记录（输入 ID）</span>', unsafe_allow_html=True)
        del_id = st.number_input("要删除的记录 ID", step=1, min_value=1, key="ind_del_id")
        if st.button("删除该记录", type="secondary"):
            ok, msg = delete_industry_data(del_id)
            st.success(msg) if ok else st.error(msg)
            st.rerun()

        # 编辑已有
        st.markdown("---")
        st.markdown('<span style="font-size:0.75rem;color:#6b7280;">编辑记录（输入 ID 并修改字段）</span>', unsafe_allow_html=True)
        edit_id = st.number_input("要编辑的记录 ID", step=1, min_value=1, key="ind_edit_id")
        target = next((r for r in existing if r["id"] == edit_id), None)
        if target:
            with st.form("industry_edit_form"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    new_cat = st.text_input("类别", value=target["category"], key="ind_edit_cat")
                    new_metric = st.text_input("指标名称", value=target["metric_name"], key="ind_edit_metric")
                with c2:
                    new_val = st.number_input("数值", value=float(target["metric_value"] or 0), step=0.01, format="%.2f", key="ind_edit_val")
                    new_unit = st.text_input("单位", value=target.get("unit", ""), key="ind_edit_unit")
                with c3:
                    new_period = st.text_input("周期", value=target["period"], key="ind_edit_period")
                    new_region = st.text_input("区域", value=target.get("region", "全球"), key="ind_edit_region")
                new_notes = st.text_input("备注", value=target.get("notes") or "", key="ind_edit_notes")
                if st.form_submit_button("更新该记录", use_container_width=True, type="primary"):
                    ok, msg = save_industry_data(new_cat, new_metric, new_val, new_unit, new_period, new_region, new_notes or None)
                    st.success(msg) if ok else st.error(msg)
        else:
            if edit_id > 0:
                st.warning(f"未找到 ID={edit_id} 的记录")


# ——— 行业排名录入 ———
def _show_ranking_form():
    st.markdown('<h3>行业排名录入</h3>', unsafe_allow_html=True)

    mode = st.radio("模式", ["新增 / 编辑", "查看 / 删除已有"], horizontal=True, key="rk_mode")

    if mode == "新增 / 编辑":
        with st.form("ranking_form"):
            st.markdown('<span style="font-size:0.75rem;color:#6b7280;">输入公司名后，系统自动检测是新增还是更新。</span>', unsafe_allow_html=True)
            company_name = st.text_input("公司名称", placeholder="如: 比亚迪、Tesla", key="rk_name")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                y24 = st.number_input("2024 (GWh)", step=0.01, format="%.2f", key="rk_24")
            with c2:
                y25 = st.number_input("2025 (GWh)", step=0.01, format="%.2f", key="rk_25")
            with c3:
                y26 = st.number_input("2026E (GWh)", step=0.01, format="%.2f", key="rk_26")
            with c4:
                pass
            st.markdown('<span style="font-size:0.7rem;color:#6b7280;">区域拆分 (GWh)</span>', unsafe_allow_html=True)
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                americas = st.number_input("美洲", step=0.01, format="%.2f", key="rk_ams")
            with c2:
                emea = st.number_input("EMEA", step=0.01, format="%.2f", key="rk_emea")
            with c3:
                china = st.number_input("中国", step=0.01, format="%.2f", key="rk_cn")
            with c4:
                asia_pac = st.number_input("亚太", step=0.01, format="%.2f", key="rk_ap")

            if st.form_submit_button("保存排名数据", use_container_width=True, type="primary"):
                if not company_name.strip():
                    st.error("公司名称不能为空")
                else:
                    ok, msg = save_ranking(company_name.strip(), y24 or None, y25 or None, y26 or None,
                                           americas or None, emea or None, china or None, asia_pac or None)
                    st.success(msg) if ok else st.error(msg)

    else:
        rankings = get_rankings()
        if not rankings:
            st.info("暂无排名数据。")
            return
        df = pd.DataFrame(rankings)
        display_cols = [c for c in ["id", "company_name", "year_2024", "year_2025", "year_2026", "china", "americas", "emea", "asia_pacific"] if c in df.columns]
        st.dataframe(df[display_cols], use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown('<span style="font-size:0.75rem;color:#6b7280;">删除记录（输入 ID）</span>', unsafe_allow_html=True)
        del_id = st.number_input("要删除的记录 ID", step=1, min_value=1, key="rk_del_id")
        if st.button("删除该记录", type="secondary", key="rk_del_btn"):
            ok, msg = delete_ranking(del_id)
            st.success(msg) if ok else st.error(msg)
            st.rerun()
