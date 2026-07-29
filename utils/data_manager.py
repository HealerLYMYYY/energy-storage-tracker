"""
光储竞对分析系统 - 数据访问层
自动适配 SQLite(?) 和 PostgreSQL(%s) 占位符
"""

from utils.database import get_connection, USE_PG


def _ph(count):
    """返回占位符字符串"""
    if USE_PG:
        return ",".join(["%s"] * count)
    return ",".join(["?"] * count)


def _q(sql):
    """替换占位符"""
    if USE_PG:
        return sql.replace("?", "%s")
    return sql


def get_competitors():
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT c.*, (SELECT COUNT(*) FROM shipment_data s WHERE s.competitor_id=c.id) as scnt,"
            "(SELECT COUNT(*) FROM financial_data f WHERE f.competitor_id=c.id) as fcnt "
            "FROM competitors c ORDER BY c.sort_order").fetchall()]


def get_competitor(cid):
    with get_connection() as conn:
        r = conn.execute(_q("SELECT * FROM competitors WHERE cid=?"), (cid,)).fetchone()
        return dict(r) if r else None


def get_shipment(cid, periods=None):
    with get_connection() as conn:
        comp = conn.execute(_q("SELECT id FROM competitors WHERE cid=?"), (cid,)).fetchone()
        if not comp:
            return []
        q = _q("SELECT * FROM shipment_data WHERE competitor_id=? ORDER BY period")
        rows = conn.execute(q, (comp["id"],)).fetchall()
        result = {}
        for r in rows:
            result[r["period"]] = {
                "total": r["total_gwh"], "domestic": r["domestic_gwh"], "export": r["export_gwh"],
                "residential": r["residential_gwh"], "utility": r["utility_gwh"], "commercial": r["commercial_gwh"]
            }
        return result


