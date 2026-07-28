"""Account Management — Admin Only"""

import streamlit as st
import pandas as pd
from utils.auth import get_all_users, create_user, update_user, check_permission


def show_accounts():
    st.markdown('<h1>Account Management</h1>', unsafe_allow_html=True)

    if not check_permission("admin"):
        st.error("Administrator access required")
        return

    tab1, tab2 = st.tabs(["USER DIRECTORY", "ADD USER"])

    with tab1:
        users = get_all_users()
        if users:
            rows = []
            for u in users:
                rows.append({
                    "ID": u["id"], "Username": u["username"], "Display Name": u["display_name"],
                    "Role": {"admin": "ADMIN", "editor": "ANALYST", "viewer": "VIEWER"}.get(u["role"], u["role"]),
                    "Status": "Active" if u["is_active"] else "Disabled",
                    "Created": u["created_at"], "Last Login": u.get("last_login") or "Never"
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            st.divider()
            st.markdown('<h3>Manage User</h3>', unsafe_allow_html=True)
            user_opts = {u["username"]: u for u in users}
            sel_name = st.selectbox("Select user", list(user_opts.keys()), key="mgmt_user", label_visibility="collapsed")
            if sel_name:
                u = user_opts[sel_name]
                with st.form("edit_user"):
                    c1, c2 = st.columns(2)
                    with c1:
                        dn = st.text_input("Display Name", value=u["display_name"])
                        role = st.selectbox("Role", ["viewer", "editor", "admin"],
                                            format_func=lambda x: {"admin": "Administrator", "editor": "Analyst", "viewer": "Viewer"}[x],
                                            index=["viewer", "editor", "admin"].index(u["role"]))
                    with c2:
                        active = st.selectbox("Status", [1, 0], format_func=lambda x: "Active" if x == 1 else "Disabled",
                                              index=0 if u["is_active"] else 1)
                    if st.form_submit_button("Save Changes", use_container_width=True):
                        ok, msg = update_user(u["id"], display_name=dn, role=role, is_active=active)
                        st.success(msg) if ok else st.error(msg)
                        if ok: st.rerun()

    with tab2:
        with st.form("create_user"):
            st.markdown('<h3>Add New User</h3>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                uname = st.text_input("Username *")
                pwd = st.text_input("Password *", type="password", help="Minimum 6 characters")
            with c2:
                dname = st.text_input("Display Name *")
                role = st.selectbox("Role *", ["viewer", "editor", "admin"],
                                    format_func=lambda x: {"admin": "Administrator (Full)", "editor": "Analyst (Edit)", "viewer": "Viewer (Read-only)"}[x], index=1)
            if st.form_submit_button("Create User", use_container_width=True, type="primary"):
                if not uname or not pwd or not dname:
                    st.error("All fields required")
                else:
                    ok, msg = create_user(uname, pwd, dname, role)
                    st.success(msg) if ok else st.error(msg)
                    if ok: st.rerun()
