"""
光储竞对分析系统 - 数据库模块
数据源：data/ 目录下的 CSV 文件（版本管理在 GitHub 中）
运行时：SQLite 内存缓存（读写性能）
"""
import os
import csv
import bcrypt
import sqlite3
import subprocess
from contextlib import contextmanager

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "energy_storage.db")
DATA_DIR = DB_DIR  # CSV 和 DB 同目录


def _get_writable_db_path():
    """获取可写的数据库路径，如果 data/ 不可写则回退到 /tmp"""
    try:
        os.makedirs(DB_DIR, exist_ok=True)
        test_file = os.path.join(DB_DIR, ".write_test")
        with open(test_file, "w") as f:
            f.write("ok")
        os.remove(test_file)
        return DB_PATH
    except Exception:
        fallback_dir = "/tmp/energy_storage_data"
        os.makedirs(fallback_dir, exist_ok=True)
        return os.path.join(fallback_dir, "energy_storage.db")

# ============================================================
#  初始化
# ============================================================

def init_db():
    """从 CSV 加载数据到 SQLite"""
    global DB_PATH
    DB_PATH = _get_writable_db_path()
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with _get_sqlite() as conn:
        _create_tables(conn)
        conn.commit()
    _load_csv_to_sqlite()
    print(f"[DB] SQLite 数据库就绪（CSV 驱动）: {DB_PATH}")


def _create_tables(conn):
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL, display_name TEXT NOT NULL,
        role TEXT DEFAULT 'viewer', is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, last_login TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS competitors (
        id INTEGER PRIMARY KEY AUTOINCREMENT, cid TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL, name_en TEXT, ticker TEXT, company_type TEXT,
        color TEXT, keywords TEXT, description TEXT, website TEXT,
        sort_order INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS shipment_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT, competitor_id INTEGER NOT NULL,
        period TEXT NOT NULL, total_gwh REAL, domestic_gwh REAL, export_gwh REAL,
        residential_gwh REAL, utility_gwh REAL, commercial_gwh REAL,
        notes TEXT, created_by INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (competitor_id) REFERENCES competitors(id),
        UNIQUE(competitor_id, period))""")
    c.execute("""CREATE TABLE IF NOT EXISTS cost_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT, competitor_id INTEGER NOT NULL,
        period TEXT NOT NULL, system_cost REAL, domestic_price REAL,
        domestic_margin REAL, export_price REAL, export_margin REAL,
        notes TEXT, created_by INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (competitor_id) REFERENCES competitors(id),
        UNIQUE(competitor_id, period))""")
    c.execute("""CREATE TABLE IF NOT EXISTS financial_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT, competitor_id INTEGER NOT NULL,
        period TEXT NOT NULL, revenue REAL, gross_margin REAL,
        net_profit REAL, net_margin REAL,
        revenue_q1 REAL, revenue_q2 REAL, revenue_q3 REAL, revenue_q4 REAL,
        net_profit_q1 REAL, net_profit_q2 REAL, net_profit_q3 REAL, net_profit_q4 REAL,
        overseas_ratio REAL, notes TEXT, created_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (competitor_id) REFERENCES competitors(id),
        UNIQUE(competitor_id, period))""")
    c.execute("""CREATE TABLE IF NOT EXISTS industry_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT NOT NULL,
        metric_name TEXT NOT NULL, metric_value REAL, unit TEXT,
        period TEXT NOT NULL, region TEXT DEFAULT '全球', notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(category, metric_name, period, region))""")
    c.execute("""CREATE TABLE IF NOT EXISTS ranking_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT, company_name TEXT NOT NULL,
        year_2024 REAL, year_2025 REAL, year_2026 REAL,
        americas REAL, emea REAL,
        china REAL, asia_pacific REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS activity_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        action TEXT NOT NULL, target_type TEXT, target_id INTEGER,
        details TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    # 管理员用户
    c.execute("SELECT id FROM users WHERE username='admin'")
    if not c.fetchone():
        pw = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
        c.execute("INSERT INTO users (username,password_hash,display_name,role) VALUES (?,?,?,?)",
                  ("admin", pw, "管理员", "admin"))


# ============================================================
#  CSV → SQLite 加载
# ============================================================

