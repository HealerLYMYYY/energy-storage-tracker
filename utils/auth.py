"""
光储竞对分析系统 - 认证模块
"""

import bcrypt
import streamlit as st
from datetime import datetime
from utils.database import get_connection


def init_auth():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = None


def verify_password(plain, hashed):
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def hash_password(plain):
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def authenticate(username, password):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT id,username,password_hash,display_name,role,is_active FROM users WHERE username=?", (username,))
        u = c.fetchone()
        if not u or not u["is_active"] or not verify_password(password, u["password_hash"]):
            return None
        c.execute("UPDATE users SET last_login=? WHERE id=?", (datetime.now(), u["id"]))
        conn.commit()
        log_activity(u["id"], "login", f"用户 {username} 登录")
        return {"id": u["id"], "username": u["username"], "display_name": u["display_name"], "role": u["role"]}


def logout():
    if st.session_state.user:
        log_activity(st.session_state.user["id"], "logout", f"用户 {st.session_state.user['username']} 退出")
    st.session_state.authenticated = False
    st.session_state.user = None


def log_activity(user_id, action, details=""):
    try:
        with get_connection() as conn:
            conn.execute("INSERT INTO activity_logs (user_id,action,details) VALUES (?,?,?)",
                         (user_id, action, details))
            conn.commit()
    except Exception:
        pass


def check_permission(required):
    if not st.session_state.authenticated:
        return False
    hierarchy = {"admin": 3, "editor": 2, "viewer": 1}
    return hierarchy.get(st.session_state.user.get("role", "viewer"), 0) >= hierarchy.get(required, 0)


def get_all_users():
    with get_connection() as conn:
        return [dict(r) for r in conn.execute("SELECT id,username,display_name,role,is_active,created_at,last_login FROM users ORDER BY created_at DESC").fetchall()]


def create_user(username, password, display_name, role="viewer"):
    if not username or not password or not display_name:
        return False, "必填字段不能为空"
    if len(password) < 6:
        return False, "密码至少6位"
    try:
        with get_connection() as conn:
            if conn.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone():
                return False, f"用户名 '{username}' 已存在"
            conn.execute("INSERT INTO users (username,password_hash,display_name,role) VALUES (?,?,?,?)",
                         (username, hash_password(password), display_name, role))
            conn.commit()
            if st.session_state.user:
                log_activity(st.session_state.user["id"], "create_user", f"创建用户 {username}")
            return True, f"用户 '{username}' 创建成功"
    except Exception as e:
        return False, f"失败: {e}"


def update_user(user_id, **kw):
    allowed = ["display_name", "role", "is_active"]
    updates = {k: v for k, v in kw.items() if k in allowed}
    if not updates:
        return False, "无有效字段"
    try:
        with get_connection() as conn:
            set_clause = ", ".join(f"{k}=?" for k in updates)
            conn.execute(f"UPDATE users SET {set_clause} WHERE id=?", (*updates.values(), user_id))
            conn.commit()
            return True, "更新成功"
    except Exception as e:
        return False, f"失败: {e}"
