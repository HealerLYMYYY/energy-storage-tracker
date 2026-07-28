"""Visualization — Dark-theme Plotly charts (Institutional grade)"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# ——— Theme constants ———
BG = "rgba(0,0,0,0)"
FONT_COLOR = "#8b949e"
GRID_COLOR = "rgba(48,54,61,0.4)"
MARGIN = dict(l=20, r=20, t=30, b=20)
LEGEND = dict(font=dict(color=FONT_COLOR, size=10))
DARK_TEMPLATE = dict(
    layout=go.Layout(
        plot_bgcolor=BG, paper_bgcolor=BG,
        font=dict(color=FONT_COLOR),
        xaxis=dict(gridcolor=GRID_COLOR, zeroline=False),
        yaxis=dict(gridcolor=GRID_COLOR, zeroline=False),
    )
)

# Color palette — gold + steel blue
GOLD = "rgba(201,169,110,0.9)"
GOLD_LIGHT = "rgba(201,169,110,0.35)"
STEEL = "rgba(91,141,184,0.9)"
STEEL_LIGHT = "rgba(91,141,184,0.35)"
DARK = "rgba(48,54,61,0.6)"


def hex_to_rgba(hex_color, alpha=0.2):
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join([c*2 for c in hex_color])
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def _base_layout(fig, **kw):
    fig.update_layout(hovermode="x unified", margin=MARGIN, legend=LEGEND,
                      plot_bgcolor=BG, paper_bgcolor=BG, font=dict(color=FONT_COLOR),
                      xaxis=dict(gridcolor=GRID_COLOR, zeroline=False),
                      yaxis=dict(gridcolor=GRID_COLOR, zeroline=False), **kw)
    return fig


def ship_trend_chart(competitors, data_map, periods):
    fig = go.Figure()
    for comp in competitors:
        d = data_map.get(comp["cid"], {})
        vals = [d.get(y, {}).get("total") for y in periods]
        fig.add_trace(go.Scatter(x=periods, y=vals, name=comp["name"],
                                 line=dict(color=comp["color"], width=2), mode="lines+markers", marker=dict(size=5)))
    return _base_layout(fig)


def ship_stack_chart(competitors, data_map, period="2025", mode="region"):
    names = [c["name"] for c in competitors]
    if mode == "region":
        d1 = [data_map.get(c["cid"], {}).get(period, {}).get("domestic", 0) or 0 for c in competitors]
        d2 = [data_map.get(c["cid"], {}).get(period, {}).get("export", 0) or 0 for c in competitors]
        fig = go.Figure(data=[
            go.Bar(name="Domestic", x=names, y=d1, marker_color=GOLD),
            go.Bar(name="Export", x=names, y=d2, marker_color=STEEL)
        ])
    else:
        d1 = [data_map.get(c["cid"], {}).get(period, {}).get("residential", 0) or 0 for c in competitors]
        d2 = [data_map.get(c["cid"], {}).get(period, {}).get("utility", 0) or 0 for c in competitors]
        d3 = [data_map.get(c["cid"], {}).get(period, {}).get("commercial", 0) or 0 for c in competitors]
        fig = go.Figure(data=[
            go.Bar(name="Residential", x=names, y=d1, marker_color=GOLD),
            go.Bar(name="Utility-scale", x=names, y=d2, marker_color=STEEL),
            go.Bar(name="C&I", x=names, y=d3, marker_color="rgba(122,163,196,0.9)")
        ])
    fig.update_layout(barmode="stack")
    return _base_layout(fig)


def fin_bar_chart(competitors, data_map, field="revenue", year1="2024", year2="2025"):
    names = [c["name"] for c in competitors]
    v1 = [data_map.get(c["cid"], {}).get(year1, {}).get(field) or 0 for c in competitors]
    v2 = [data_map.get(c["cid"], {}).get(year2, {}).get(field) or 0 for c in competitors]
    fig = go.Figure(data=[
        go.Bar(name=year1, x=names, y=v1, marker_color=DARK),
        go.Bar(name=f"{year2}E", x=names, y=v2, marker_color=GOLD)
    ])
    fig.update_layout(barmode="group")
    return _base_layout(fig)


def qtr_bar_chart(competitors, data_map, field="rv", year="2025"):
    names = [c["name"] for c in competitors]
    colors = [GOLD, STEEL, GOLD_LIGHT, STEEL_LIGHT]
    q1 = [data_map.get(c["cid"], {}).get(year, {}).get(f"{field}_q1") or 0 for c in competitors]
    q2 = [data_map.get(c["cid"], {}).get(year, {}).get(f"{field}_q2") or 0 for c in competitors]
    q3 = [data_map.get(c["cid"], {}).get(year, {}).get(f"{field}_q3") or 0 for c in competitors]
    q4 = [data_map.get(c["cid"], {}).get(year, {}).get(f"{field}_q4") or 0 for c in competitors]
    fig = go.Figure(data=[
        go.Bar(name="Q1", x=names, y=q1, marker_color=GOLD),
        go.Bar(name="Q2", x=names, y=q2, marker_color=STEEL),
        go.Bar(name="Q3", x=names, y=q3, marker_color=GOLD_LIGHT),
        go.Bar(name="Q4", x=names, y=q4, marker_color=STEEL_LIGHT)
    ])
    fig.update_layout(barmode="stack")
    return _base_layout(fig)


def cost_margin_scatter(competitors, cost_map, margin_map):
    names, xs, ys, colors = [], [], [], []
    for c in competitors:
        co = cost_map.get(c["cid"], {}).get("2025", {})
        if co.get("system_cost"):
            names.append(c["name"]); xs.append(co["system_cost"])
            ys.append(co.get("domestic_margin") or 0); colors.append(c["color"])
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="markers+text", text=names, textposition="top center",
                             marker=dict(size=12, color=colors, line=dict(width=1, color="#21262d")),
                             textfont=dict(size=10, color=FONT_COLOR)))
    fig.update_layout(xaxis_title="System Cost (RMB/Wh)", yaxis_title="Domestic GM (%)")
    return _base_layout(fig)


def industry_chart(data_list, title=""):
    if not data_list:
        return go.Figure()
    df = pd.DataFrame(data_list)
    fig = px.line(df, x="period", y="metric_value", color="metric_name", title=title, markers=True)
    return _base_layout(fig)


def ranking_chart(rankings):
    top10 = sorted(rankings, key=lambda x: x["year_2025"] or 0, reverse=True)[:10]
    names = [r["company_name"] for r in top10]
    v24 = [r["year_2024"] or 0 for r in top10]
    v25 = [r["year_2025"] or 0 for r in top10]
    fig = go.Figure(data=[
        go.Bar(name="2024", y=names, x=v24, orientation="h", marker_color=DARK),
        go.Bar(name="2025E", y=names, x=v25, orientation="h", marker_color=GOLD)
    ])
    fig.update_layout(barmode="group", yaxis=dict(autorange="reversed"))
    return _base_layout(fig)


def company_trend_chart(data, periods, color, label="GWh", y_key="total"):
    vals = [data.get(y, {}).get(y_key) for y in periods]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=periods, y=vals, name=label,
                             line=dict(color=color, width=2.5), mode="lines+markers",
                             fill="tozeroy", fillcolor=hex_to_rgba(color, 0.12), marker=dict(size=5)))
    return _base_layout(fig)


def cost_price_chart(cost_data, periods, color):
    fig = go.Figure()
    for key, name, dash in [("system_cost", "System Cost", "solid"),
                             ("domestic_price", "Domestic ASP", "dash"),
                             ("export_price", "Export ASP", "dot")]:
        vals = [cost_data.get(y, {}).get(key) for y in periods if y in cost_data]
        ys = [y for y in periods if y in cost_data]
        if any(v is not None for v in vals):
            fig.add_trace(go.Scatter(x=ys, y=vals, name=name, line=dict(dash=dash, width=2), mode="lines+markers"))
    return _base_layout(fig)