def get_all_shipments():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT c.cid, c.name, s.* FROM shipment_data s
            JOIN competitors c ON s.competitor_id=c.id ORDER BY s.period DESC
        """).fetchall()
        return [dict(r) for r in rows]


def get_cost(cid):
    with get_connection() as conn:
        comp = conn.execute(_q("SELECT id FROM competitors WHERE cid=?"), (cid,)).fetchone()
        if not comp:
            return {}
        rows = conn.execute(_q("SELECT * FROM cost_data WHERE competitor_id=? ORDER BY period"), (comp["id"],)).fetchall()
        result = {}
        for r in rows:
            result[r["period"]] = {
                "system_cost": r["system_cost"], "domestic_price": r["domestic_price"],
                "domestic_margin": r["domestic_margin"], "export_price": r["export_price"],
                "export_margin": r["export_margin"]
            }
        return result


def get_financial(cid):
    with get_connection() as conn:
        comp = conn.execute(_q("SELECT id FROM competitors WHERE cid=?"), (cid,)).fetchone()
        if not comp:
            return {}
        rows = conn.execute(_q("SELECT * FROM financial_data WHERE competitor_id=? ORDER BY period"), (comp["id"],)).fetchall()
        result = {}
        for r in rows:
            result[r["period"]] = {
                "revenue": r["revenue"], "gross_margin": r["gross_margin"],
                "net_profit": r["net_profit"], "net_margin": r["net_margin"],
                "rv_q1": r["revenue_q1"], "rv_q2": r["revenue_q2"],
                "rv_q3": r["revenue_q3"], "rv_q4": r["revenue_q4"],
                "np_q1": r["net_profit_q1"], "np_q2": r["net_profit_q2"],
                "np_q3": r["net_profit_q3"], "np_q4": r["net_profit_q4"],
                "overseas_ratio": r["overseas_ratio"],
            }
        return result


def get_industry_data(category=None, region="全球"):
    with get_connection() as conn:
        q = _q("SELECT * FROM industry_data WHERE region=? ORDER BY period")
        params = [region]
        if category:
            q = _q("SELECT * FROM industry_data WHERE category=? AND region=? ORDER BY period")
            params = [category, region]
        return [dict(r) for r in conn.execute(q, params).fetchall()]


def get_rankings():
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM ranking_data ORDER BY year_2025 DESC").fetchall()]


# ========== 数据更新 ==========

def save_shipment(cid, period, data):
    with get_connection() as conn:
        comp = conn.execute(_q("SELECT id FROM competitors WHERE cid=?"), (cid,)).fetchone()
        if not comp:
            return False, "公司不存在"
        existing = conn.execute(_q("SELECT id FROM shipment_data WHERE competitor_id=? AND period=?"),
                                (comp["id"], period)).fetchone()
        vals = (comp["id"], period, data.get("total"), data.get("domestic"), data.get("export"),
                data.get("residential"), data.get("utility"), data.get("commercial"))
        if existing:
            conn.execute(_q("UPDATE shipment_data SET total_gwh=?,domestic_gwh=?,export_gwh=?,residential_gwh=?,utility_gwh=?,commercial_gwh=? WHERE id=?"),
                         (*vals[2:], existing["id"]))
        else:
            conn.execute(_q("INSERT INTO shipment_data (competitor_id,period,total_gwh,domestic_gwh,export_gwh,residential_gwh,utility_gwh,commercial_gwh) VALUES (?,?,?,?,?,?,?,?)"), vals)
        conn.commit()
        return True, "保存成功"


def save_cost(cid, period, data):
    with get_connection() as conn:
        comp = conn.execute(_q("SELECT id FROM competitors WHERE cid=?"), (cid,)).fetchone()
        if not comp:
            return False, "公司不存在"
        existing = conn.execute(_q("SELECT id FROM cost_data WHERE competitor_id=? AND period=?"),
                                (comp["id"], period)).fetchone()
        vals = (comp["id"], period, data.get("system_cost"), data.get("domestic_price"),
                data.get("domestic_margin"), data.get("export_price"), data.get("export_margin"))
        if existing:
            conn.execute(_q("UPDATE cost_data SET system_cost=?,domestic_price=?,domestic_margin=?,export_price=?,export_margin=? WHERE id=?"),
                         (*vals[2:], existing["id"]))
        else:
            conn.execute(_q("INSERT INTO cost_data (competitor_id,period,system_cost,domestic_price,domestic_margin,export_price,export_margin) VALUES (?,?,?,?,?,?,?)"), vals)
        conn.commit()
        return True, "保存成功"


def save_financial(cid, period, data):
    with get_connection() as conn:
        comp = conn.execute(_q("SELECT id FROM competitors WHERE cid=?"), (cid,)).fetchone()
        if not comp:
            return False, "公司不存在"
        existing = conn.execute(_q("SELECT id FROM financial_data WHERE competitor_id=? AND period=?"),
                                (comp["id"], period)).fetchone()
        vals = (comp["id"], period, data.get("revenue"), data.get("gross_margin"),
                data.get("net_profit"), data.get("net_margin"),
                data.get("rv_q1"), data.get("rv_q2"), data.get("rv_q3"), data.get("rv_q4"),
                data.get("np_q1"), data.get("np_q2"), data.get("np_q3"), data.get("np_q4"))
        if existing:
            conn.execute(_q("""UPDATE financial_data SET revenue=?,gross_margin=?,net_profit=?,net_margin=?,
                revenue_q1=?,revenue_q2=?,revenue_q3=?,revenue_q4=?,
                net_profit_q1=?,net_profit_q2=?,net_profit_q3=?,net_profit_q4=? WHERE id=?"""),
                         (*vals[2:], existing["id"]))
        else:
            conn.execute(_q("""INSERT INTO financial_data (competitor_id,period,revenue,gross_margin,net_profit,net_margin,
                revenue_q1,revenue_q2,revenue_q3,revenue_q4,
                net_profit_q1,net_profit_q2,net_profit_q3,net_profit_q4) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""), vals)
        conn.commit()
        return True, "保存成功"
