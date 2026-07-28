"""Visualization — Dark-theme Plotly charts (Institutional grade)
2026E Forecast Support: dashed lines + lighter fills for projected data
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# ——— Theme constants ———
BG = "rgba(0,0,0,0)"
FONT_COLOR = "#8b949e"
GRID_COLOR = "rgba(48,54,61,0.4)"
MARGIN = dict(l=20, r=20, t=30, b=20)
LEGEND = dict(font=dict(color=FONT_COLOR, size=10))

# Color palette — gold + steel blue
GOLD = "rgba(201,169,110,0.9)"
GOLD_LIGHT = "rgba(201,169,110,0.35)"
STEEL = "rgba(91,141,184,0.9)"
STEEL_LIGHT = "rgba(91,141,184,0.35)"
DARK = "rgba(48,54,61,0.6)"

# Forecast styling
FORECAST_PERIOD = "2026E"
FORECAST_DASH = "dash"       # dashed line for forecast traces
FORECAST_FILL_ALPHA = 0.06   # lighter fill for forecast (vs 0.12 for historical)
FORECAST_MARKER_ALPHA = 0.55 # lighter markers for forecast
FORECAST_BAR_ALPHA = 0.50    # lighter bars for forecast


def hex_to_rgba(hex_color, alpha=0.2):
    """Convert hex color to rgba() string for Plotly compatibility"""
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


def _split_periods(periods):
    """Split periods into historical (solid) and forecast (dashed).
    Returns (hist_periods, fcst_periods)"""
    hist = [p for p in periods if p != FORECAST_PERIOD]
    fcst = [p for p in periods if p == FORECAST_PERIOD]
    return hist, fcst


# ================================================================
#  Shipment Trend — Multi-company line chart
# ================================================================

def ship_trend_chart(competitors, data_map, periods):
    """Multi-company shipment trend.
    Historical periods: solid lines + markers
    Forecast periods (2026E): dashed lines + lighter markers + lighter fill
    """
    hist_periods, fcst_periods = _split_periods(periods)
    fig = go.Figure()

    for comp in competitors:
        d = data_map.get(comp["cid"], {})
        color = comp["color"]
        rgba_color = hex_to_rgba(color, 0.9)
        rgba_fcst = hex_to_rgba(color, FORECAST_MARKER_ALPHA)

        # Historical trace — solid line
        hist_vals = [d.get(y, {}).get("total") for y in hist_periods]
        if any(v is not None for v in hist_vals):
            fig.add_trace(go.Scatter(
                x=hist_periods, y=hist_vals, name=comp["name"],
                line=dict(color=color, width=2.2), mode="lines+markers",
                marker=dict(size=5, color=color),
                legendgroup=comp["name"],
                showlegend=True,
            ))

        # Forecast trace — dashed line, lighter color, lighter fill
        fcst_vals = [d.get(y, {}).get("total") for y in fcst_periods]
        if any(v is not None for v in fcst_vals):
            # Connect from last historical point for continuity
            fcst_x = fcst_periods.copy()
            fcst_y = fcst_vals.copy()
            if hist_periods and hist_vals and hist_vals[-1] is not None:
                fcst_x = [hist_periods[-1]] + fcst_periods
                fcst_y = [hist_vals[-1]] + fcst_vals

            fig.add_trace(go.Scatter(
                x=fcst_x, y=fcst_y, name=f"{comp['name']} (E)",
                line=dict(color=rgba_fcst, width=2.2, dash=FORECAST_DASH),
                mode="lines+markers",
                marker=dict(size=5, color=rgba_fcst),
                fill="tozeroy",
                fillcolor=hex_to_rgba(color, FORECAST_FILL_ALPHA),
                legendgroup=comp["name"],
                showlegend=True,
            ))

    return _base_layout(fig)


# ================================================================
#  Shipment Stack Chart — Regional / Application breakdown
# ================================================================

def ship_stack_chart(competitors, data_map, period="2025", mode="region"):
    """Stacked bar: Domestic/Export or Residential/Utility/C&I.
    For forecast periods, bars use lighter alpha.
    """
    names = [c["name"] for c in competitors]
    is_forecast = (period == FORECAST_PERIOD)

    if mode == "region":
        alpha = FORECAST_BAR_ALPHA if is_forecast else 0.9
        d1 = [data_map.get(c["cid"], {}).get(period, {}).get("domestic", 0) or 0 for c in competitors]
        d2 = [data_map.get(c["cid"], {}).get(period, {}).get("export", 0) or 0 for c in competitors]
        fig = go.Figure(data=[
            go.Bar(name="Domestic", x=names, y=d1,
                   marker_color=f"rgba(201,169,110,{alpha})",
                   marker_line=dict(width=1, color="rgba(201,169,110,0.3)") if is_forecast else None),
            go.Bar(name="Export", x=names, y=d2,
                   marker_color=f"rgba(91,141,184,{alpha})",
                   marker_line=dict(width=1, color="rgba(91,141,184,0.3)") if is_forecast else None)
        ])
    else:
        alpha = FORECAST_BAR_ALPHA if is_forecast else 0.9
        d1 = [data_map.get(c["cid"], {}).get(period, {}).get("residential", 0) or 0 for c in competitors]
        d2 = [data_map.get(c["cid"], {}).get(period, {}).get("utility", 0) or 0 for c in competitors]
        d3 = [data_map.get(c["cid"], {}).get(period, {}).get("commercial", 0) or 0 for c in competitors]
        fig = go.Figure(data=[
            go.Bar(name="Residential", x=names, y=d1,
                   marker_color=f"rgba(201,169,110,{alpha})"),
            go.Bar(name="Utility-scale", x=names, y=d2,
                   marker_color=f"rgba(91,141,184,{alpha})"),
            go.Bar(name="C&I", x=names, y=d3,
                   marker_color=f"rgba(122,163,196,{alpha})")
        ])
    fig.update_layout(barmode="stack")
    if is_forecast:
        fig.update_layout(title=dict(text="▨ Forecast", font=dict(size=10, color="#c9a96e"),
                                      x=1, y=0.99, xanchor="right"))
    return _base_layout(fig)


# ================================================================
#  Financial Bar Chart — Year-over-year comparison
# ================================================================

def fin_bar_chart(competitors, data_map, field="revenue", year1="2024", year2="2025"):
    """Grouped bar chart comparing two years.
    If year2 is forecast, it uses lighter color + dashed border.
    """
    names = [c["name"] for c in competitors]
    v1 = [data_map.get(c["cid"], {}).get(year1, {}).get(field) or 0 for c in competitors]
    v2 = [data_map.get(c["cid"], {}).get(year2, {}).get(field) or 0 for c in competitors]

    y2_is_fcst = (year2 == FORECAST_PERIOD)
    y2_label = f"{year2}E" if y2_is_fcst else year2

    traces = [
        go.Bar(name=year1, x=names, y=v1, marker_color=DARK)
    ]

    if y2_is_fcst:
        traces.append(go.Bar(
            name=y2_label, x=names, y=v2,
            marker_color=f"rgba(201,169,110,{FORECAST_BAR_ALPHA})",
            marker_line=dict(width=1.5, color="rgba(201,169,110,0.5)"),
            marker_pattern_shape="/",
        ))
    else:
        traces.append(go.Bar(name=y2_label, x=names, y=v2, marker_color=GOLD))

    fig = go.Figure(data=traces)
    fig.update_layout(barmode="group")
    if y2_is_fcst:
        fig.update_layout(title=dict(text="▨ Forecast", font=dict(size=10, color="#c9a96e"),
                                      x=1, y=0.99, xanchor="right"))
    return _base_layout(fig)


# ================================================================
#  Quarterly Bar Chart — Q1-Q4 stack
# ================================================================

def qtr_bar_chart(competitors, data_map, field="rv", year="2025"):
    """Stacked quarterly bar chart.
    For forecast year (2026E), uses lighter/translucent colors.
    """
    names = [c["name"] for c in competitors]
    is_forecast = (year == FORECAST_PERIOD)

    if is_forecast:
        # Lighter, more translucent palette for forecast quarters
        q_colors = [
            f"rgba(201,169,110,{FORECAST_BAR_ALPHA})",
            f"rgba(91,141,184,{FORECAST_BAR_ALPHA})",
            f"rgba(201,169,110,{FORECAST_BAR_ALPHA - 0.1})",
            f"rgba(91,141,184,{FORECAST_BAR_ALPHA - 0.1})",
        ]
    else:
        q_colors = [GOLD, STEEL, GOLD_LIGHT, STEEL_LIGHT]

    q1 = [data_map.get(c["cid"], {}).get(year, {}).get(f"{field}_q1") or 0 for c in competitors]
    q2 = [data_map.get(c["cid"], {}).get(year, {}).get(f"{field}_q2") or 0 for c in competitors]
    q3 = [data_map.get(c["cid"], {}).get(year, {}).get(f"{field}_q3") or 0 for c in competitors]
    q4 = [data_map.get(c["cid"], {}).get(year, {}).get(f"{field}_q4") or 0 for c in competitors]

    fig = go.Figure(data=[
        go.Bar(name="Q1", x=names, y=q1, marker_color=q_colors[0]),
        go.Bar(name="Q2", x=names, y=q2, marker_color=q_colors[1]),
        go.Bar(name="Q3", x=names, y=q3, marker_color=q_colors[2]),
        go.Bar(name="Q4", x=names, y=q4, marker_color=q_colors[3])
    ])
    fig.update_layout(barmode="stack")
    if is_forecast:
        fig.update_layout(title=dict(text="▨ Forecast", font=dict(size=10, color="#c9a96e"),
                                      x=1, y=0.99, xanchor="right"))
    return _base_layout(fig)


# ================================================================
#  Cost-Margin Scatter
# ================================================================

def cost_margin_scatter(competitors, cost_map, margin_map, period="2025"):
    """Scatter plot: System Cost vs Domestic GM"""
    names, xs, ys, colors = [], [], [], []
    for c in competitors:
        co = cost_map.get(c["cid"], {}).get(period, {})
        if co.get("system_cost"):
            names.append(c["name"]); xs.append(co["system_cost"])
            ys.append(co.get("domestic_margin") or 0); colors.append(c["color"])
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="markers+text", text=names, textposition="top center",
                             marker=dict(size=12, color=colors, line=dict(width=1, color="#21262d")),
                             textfont=dict(size=10, color=FONT_COLOR)))
    fig.update_layout(xaxis_title="System Cost (RMB/Wh)", yaxis_title="Domestic GM (%)")
    if period == FORECAST_PERIOD:
        fig.update_layout(title=dict(text="▨ Forecast", font=dict(size=10, color="#c9a96e"),
                                      x=1, y=0.99, xanchor="right"))
    return _base_layout(fig)


# ================================================================
#  Industry Chart
# ================================================================

def industry_chart(data_list, title=""):
    """Line chart for industry time-series data."""
    if not data_list:
        return go.Figure()
    df = pd.DataFrame(data_list)
    fig = px.line(df, x="period", y="metric_value", color="metric_name", title=title, markers=True)
    return _base_layout(fig)


# ================================================================
#  Ranking Chart — Horizontal bar
# ================================================================

def ranking_chart(rankings):
    """Horizontal bar chart for rankings.
    Supports up to 3 years: 2024 (dark), 2025 (gold), 2026E (gold dashed).
    """
    top10 = sorted(rankings, key=lambda x: x.get("year_2025") or 0, reverse=True)[:10]
    names = [r["company_name"] for r in top10]
    v24 = [r.get("year_2024") or 0 for r in top10]
    v25 = [r.get("year_2025") or 0 for r in top10]

    traces = [
        go.Bar(name="2024", y=names, x=v24, orientation="h", marker_color=DARK),
        go.Bar(name="2025", y=names, x=v25, orientation="h", marker_color=GOLD),
    ]

    # 2026E if available
    if any(r.get("year_2026") for r in top10):
        v26 = [r.get("year_2026") or 0 for r in top10]
        traces.append(go.Bar(
            name="2026E", y=names, x=v26, orientation="h",
            marker_color=f"rgba(201,169,110,{FORECAST_BAR_ALPHA})",
            marker_line=dict(width=1.5, color="rgba(201,169,110,0.5)"),
            marker_pattern_shape="/",
        ))

    fig = go.Figure(data=traces)
    fig.update_layout(barmode="group", yaxis=dict(autorange="reversed"))
    return _base_layout(fig)


# ================================================================
#  Company Trend — Single company line chart
# ================================================================

def company_trend_chart(data, periods, color, label="GWh", y_key="total"):
    """Single-company trend line.
    Historical: solid line + solid fill
    Forecast (2026E): dashed line + lighter fill
    """
    hist_periods, fcst_periods = _split_periods(periods)
    fig = go.Figure()

    # Historical trace
    hist_vals = [data.get(y, {}).get(y_key) for y in hist_periods]
    if any(v is not None for v in hist_vals):
        fig.add_trace(go.Scatter(
            x=hist_periods, y=hist_vals, name=label,
            line=dict(color=color, width=2.5), mode="lines+markers",
            fill="tozeroy", fillcolor=hex_to_rgba(color, 0.12),
            marker=dict(size=5),
        ))

    # Forecast trace — connect from last historical point
    fcst_vals = [data.get(y, {}).get(y_key) for y in fcst_periods]
    if any(v is not None for v in fcst_vals):
        fcst_x = fcst_periods.copy()
        fcst_y = fcst_vals.copy()
        if hist_periods and hist_vals and hist_vals[-1] is not None:
            fcst_x = [hist_periods[-1]] + fcst_periods
            fcst_y = [hist_vals[-1]] + fcst_vals

        fig.add_trace(go.Scatter(
            x=fcst_x, y=fcst_y, name=f"{label} (E)",
            line=dict(color=hex_to_rgba(color, FORECAST_MARKER_ALPHA),
                       width=2.5, dash=FORECAST_DASH),
            mode="lines+markers",
            marker=dict(size=5, color=hex_to_rgba(color, FORECAST_MARKER_ALPHA)),
            fill="tozeroy",
            fillcolor=hex_to_rgba(color, FORECAST_FILL_ALPHA),
        ))

    return _base_layout(fig)


# ================================================================
#  Cost / Price / Margin Chart
# ================================================================

def cost_price_chart(cost_data, periods, color):
    """Multi-line: System Cost, Domestic ASP, Export ASP.
    Forecast periods (2026E) use dashed lines.
    """
    fig = go.Figure()
    hist_periods, fcst_periods = _split_periods(periods)

    line_configs = [
        ("system_cost", "System Cost", "solid"),
        ("domestic_price", "Domestic ASP", "dash"),
        ("export_price", "Export ASP", "dot"),
    ]

    for key, name, dash_style in line_configs:
        # Historical
        hist_ys = [p for p in hist_periods if p in cost_data]
        hist_vals = [cost_data.get(y, {}).get(key) for y in hist_ys]
        if any(v is not None for v in hist_vals):
            fig.add_trace(go.Scatter(
                x=hist_ys, y=hist_vals, name=name,
                line=dict(dash=dash_style, width=2), mode="lines+markers",
                legendgroup=name,
            ))

        # Forecast
        fcst_ys = [p for p in fcst_periods if p in cost_data]
        fcst_vals = [cost_data.get(y, {}).get(key) for y in fcst_ys]
        if any(v is not None for v in fcst_vals):
            # Connect from last historical
            fcst_x = fcst_ys.copy()
            fcst_y = fcst_vals.copy()
            if hist_ys and hist_vals:
                last_hist_val = next((v for v in reversed(hist_vals) if v is not None), None)
                if last_hist_val is not None:
                    fcst_x = [hist_ys[-1]] + fcst_ys
                    fcst_y = [last_hist_val] + fcst_vals

            fig.add_trace(go.Scatter(
                x=fcst_x, y=fcst_y, name=f"{name} (E)",
                line=dict(dash=dash_style, width=2,
                           color=hex_to_rgba(color, FORECAST_MARKER_ALPHA)),
                mode="lines+markers",
                marker=dict(size=5, color=hex_to_rgba(color, FORECAST_MARKER_ALPHA)),
                legendgroup=name,
            ))

    return _base_layout(fig)
