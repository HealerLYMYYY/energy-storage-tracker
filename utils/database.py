"""
光储竞对分析系统 - 数据库模块 (双模式: SQLite开发 / PostgreSQL生产)
环境变量 DATABASE_URL 为空时使用本地 SQLite，否则使用 PostgreSQL
"""

import os
import bcrypt
import psycopg2
import psycopg2.extras
import sqlite3
from contextlib import contextmanager

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "energy_storage.db")
DATABASE_URL = os.environ.get("DATABASE_URL", "")

# 当前模式
USE_PG = bool(DATABASE_URL)


def init_db():
    """初始化数据库 + 建表 + 种子数据"""
    if USE_PG:
        _init_pg()
    else:
        _init_sqlite()


# ============================================================
#  SQLite 模式
# ============================================================

def _init_sqlite():
    os.makedirs(DB_DIR, exist_ok=True)
    with _get_sqlite() as conn:
        _create_tables_sqlite(conn)
        conn.commit()
    seed_all_data()
    print(f"SQLite 数据库就绪: {DB_PATH}")


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


def _create_tables_sqlite(conn):
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
        year_2024 REAL, year_2025 REAL, americas REAL, emea REAL,
        china REAL, asia_pacific REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS activity_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        action TEXT NOT NULL, target_type TEXT, target_id INTEGER,
        details TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")


# ============================================================
#  PostgreSQL 模式
# ============================================================

def _init_pg():
    with _get_pg() as conn:
        _create_tables_pg(conn)
        conn.commit()
    seed_all_data()
    print(f"PostgreSQL 数据库就绪")


@contextmanager
def _get_pg():
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    try:
        yield conn
    finally:
        conn.close()


