"""账户管理 — 仅管理员"""

import streamlit as st
import pandas as pd
from utils.auth import get_all_users, create_user, update_user, check_permission


def show_accounts():
    st.markdown('<h1>账户管理</h1>', unsafe_allow_html=True)

    if not check_permission("admin"):
        st.error("需要管理员权限")
        return

    tab1, tab2 = st.tabs(["用户目录", "新增用户"])

    with tab1:
        users = get_all_users()
        if users:
            rows = []
            for u in users:
                rows.append({
                    "ID": u["id"], "用户名": u["username"], "显示名": u["display_name"],
                    "角色": {"admin": "管理员", "editor": "分析师", "viewer": "访客"}.get(u["role"], u["role"]),
                    "状态": "启用" if u["is_active"] else "禁用",
                    "创建时间": u["created_at"], "最后登录": u.get("last_login") or "从未"
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            st.divider()
            st.markdown('<h3>管理用户</h3>', unsafe_allow_html=True)
            user_opts = {u["username"]: u for u in users}
            sel_name = st.selectbox("选择用户", list(user_opts.keys()), key="mgmt_user", label_visibility="collapsed")
            if sel_name:
                u = user_opts[sel_name]
                with st.form("edit_user"):
                    c1, c2 = st.columns(2)
                    with c1:
                        dn = st.text_input("显示名", value=u["display_name"])
                        role = st.selectbox("角色", ["viewer", "editor", "admin"],
                                            format_func=lambda x: {"admin": "管理员", "editor": "分析师", "viewer": "访客"}[x],
                                            index=["viewer", "editor", "admin"].index(u["role"]))
                    with c2:
                        active = st.selectbox("状态", [1, 0], format_func=lambda x: "启用" if x == 1 else "禁用",
                                              index=0 if u["is_active"] else 1)
                    if st.form_submit_button("保存修改", use_container_width=True):
                        ok, msg = update_user(u["id"], display_name=dn, role=role, is_active=active)
                        st.success(msg) if ok else st.error(msg)
                        if ok: st.rerun()

    with tab2:
        with st.form("create_user"):
            st.markdown('<h3>新增用户</h3>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                uname = st.text_input("用户名 *")
                pwd = st.text_input("密码 *", type="password", help="至少 6 位字符")
            with c2:
                dname = st.text_input("显示名 *")
                role = st.selectbox("角色 *", ["viewer", "editor", "admin"],
                                    format_func=lambda x: {"admin": "管理员（全部权限）", "editor": "分析师（可编辑）", "viewer": "访客（只读）"}[x], index=1)
            if st.form_submit_button("创建用户", use_container_width=True, type="primary"):
                if not uname or not pwd or not dname:
                    st.error("请填写所有必填项")
                else:
                    ok, msg = create_user(uname, pwd, dname, role)
                    st.success(msg) if ok else st.error(msg)
                    if ok: st.rerun()
