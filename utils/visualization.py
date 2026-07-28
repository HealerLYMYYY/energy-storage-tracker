"""
光储竞对分析系统 - 可视化模块 (Plotly)
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


def ship_trend_chart(competitors, data_map, periods):
    """出货量趋势折线图"""
    fig = go.Figure()
    for comp in competitors:
        d = data_map.get(comp["cid"], {})
        vals = [d.get(y, {}).get("total") for y in periods]
        fig.add_trace(go.Scatter(x=periods, y=vals, name=comp["name"],
                                 line=dict(color=comp["color"], width=2.5),
                                 mode="lines+markers", marker=dict(size=6)))
    fig.update_layout(hovermode="x unified", margin=dict(l=20, r=20, t=30, b=20),
                      legend=dict(font=dict(size=10)), plot_bgcolor="rgba(0,0,0,0)",
                      paper_bgcolor="rgba(0,0,0,0)")
    return fig


def ship_stack_chart(competitors, data_map, period="2025", mode="region"):
    """出货量堆叠柱状图"""
    names = [c["name"] for c in competitors]
    if mode == "region":
        d1, d2 = [data_map.get(c["cid"], {}).get(period, {}).get("domestic", 0) or 0 for c in competitors], \
                 [data_map.get(c["cid"], {}).get(period, {}).get("export", 0) or 0 for c in competitors]
        fig = go.Figure(data=[
            go.Bar(name="国内", x=names, y=d1, marker_color="rgba(255,123,0,0.7)"),
            go.Bar(name="海外", x=names, y=d2, marker_color="rgba(84,184,107,0.7)")
        ])
    else:
        d1 = [data_map.get(c["cid"], {}).get(period, {}).get("residential", 0) or 0 for c in competitors]
        d2 = [data_map.get(c["cid"], {}).get(period, {}).get("utility", 0) or 0 for c in competitors]
        d3 = [data_map.get(c["cid"], {}).get(period, {}).get("commercial", 0) or 0 for c in competitors]
        fig = go.Figure(data=[
            go.Bar(name="户用储能", x=names, y=d1, marker_color="rgba(85,184,180,0.7)"),
            go.Bar(name="大储", x=names, y=d2, marker_color="rgba(255,123,0,0.7)"),
            go.Bar(name="工商业储能", x=names, y=d3, marker_color="rgba(110,142,251,0.7)")
        ])
    fig.update_layout(barmode="stack", margin=dict(l=20, r=20, t=30, b=20),
                      legend=dict(font=dict(size=10)), plot_bgcolor="rgba(0,0,0,0)",
                      paper_bgcolor="rgba(0,0,0,0)")
    return fig


def fin_bar_chart(competitors, data_map, field="revenue", year1="2024", year2="2025"):
    """财务对比柱状图"""
    names = [c["name"] for c in competitors]
    v1 = [data_map.get(c["cid"], {}).get(year1, {}).get(field) or 0 for c in competitors]
    v2 = [data_map.get(c["cid"], {}).get(year2, {}).get(field) or 0 for c in competitors]
    fig = go.Figure(data=[
        go.Bar(name=year1, x=names, y=v1, marker_color="rgba(0,0,0,0.1)"),
        go.Bar(name=year2, x=names, y=v2, marker_color="rgba(255,123,0,0.7)")
    ])
    fig.update_layout(barmode="group", margin=dict(l=20, r=20, t=30, b=20),
                      legend=dict(font=dict(size=10)), plot_bgcolor="rgba(0,0,0,0)",
                      paper_bgcolor="rgba(0,0,0,0)")
    return fig


def qtr_bar_chart(competitors, data_map, field="rv", year="2025"):
    """季度拆分柱状图"""
    names = [c["name"] for c in competitors]
    q1 = [data_map.get(c["cid"], {}).get(year, {}).get(f"{field}_q1") or 0 for c in competitors]
    q2 = [data_map.get(c["cid"], {}).get(year, {}).get(f"{field}_q2") or 0 for c in competitors]
    q3 = [data_map.get(c["cid"], {}).get(year, {}).get(f"{field}_q3") or 0 for c in competitors]
    q4 = [data_map.get(c["cid"], {}).get(year, {}).get(f"{field}_q4") or 0 for c in competitors]
    fig = go.Figure(data=[
        go.Bar(name="Q1", x=names, y=q1, marker_color="rgba(255,123,0,0.8)"),
        go.Bar(name="Q2", x=names, y=q2, marker_color="rgba(84,184,107,0.8)"),
        go.Bar(name="Q3", x=names, y=q3, marker_color="rgba(85,184,180,0.8)"),
        go.Bar(name="Q4", x=names, y=q4, marker_color="rgba(110,142,251,0.8)")
    ])
    fig.update_layout(barmode="stack", margin=dict(l=20, r=20, t=30, b=20),
                      legend=dict(font=dict(size=10)), plot_bgcolor="rgba(0,0,0,0)",
                      paper_bgcolor="rgba(0,0,0,0)")
    return fig


def cost_margin_scatter(competitors, cost_map, margin_map):
    """成本-毛利散点图"""
    names, xs, ys, colors = [], [], [], []
    for c in competitors:
        co = cost_map.get(c["cid"], {}).get("2025", {})
        fi = margin_map.get(c["cid"], {}).get("2025", {})
        if co.get("system_cost"):
            names.append(c["name"]); xs.append(co["system_cost"])
            ys.append(co.get("domestic_margin") or 0); colors.append(c["color"])
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="markers+text", text=names, textposition="top center",
                             marker=dict(size=14, color=colors), textfont=dict(size=10)))
    fig.update_layout(xaxis_title="系统成本 (¥/Wh)", yaxis_title="国内毛利率 (%)",
                      margin=dict(l=20, r=20, t=30, b=20), plot_bgcolor="rgba(0,0,0,0)",
                      paper_bgcolor="rgba(0,0,0,0)")
    return fig


def industry_chart(data_list, title=""):
    """行业趋势图"""
    if not data_list:
        return go.Figure()
    df = pd.DataFrame(data_list)
    fig = px.line(df, x="period", y="metric_value", color="metric_name",
                  title=title, markers=True)
    fig.update_layout(hovermode="x unified", margin=dict(l=20, r=20, t=30, b=20),
                      legend=dict(font=dict(size=10)), plot_bgcolor="rgba(0,0,0,0)",
                      paper_bgcolor="rgba(0,0,0,0)")
    return fig


def ranking_chart(rankings):
    """行业排名横向柱状图"""
    top10 = sorted(rankings, key=lambda x: x["year_2025"] or 0, reverse=True)[:10]
    names = [r["company_name"] for r in top10]
    v24 = [r["year_2024"] or 0 for r in top10]
    v25 = [r["year_2025"] or 0 for r in top10]
    fig = go.Figure(data=[
        go.Bar(name="2024", y=names, x=v24, orientation="h", marker_color="rgba(0,0,0,0.08)"),
        go.Bar(name="2025", y=names, x=v25, orientation="h", marker_color="rgba(255,123,0,0.7)")
    ])
    fig.update_layout(barmode="group", margin=dict(l=20, r=20, t=30, b=20),
                      legend=dict(font=dict(size=10)), plot_bgcolor="rgba(0,0,0,0)",
                      paper_bgcolor="rgba(0,0,0,0)", yaxis=dict(autorange="reversed"))
    return fig


def hex_to_rgba(hex_color, alpha=0.2):
    """将 #RRGGBB 转为 rgba(r,g,b,a)"""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join([c*2 for c in hex_color])
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def company_trend_chart(data, periods, color, label="出货量(GWh)", y_key="total"):
    """单公司趋势图"""
    vals = [data.get(y, {}).get(y_key) for y in periods]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=periods, y=vals, name=label,
                             line=dict(color=color, width=3), mode="lines+markers",
                             fill="tozeroy", fillcolor=hex_to_rgba(color, 0.2), marker=dict(size=6)))
    fig.update_layout(margin=dict(l=20, r=20, t=10, b=20),
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    return fig


def cost_price_chart(cost_data, periods, color):
    """成本-单价-毛利图"""
    fig = go.Figure()
    for key, name, dash in [("system_cost", "系统成本", "solid"), ("domestic_price", "国内单价", "dash"),
                             ("export_price", "海外单价", "dot")]:
        vals = [cost_data.get(y, {}).get(key) for y in periods if y in cost_data]
        ys = [y for y in periods if y in cost_data]
        if any(v is not None for v in vals):
            fig.add_trace(go.Scatter(x=ys, y=vals, name=name,
                                     line=dict(dash=dash, width=2), mode="lines+markers"))
    fig.update_layout(margin=dict(l=20, r=20, t=10, b=20),
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    return fig