def _create_tables_pg(conn):
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY, username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL, display_name TEXT NOT NULL,
            role TEXT DEFAULT 'viewer', is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, last_login TIMESTAMP)""")
    c.execute("""
        CREATE TABLE IF NOT EXISTS competitors (
            id SERIAL PRIMARY KEY, cid TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL, name_en TEXT, ticker TEXT, company_type TEXT,
            color TEXT, keywords TEXT, description TEXT, website TEXT,
            sort_order INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""
        CREATE TABLE IF NOT EXISTS shipment_data (
            id SERIAL PRIMARY KEY, competitor_id INTEGER NOT NULL REFERENCES competitors(id),
            period TEXT NOT NULL, total_gwh REAL, domestic_gwh REAL, export_gwh REAL,
            residential_gwh REAL, utility_gwh REAL, commercial_gwh REAL,
            notes TEXT, created_by INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(competitor_id, period))""")
    c.execute("""
        CREATE TABLE IF NOT EXISTS cost_data (
            id SERIAL PRIMARY KEY, competitor_id INTEGER NOT NULL REFERENCES competitors(id),
            period TEXT NOT NULL, system_cost REAL, domestic_price REAL,
            domestic_margin REAL, export_price REAL, export_margin REAL,
            notes TEXT, created_by INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(competitor_id, period))""")
    c.execute("""
        CREATE TABLE IF NOT EXISTS financial_data (
            id SERIAL PRIMARY KEY, competitor_id INTEGER NOT NULL REFERENCES competitors(id),
            period TEXT NOT NULL, revenue REAL, gross_margin REAL,
            net_profit REAL, net_margin REAL,
            revenue_q1 REAL, revenue_q2 REAL, revenue_q3 REAL, revenue_q4 REAL,
            net_profit_q1 REAL, net_profit_q2 REAL, net_profit_q3 REAL, net_profit_q4 REAL,
            overseas_ratio REAL, notes TEXT, created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(competitor_id, period))""")
    c.execute("""
        CREATE TABLE IF NOT EXISTS industry_data (
            id SERIAL PRIMARY KEY, category TEXT NOT NULL,
            metric_name TEXT NOT NULL, metric_value REAL, unit TEXT,
            period TEXT NOT NULL, region TEXT DEFAULT '全球', notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(category, metric_name, period, region))""")
    c.execute("""
        CREATE TABLE IF NOT EXISTS ranking_data (
            id SERIAL PRIMARY KEY, company_name TEXT NOT NULL,
            year_2024 REAL, year_2025 REAL, americas REAL, emea REAL,
            china REAL, asia_pacific REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""
        CREATE TABLE IF NOT EXISTS activity_logs (
            id SERIAL PRIMARY KEY, user_id INTEGER,
            action TEXT NOT NULL, target_type TEXT, target_id INTEGER,
            details TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")


# ============================================================
#  统一连接接口
# ============================================================

@contextmanager
def get_connection():
    """统一数据库连接 - 自动选择 SQLite 或 PostgreSQL"""
    if USE_PG:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        conn.cursor_factory = psycopg2.extras.RealDictCursor
        try:
            yield conn
        finally:
            conn.close()
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
        finally:
            conn.close()


def _dict_row(row):
    """将查询结果转为 dict"""
    if row is None:
        return None
    if isinstance(row, dict):
        return row
    return dict(row)


# ============================================================
#  种子数据
# ============================================================

COMPETITORS_SEED = [
    ("catl", "宁德时代", "CATL", "300750.SZ", "电池/系统", "#ff7b00",
     "宁德时代 CATL 麒麟电池 神行电池", "全球领先的动力电池与储能电池制造商", "https://www.catl.com", 1),
    ("byd", "比亚迪", "BYD", "002594.SZ", "电池/系统", "#54b86b",
     "比亚迪 弗迪电池 刀片电池", "新能源汽车与电池垂直整合企业", "https://www.byd.com", 2),
    ("hb", "海博思创", "Hyperstrong", "688411.SH", "储能系统", "#55b8b4",
     "海博思创 Hyperstrong", "国内储能系统集成龙头", "https://www.hyperstrong.com.cn", 3),
    ("hc", "海辰储能", "HiTHIUM", "未上市", "储能电池", "#6e8efb",
     "海辰储能 HiTHIUM", "快速崛起的储能电池新势力", "https://www.hithium.com", 4),
    ("tesla", "Tesla", "Tesla", "TSLA", "综合能源", "#e85d75",
     "Tesla Megapack Powerwall", "全球综合能源标杆企业", "https://www.tesla.com", 5),
    ("tc", "天合储能", "TrinaStorage", "688599.SH", "光储一体", "#f5a623",
     "天合光能 天合储能 TrinaStorage", "光伏+储能一体化企业", "https://www.trinasolar.com", 6),
    ("deye", "德业股份", "Deye", "605117.SH", "逆变器", "#55b8b4",
     "德业股份 Deye", "逆变器+储能系统双轮驱动", "https://www.deye.com.cn", 7),
    ("sg", "思格新能源", "Sigenergy", "未上市", "储能系统", "#54b86b",
     "思格新能源 Sigenergy", "专注海外户用储能市场", "https://www.sigenergy.com", 8),
    ("flu", "Fluence", "Fluence", "FLNC", "储能系统", "#6e8efb",
     "Fluence Energy", "全球储能系统集成商", "https://fluenceenergy.com", 9),
]

SHIPMENT_SEED = [
    ("catl", "2022", 47, 47, 0, 5, 35, 7), ("catl", "2023", 69, 69, 0, 8, 52, 9),
    ("catl", "2024", 93, 31.4, 61.6, 12, 65, 16), ("catl", "2025", 121, 32, 89, 15, 80, 26),
    ("byd", "2022", 11, 8.8, 2.2, 1, 8, 2), ("byd", "2023", 23, 17.5, 5.5, 2, 18, 3),
    ("byd", "2024", 28, 22, 6, 3, 20, 5), ("byd", "2025", 65, 40, 25, 5, 50, 10),
    ("hb", "2022", 2.105, 2.105, 0, 0, 1.5, 0.605), ("hb", "2023", 6.212, 6.212, 0, 0.2, 5, 1.012),
    ("hb", "2024", 13.60, 13.0, 0.60, 0.5, 10, 3.1), ("hb", "2025", 28, 27.5, 0.5, 1, 22, 5),
    ("hb", "2026E", 65, 57, 8, 3, 50, 12),
    ("hc", "2022", 4.3, 4.3, 0, 0.5, 3, 0.8), ("hc", "2023", 17.8, 17.6, 0.2, 1.5, 14, 2.3),
    ("hc", "2024", 33.6, 28.3, 5.3, 3, 25, 5.6), ("hc", "2025", 68.4, 58.1, 10.3, 5, 55, 8.4),
    ("tesla", "2024", 33.65, 0, 33.65, 1.65, 25, 7), ("tesla", "2025", 46.7, 0, 46.7, 2, 35, 9.7),
    ("tc", "2022", 2.0, 1.48, 0.46, 0.3, 1.3, 0.4), ("tc", "2023", 2.17, 1.56, 0.61, 0.3, 1.5, 0.37),
    ("tc", "2024", 4.84, 3.3, 1.54, 0.6, 3.5, 0.74), ("tc", "2025", 9.5, 6.5, 3.0, 1, 7, 1.5),
    ("deye", "2022", 12.0, 3.5, 8.5, 8, 1.5, 2.5), ("deye", "2023", 25.5, 6.0, 19.5, 18, 3, 4.5),
    ("deye", "2024", 38.0, 8.0, 30.0, 27, 4, 7), ("deye", "2025", 52.0, 10.0, 42.0, 36, 6, 10),
    ("sg", "2024", 1.5, 0.05, 1.45, 1.2, 0.1, 0.2), ("sg", "2025", 4.0, 0.04, 3.96, 3.2, 0.3, 0.5),
    ("flu", "2024", 9.0, 5.1, 3.9, 0, 7, 2), ("flu", "2025", 8.5, 4.7, 3.8, 0, 6.5, 2),
]

COST_SEED = [
    ("catl", "2022", 0.794, 0.794, 17.0, 0.957, 17.0), ("catl", "2023", 0.706, 0.706, 18.7, 0.868, 18.7),
    ("catl", "2024", 0.451, 0.451, 26.8, 0.616, 26.8), ("catl", "2025", 0.389, 0.389, 26.7, 0.580, 32.9),
    ("byd", "2024", None, None, 15.0, None, 15.0), ("byd", "2025", None, None, 15.0, None, 15.0),
    ("hb", "2022", 0.87, 1.16, 24.8, None, None), ("hb", "2023", 0.83, 1.08, 23.5, None, None),
    ("hb", "2024", 0.51, 0.59, 16.85, 0.69, 35.0), ("hb", "2025", 0.448, 0.54, 17.0, 0.68, 35.0),
    ("hb", "2026E", 0.483, 0.59, 18.0, 0.60, 19.5),
    ("hc", "2022", 0.777, 0.870, 10.7, 1.040, 25.3), ("hc", "2023", 0.504, 0.576, 12.5, 1.028, 51.0),
    ("hc", "2024", 0.288, 0.316, 9.0, 0.983, 70.7), ("hc", "2025", 0.258, 0.287, 9.9, 0.565, 54.3),
    ("tesla", "2024", 0.62, 0.85, 27.1, 0.98, 36.7), ("tesla", "2025", 0.55, 0.75, 26.7, 0.88, 37.5),
    ("tc", "2022", 0.884, 1.13, 28.0, 1.29, 31.0), ("tc", "2023", 0.778, 1.0, 29.0, 1.15, 33.0),
    ("tc", "2024", 0.548, 0.58, 5.5, 0.65, 15.7), ("tc", "2025", 0.43, 0.44, 1.7, 0.52, 16.4),
    ("deye", "2022", 0.35, 0.52, 32.7, 0.68, 48.5), ("deye", "2023", 0.30, 0.45, 33.3, 0.58, 48.3),
    ("deye", "2024", 0.26, 0.38, 31.6, 0.50, 48.0), ("deye", "2025", 0.23, 0.34, 32.4, 0.45, 48.9),
    ("sg", "2024", 0.35, 0.48, 27.1, 0.62, 43.5), ("sg", "2025", 0.30, 0.42, 28.6, 0.55, 45.5),
    ("flu", "2024", 0.62, 0.75, 17.3, 0.90, 31.1), ("flu", "2025", 0.55, 0.65, 15.4, 0.78, 29.5),
]

FINANCIAL_SEED = [
    ("catl", "2022", 449.80, 17.01, 76.53, 17.01, 110, 112, 115, 112.8, 19, 19.5, 20, 18.03),
    ("catl", "2023", 599.01, 18.66, 111.75, 18.66, 145, 150, 152, 152.01, 27, 28, 28.5, 28.25),
    ("catl", "2024", 572.90, 26.84, 153.76, 26.84, 140, 143, 145, 144.9, 38, 38.5, 39, 38.26),
    ("catl", "2025", 624.40, 26.71, 165.84, 26.56, 150, 155, 160, 159.4, 40, 42, 41, 42.84),
    ("byd", "2024", 220.0, 15.0, None, None, 50, 55, 58, 57, None, None, None, None),
    ("byd", "2025", 385.0, 15.0, None, None, 90, 95, 100, 100, None, None, None, None),
    ("hb", "2022", 26.26, 20.79, 1.82, 6.93, 6, 6.5, 7, 6.76, 0.4, 0.45, 0.5, 0.47),
    ("hb", "2023", 69.82, 19.80, 5.78, 8.28, 16, 17, 18, 18.82, 1.3, 1.4, 1.5, 1.58),
    ("hb", "2024", 82.70, 17.90, 6.48, 7.85, 19, 20, 21, 22.7, 1.5, 1.6, 1.7, 1.68),
    ("hb", "2025", 116.04, 19.26, 9.49, 8.18, 27, 29, 30, 30.04, 2.2, 2.4, 2.5, 2.39),
    ("hb", "2026E", 331.20, 18.29, 26.83, 8.10, 78, 82, 85, 86.2, 6.3, 6.7, 7.0, 6.83),
    ("hc", "2022", 36.15, 11.30, -17.77, -49.16, 8, 9, 10, 9.15, -4.5, -4.3, -4.2, -4.77),
    ("hc", "2023", 102.02, 12.10, -19.75, -19.36, 24, 25, 26, 27.02, -5, -4.8, -4.7, -5.25),
    ("hc", "2024", 129.17, 17.90, 2.88, 2.23, 30, 32, 33, 34.17, 0.5, 0.7, 0.8, 0.88),
    ("hc", "2025", 224.48, 17.55, 7.30, 3.25, 52, 55, 58, 59.48, 1.5, 1.8, 2.0, 2.0),
    ("tesla", "2024", 234.0, 17.0, 40.95, 17.5, 55, 58, 60, 61, 9.5, 10, 10.5, 10.95),
    ("tesla", "2025", 327.0, 17.0, 55.59, 17.0, 78, 81, 84, 84, 13, 14, 14.5, 14.09),
    ("tc", "2022", 19.54, 9.53, 0.01, 0.04, 4.5, 5, 5, 5.04, 0, 0, 0, 0.01),
    ("tc", "2023", 21.60, 16.90, 0.24, 1.11, 5, 5.5, 5.5, 5.6, 0.05, 0.06, 0.06, 0.07),
    ("tc", "2024", 29.15, 11.15, -3.50, -12.01, 7, 7.5, 7.5, 7.15, -0.8, -0.9, -0.9, -0.9),
    ("tc", "2025", 35.40, 8.90, -4.60, -12.99, 8.5, 9, 9, 8.9, -1.1, -1.2, -1.1, -1.2),
    ("deye", "2022", 59.56, 40.4, 15.17, 25.5, 14, 15, 15.5, 15.06, 3.5, 3.8, 4, 3.87),
    ("deye", "2023", 74.80, 40.4, 17.91, 23.9, 18, 19, 19, 18.8, 4.3, 4.5, 4.6, 4.51),
    ("deye", "2024", 112.06, 38.8, 29.60, 26.4, 27, 28, 28.5, 28.56, 7, 7.5, 7.5, 7.6),
    ("deye", "2025", 122.24, 38.1, 31.71, 25.9, 30, 31, 30.5, 30.74, 7.8, 8, 7.9, 8.01),
    ("sg", "2023", 0.58, 31.3, -3.73, -640.5, 0.1, 0.15, 0.15, 0.18, -1, -0.9, -0.9, -0.93),
    ("sg", "2024", 13.30, 46.9, 0.84, 6.3, 3, 3.3, 3.5, 3.5, 0.15, 0.2, 0.25, 0.24),
    ("sg", "2025", 90.01, 50.1, 29.19, 32.4, 20, 22, 24, 24.01, 6.5, 7, 7.8, 7.89),
    ("flu", "2024", 63.0, 12.0, -0.28, -0.44, 15, 16, 16, 16, -0.1, -0.05, -0.05, -0.08),
    ("flu", "2025", 59.5, 14.0, 0.50, 0.84, 14, 15, 15.5, 15, 0.1, 0.15, 0.15, 0.1),
]

INDUSTRY_SEED = [
    ("光伏", "全球光伏出货量", 130, "GW", "2020", "全球"), ("光伏", "全球光伏出货量", 170, "GW", "2021", "全球"),
    ("光伏", "全球光伏出货量", 240, "GW", "2022", "全球"), ("光伏", "全球光伏出货量", 390, "GW", "2023", "全球"),
    ("光伏", "全球光伏出货量", 520, "GW", "2024", "全球"), ("光伏", "全球光伏出货量", 650, "GW", "2025", "全球"),
    ("储能", "全球储能出货量", 15, "GWh", "2020", "全球"), ("储能", "全球储能出货量", 29, "GWh", "2021", "全球"),
    ("储能", "全球储能出货量", 54, "GWh", "2022", "全球"), ("储能", "全球储能出货量", 98, "GWh", "2023", "全球"),
    ("储能", "全球储能出货量", 185, "GWh", "2024", "全球"), ("储能", "全球储能出货量", 310, "GWh", "2025", "全球"),
    ("锂电池", "全球锂电池出货量", 150, "GWh", "2020", "全球"), ("锂电池", "全球锂电池出货量", 260, "GWh", "2021", "全球"),
    ("锂电池", "全球锂电池出货量", 420, "GWh", "2022", "全球"), ("锂电池", "全球锂电池出货量", 590, "GWh", "2023", "全球"),
    ("锂电池", "全球锂电池出货量", 780, "GWh", "2024", "全球"), ("锂电池", "全球锂电池出货量", 980, "GWh", "2025", "全球"),
    ("锂电池", "碳酸锂价格", 0.85, "万元/吨", "2020", "全球"), ("锂电池", "碳酸锂价格", 0.72, "万元/吨", "2021", "全球"),
    ("锂电池", "碳酸锂价格", 0.58, "万元/吨", "2022", "全球"), ("锂电池", "碳酸锂价格", 0.42, "万元/吨", "2023", "全球"),
    ("锂电池", "碳酸锂价格", 0.35, "万元/吨", "2024", "全球"), ("锂电池", "碳酸锂价格", 0.32, "万元/吨", "2025", "全球"),
    ("储能", "系统成本", 1.25, "?/Wh", "2020", "全球"), ("储能", "系统成本", 1.05, "?/Wh", "2021", "全球"),
    ("储能", "系统成本", 0.82, "?/Wh", "2022", "全球"), ("储能", "系统成本", 0.58, "?/Wh", "2023", "全球"),
    ("储能", "系统成本", 0.45, "?/Wh", "2024", "全球"), ("储能", "系统成本", 0.38, "?/Wh", "2025", "全球"),
]

RANKING_SEED = [
    ("比亚迪", 25.2, 53.63, 7.6, 5.2, 11.6, 0.8), ("Tesla", 33.65, 46.7, 27.1, 3.5, 0, 3.1),
    ("阳光电源", 28, 42.95, 8, 5, 13.5, 1.5), ("宁德时代", 33, 41.5, 14.2, 3, 13.6, 2.2),
    ("中车株洲所", 14.6, 25.05, 0, 0, 14.6, 0), ("华为", 6.6, 25.6, 0, 2.4, 2.9, 1.3),
    ("海博思创", 12.1, 24, 0, 0, 12.47, 0.03), ("远景能源", 8, 17.1, 0.4, 0.5, 6.8, 0.3),
    ("海辰储能", 0, 10.3, 4.7, 1.2, 3.3, 1.1), ("电工时代", 5.8, 9.8, 0, 0, 5.8, 0),
    ("Fluence", 9, 8.5, 5.1, 1.825, 0, 2.1), ("阿特斯", 6.5, 8.1, 3.5, 0.2, 1.66, 1.14),
]


def seed_all_data():
    """预置所有种子数据（仅首次插入）"""
    with get_connection() as conn:
        c = conn.cursor()

        # 管理员
        c.execute("SELECT id FROM users WHERE username='admin'")
        if not c.fetchone():
            pw = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
            c.execute("INSERT INTO users (username,password_hash,display_name,role) VALUES (%s,%s,%s,%s)" if USE_PG else
                      "INSERT INTO users (username,password_hash,display_name,role) VALUES (?,?,?,?)",
                      ("admin", pw, "管理员", "admin"))

        # 竞对
        c.execute("SELECT COUNT(*) as cnt FROM competitors")
        if c.fetchone()["cnt"] == 0:
            for comp in COMPETITORS_SEED:
                ph = "(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)" if USE_PG else "(?,?,?,?,?,?,?,?,?,?)"
                c.execute(f"INSERT INTO competitors (cid,name,name_en,ticker,company_type,color,keywords,description,website,sort_order) VALUES {ph}", comp)

        # 出货量
        c.execute("SELECT COUNT(*) as cnt FROM shipment_data")
        if c.fetchone()["cnt"] == 0:
            for s in SHIPMENT_SEED:
                cid = s[0]
                comp = c.execute(f"SELECT id FROM competitors WHERE cid={'%s' if USE_PG else '?'}", (cid,)).fetchone()
                if comp:
                    ph = "(%s,%s,%s,%s,%s,%s,%s,%s)" if USE_PG else "(?,?,?,?,?,?,?,?)"
                    c.execute(f"INSERT INTO shipment_data (competitor_id,period,total_gwh,domestic_gwh,export_gwh,residential_gwh,utility_gwh,commercial_gwh) VALUES {ph}",
                              (comp["id"], s[1], s[2], s[3], s[4], s[5], s[6], s[7]))

        # 成本
        c.execute("SELECT COUNT(*) as cnt FROM cost_data")
        if c.fetchone()["cnt"] == 0:
            for item in COST_SEED:
                cid = item[0]
                comp = c.execute(f"SELECT id FROM competitors WHERE cid={'%s' if USE_PG else '?'}", (cid,)).fetchone()
                if comp:
                    ph = "(%s,%s,%s,%s,%s,%s,%s)" if USE_PG else "(?,?,?,?,?,?,?)"
                    c.execute(f"INSERT INTO cost_data (competitor_id,period,system_cost,domestic_price,domestic_margin,export_price,export_margin) VALUES {ph}",
                              (comp["id"], item[1], item[2], item[3], item[4], item[5], item[6]))

        # 财务
        c.execute("SELECT COUNT(*) as cnt FROM financial_data")
        if c.fetchone()["cnt"] == 0:
            for item in FINANCIAL_SEED:
                cid = item[0]
                comp = c.execute(f"SELECT id FROM competitors WHERE cid={'%s' if USE_PG else '?'}", (cid,)).fetchone()
                if comp:
                    ph = "(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)" if USE_PG else "(?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
                    c.execute(f"INSERT INTO financial_data (competitor_id,period,revenue,gross_margin,net_profit,net_margin,revenue_q1,revenue_q2,revenue_q3,revenue_q4,net_profit_q1,net_profit_q2,net_profit_q3,net_profit_q4) VALUES {ph}",
                              (comp["id"], item[1], item[2], item[3], item[4], item[5], item[6], item[7], item[8], item[9], item[10], item[11], item[12], item[13]))

        # 行业
        c.execute("SELECT COUNT(*) as cnt FROM industry_data")
        if c.fetchone()["cnt"] == 0:
            for item in INDUSTRY_SEED:
                ph = "(%s,%s,%s,%s,%s,%s)" if USE_PG else "(?,?,?,?,?,?)"
                c.execute(f"INSERT INTO industry_data (category,metric_name,metric_value,unit,period,region) VALUES {ph}", item)

        # 排名
        c.execute("SELECT COUNT(*) as cnt FROM ranking_data")
        if c.fetchone()["cnt"] == 0:
            for item in RANKING_SEED:
                ph = "(%s,%s,%s,%s,%s,%s,%s)" if USE_PG else "(?,?,?,?,?,?,?)"
                c.execute(f"INSERT INTO ranking_data (company_name,year_2024,year_2025,americas,emea,china,asia_pacific) VALUES {ph}", item)

        conn.commit()
    print("种子数据预置完成")