def _load_csv_to_sqlite():
    """将 data/*.csv 文件加载到 SQLite（仅插入缺失数据，不覆盖已有）"""
    with _get_sqlite() as conn:
        c = conn.cursor()

        # 竞对公司
        csv_path = os.path.join(DATA_DIR, "competitors.csv")
        if os.path.exists(csv_path):
            c.execute("SELECT COUNT(*) as cnt FROM competitors")
            if c.fetchone()["cnt"] == 0:
                with open(csv_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        c.execute(
                            "INSERT INTO competitors (cid,name,name_en,ticker,company_type,color,keywords,description,website,sort_order) VALUES (?,?,?,?,?,?,?,?,?,?)",
                            (row["cid"], row["name"], row["name_en"] or None, row["ticker"] or None,
                             row["company_type"] or None, row["color"] or None, row["keywords"] or None,
                             row["description"] or None, row["website"] or None, int(row["sort_order"] or 0)))
            else:
                # 同步颜色
                with open(csv_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row.get("color"):
                            c.execute("UPDATE competitors SET color=? WHERE cid=?", (row["color"], row["cid"]))

        # 出货量
        _load_csv(c, "shipment_data.csv", "shipment_data",
                  ["cid", "period", "total_gwh", "domestic_gwh", "export_gwh",
                   "residential_gwh", "utility_gwh", "commercial_gwh"],
                  competitor_ref=True)

        # 成本
        _load_csv(c, "cost_data.csv", "cost_data",
                  ["cid", "period", "system_cost", "domestic_price", "domestic_margin",
                   "export_price", "export_margin"],
                  competitor_ref=True)

        # 财务
        _load_csv(c, "financial_data.csv", "financial_data",
                  ["cid", "period", "revenue", "gross_margin", "net_profit", "net_margin",
                   "revenue_q1", "revenue_q2", "revenue_q3", "revenue_q4",
                   "net_profit_q1", "net_profit_q2", "net_profit_q3", "net_profit_q4",
                   "overseas_ratio"],
                  competitor_ref=True)

        # 行业
        _load_csv(c, "industry_data.csv", "industry_data",
                  ["category", "metric_name", "metric_value", "unit", "period", "region"])

        # 排名
        _load_csv(c, "ranking_data.csv", "ranking_data",
                  ["company_name", "year_2024", "year_2025", "year_2026",
                   "americas", "emea", "china", "asia_pacific"])

        conn.commit()


def _load_csv(cursor, filename, table, columns, competitor_ref=False):
    csv_path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(csv_path):
        return
    cursor.execute(f"SELECT COUNT(*) as cnt FROM {table}")
    if cursor.fetchone()["cnt"] > 0:
        return  # 已有数据，不覆盖

    # 数值列（不应被 safe_float 影响的文本列）
    text_cols = {"cid", "period", "category", "metric_name", "unit", "region", "company_name"}

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            vals = []
            for col in columns:
                v = row.get(col)
                if col in text_cols:
                    vals.append(v if v else None)
                else:
                    vals.append(_safe_float(v))

            if competitor_ref:
                cid = row["cid"]
                comp = cursor.execute("SELECT id FROM competitors WHERE cid=?", (cid,)).fetchone()
                if not comp:
                    continue
                vals[0] = comp["id"]

            placeholders = ",".join(["?"] * len(vals))
            col_names = ",".join(columns)
            if competitor_ref:
                col_names = "competitor_id," + ",".join(columns[1:])
            cursor.execute(f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})", vals)


def _safe_float(v):
    if v is None or v == "" or v == "None":
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


# ============================================================
#  SQLite → CSV 导出（数据持久化）
# ============================================================

def export_all_csv():
    """将所有数据从 SQLite 导出到 CSV 文件"""
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        with _get_sqlite() as conn:
            c = conn.cursor()

        # 竞对公司（从 SQLite 读取完整数据）
        rows = c.execute("SELECT cid,name,name_en,ticker,company_type,color,keywords,description,website,sort_order FROM competitors ORDER BY sort_order").fetchall()
        _write_csv("competitors.csv",
                   ["cid","name","name_en","ticker","company_type","color","keywords","description","website","sort_order"],
                   [dict(r) for r in rows])

        # 出货量
        rows = c.execute("""
            SELECT c.cid, s.period, s.total_gwh, s.domestic_gwh, s.export_gwh,
                   s.residential_gwh, s.utility_gwh, s.commercial_gwh
            FROM shipment_data s JOIN competitors c ON s.competitor_id=c.id ORDER BY c.sort_order, s.period
        """).fetchall()
        _write_csv("shipment_data.csv",
                   ["cid","period","total_gwh","domestic_gwh","export_gwh","residential_gwh","utility_gwh","commercial_gwh"],
                   [dict(r) for r in rows])

        # 成本
        rows = c.execute("""
            SELECT c.cid, s.period, s.system_cost, s.domestic_price, s.domestic_margin, s.export_price, s.export_margin
            FROM cost_data s JOIN competitors c ON s.competitor_id=c.id ORDER BY c.sort_order, s.period
        """).fetchall()
        _write_csv("cost_data.csv",
                   ["cid","period","system_cost","domestic_price","domestic_margin","export_price","export_margin"],
                   [dict(r) for r in rows])

        # 财务
        rows = c.execute("""
            SELECT c.cid, s.period, s.revenue, s.gross_margin, s.net_profit, s.net_margin,
                   s.revenue_q1, s.revenue_q2, s.revenue_q3, s.revenue_q4,
                   s.net_profit_q1, s.net_profit_q2, s.net_profit_q3, s.net_profit_q4, s.overseas_ratio
            FROM financial_data s JOIN competitors c ON s.competitor_id=c.id ORDER BY c.sort_order, s.period
        """).fetchall()
        _write_csv("financial_data.csv",
                   ["cid","period","revenue","gross_margin","net_profit","net_margin",
                    "revenue_q1","revenue_q2","revenue_q3","revenue_q4",
                    "net_profit_q1","net_profit_q2","net_profit_q3","net_profit_q4","overseas_ratio"],
                   [dict(r) for r in rows])

        # 行业数据
        rows = c.execute("SELECT category,metric_name,metric_value,unit,period,region FROM industry_data ORDER BY category,period").fetchall()
        _write_csv("industry_data.csv",
                   ["category","metric_name","metric_value","unit","period","region"],
                   [dict(r) for r in rows])

        # 排名
        rows = c.execute("SELECT company_name,year_2024,year_2025,year_2026,americas,emea,china,asia_pacific FROM ranking_data ORDER BY year_2025 DESC").fetchall()
        _write_csv("ranking_data.csv",
                   ["company_name","year_2024","year_2025","year_2026","americas","emea","china","asia_pacific"],
                   [dict(r) for r in rows])
    except Exception as e:
        print(f"[DB] CSV 导出失败: {e}")
        raise


def _write_csv(filename, columns, rows):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            # 处理 None → ""
            clean = {k: ("" if row[k] is None else row[k]) for k in columns}
            writer.writerow(clean)


# ============================================================
#  Git 自动提交
# ============================================================

def git_commit_and_push(message="数据更新"):
    """将 data/ 目录下的 CSV 文件 commit 并 push 到 GitHub"""
    repo_dir = os.path.dirname(DB_DIR)
    try:
        # 检查是否有 git 仓库
        result = subprocess.run(["git", "-C", repo_dir, "rev-parse", "--git-dir"],
                                capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            return False, "当前目录不是 Git 仓库"

        # 设置 commit 作者（避免 Streamlit Cloud 未配置 git identity）
        env = os.environ.copy()
        if not os.environ.get("GIT_AUTHOR_NAME"):
            env["GIT_AUTHOR_NAME"] = "Energy Tracker"
        if not os.environ.get("GIT_AUTHOR_EMAIL"):
            env["GIT_AUTHOR_EMAIL"] = "energy-tracker@streamlit.app"
        if not os.environ.get("GIT_COMMITTER_NAME"):
            env["GIT_COMMITTER_NAME"] = env["GIT_AUTHOR_NAME"]
        if not os.environ.get("GIT_COMMITTER_EMAIL"):
            env["GIT_COMMITTER_EMAIL"] = env["GIT_AUTHOR_EMAIL"]

        subprocess.run(["git", "-C", repo_dir, "add", "data/*.csv"],
                       capture_output=True, timeout=10, env=env)
        result = subprocess.run(
            ["git", "-C", repo_dir, "commit", "-m", f"data: {message}"],
            capture_output=True, timeout=10, text=True, env=env
        )
        # 如果有变更才 push
        if result.returncode == 0:
            push_result = subprocess.run(["git", "-C", repo_dir, "push", "origin", "main"],
                           capture_output=True, text=True, timeout=30, env=env)
            if push_result.returncode == 0:
                return True, "已同步到 GitHub"
            else:
                return False, f"Push 失败: {push_result.stderr}"
        elif "nothing to commit" in result.stdout or "nothing to commit" in result.stderr:
            return True, "无变更"
        else:
            return False, f"Commit 失败: {result.stderr}"
    except Exception as e:
        return False, f"Git 操作失败: {e}"


# ============================================================
#  连接管理
# ============================================================

@contextmanager
def _get_sqlite():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def get_connection():
    """统一数据库连接（始终使用 SQLite）"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
    finally:
        conn.close()
