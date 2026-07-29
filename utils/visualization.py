"""可视化 — 品牌色系 Plotly 图表
主色: 橙 #FF7900 | 辅助: 黄#EEB83F 绿#54B244 青#55BABE 蓝#6E92FF 深青#2B686F
2026E: 季度堆积柱状图（Q1-Q4 相加 = 全年预测）
"""

import datetime
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# ——— 主题常量 ———
BG = "rgba(0,0,0,0)"
FONT_COLOR = "#9a9a9a"
GRID_COLOR = "rgba(58,64,72,0.4)"
MARGIN = dict(l=20, r=20, t=30, b=20)
LEGEND = dict(font=dict(color=FONT_COLOR, size=10))

# ——— 品牌色板 ———
ORANGE = "rgba(255,121,0,0.92)"      # 主橙
ORANGE_LIGHT = "rgba(255,121,0,0.40)"
YELLOW = "rgba(238,184,63,0.92)"     # 黄
GREEN = "rgba(84,178,68,0.92)"       # 绿
TEAL = "rgba(85,186,190,0.92)"       # 青
BLUE = "rgba(110,146,255,0.92)"      # 蓝
DARKTEAL = "rgba(43,104,111,0.92)"   # 深青
GRAY = "rgba(96,96,96,0.60)"         # 灰（历史对比）
DARK = "rgba(58,64,72,0.6)"

# 季度配色（Q1→Q4 由暖到冷，符合时间推进感）
Q_COLORS = [
    "rgba(255,121,0,0.92)",   # Q1 橙
    "rgba(238,184,63,0.92)",  # Q2 黄
    "rgba(85,186,190,0.85)",  # Q3 青
    "rgba(110,146,255,0.85)", # Q4 蓝
]
# 未来季度（预测）透明度
Q_COLORS_FUTURE = [
    "rgba(255,121,0,0.92)",
    "rgba(238,184,63,0.92)",
    "rgba(85,186,190,0.45)",
    "rgba(110,146,255,0.45)",
]

FORECAST_PERIOD = "2026E"
FORECAST_DASH = "dash"
FORECAST_FILL_ALPHA = 0.06
FORECAST_MARKER_ALPHA = 0.55
FORECAST_BAR_ALPHA = 0.50


def current_completed_quarters():
    """根据当前日期计算 2026 已结束的季度（Q3进行中 → Q1,Q2已完成）"""
    now = datetime.datetime.now()
    if now.year > 2026:
        return ["Q1", "Q2", "Q3", "Q4"]
    if now.year < 2026:
        return []
    current_q = (now.month - 1) // 3 + 1  # 当前进行中季度
    return [f"Q{i}" for i in range(1, current_q)]  # 已完成的季度


def hex_to_rgba(hex_color, alpha=0.2):
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join([c * 2 for c in hex_color])
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def _base_layout(fig, **kw):
    fig.update_layout(hovermode="x unified", margin=MARGIN, legend=LEGEND,
                      plot_bgcolor=BG, paper_bgcolor=BG, font=dict(color=FONT_COLOR),
                      xaxis=dict(gridcolor=GRID_COLOR, zeroline=False),
                      yaxis=dict(gridcolor=GRID_COLOR, zeroline=False), **kw)
    return fig


def _split_periods(periods):
    hist = [p for p in periods if p != FORECAST_PERIOD]
    fcst = [p for p in periods if p == FORECAST_PERIOD]
    return hist, fcst


# ================================================================
#  出货趋势 — 多公司折线（历史实线 + 2026E 虚线）
# ================================================================

def ship_trend_chart(competitors, data_map, periods):
    hist_periods, fcst_periods = _split_periods(periods)
    fig = go.Figure()

    for comp in competitors:
        d = data_map.get(comp["cid"], {})
        color = comp["color"]

        hist_vals = [d.get(y, {}).get("total") for y in hist_periods]
        if any(v is not None for v in hist_vals):
            fig.add_trace(go.Scatter(
                x=hist_periods, y=hist_vals, name=comp["name"],
                line=dict(color=color, width=2.2), mode="lines+markers",
                marker=dict(size=5, color=color),
                legendgroup=comp["name"], showlegend=True,
            ))

        fcst_vals = [d.get(y, {}).get("total") for y in fcst_periods]
        if any(v is not None for v in fcst_vals):
            fcst_x = fcst_periods.copy()
            fcst_y = fcst_vals.copy()
            if hist_periods and hist_vals and hist_vals[-1] is not None:
                fcst_x = [hist_periods[-1]] + fcst_periods
                fcst_y = [hist_vals[-1]] + fcst_vals

            fig.add_trace(go.Scatter(
                x=fcst_x, y=fcst_y, name=f"{comp['name']} (E)",
                line=dict(color=hex_to_rgba(color, FORECAST_MARKER_ALPHA), width=2.2, dash=FORECAST_DASH),
                mode="lines+markers",
                marker=dict(size=5, color=hex_to_rgba(color, FORECAST_MARKER_ALPHA)),
                fill="tozeroy", fillcolor=hex_to_rgba(color, FORECAST_FILL_ALPHA),
                legendgroup=comp["name"], showlegend=True,
            ))

    return _base_layout(fig)


# ================================================================
#  出货结构堆积（区域/应用）
# ================================================================

def ship_stack_chart(competitors, data_map, period="2025", mode="region"):
    names = [c["name"] for c in competitors]
    is_forecast = (period == FORECAST_PERIOD)
    alpha = FORECAST_BAR_ALPHA if is_forecast else 0.92

    if mode == "region":
        d1 = [data_map.get(c["cid"], {}).get(period, {}).get("domestic", 0) or 0 for c in competitors]
        d2 = [data_map.get(c["cid"], {}).get(period, {}).get("export", 0) or 0 for c in competitors]
        fig = go.Figure(data=[
            go.Bar(name="国内", x=names, y=d1, marker_color=f"rgba(255,121,0,{alpha})"),
            go.Bar(name="海外", x=names, y=d2, marker_color=f"rgba(110,146,255,{alpha})")
        ])
    else:
        d1 = [data_map.get(c["cid"], {}).get(period, {}).get("residential", 0) or 0 for c in competitors]
        d2 = [data_map.get(c["cid"], {}).get(period, {}).get("utility", 0) or 0 for c in competitors]
        d3 = [data_map.get(c["cid"], {}).get(period, {}).get("commercial", 0) or 0 for c in competitors]
        fig = go.Figure(data=[
            go.Bar(name="户用", x=names, y=d1, marker_color=f"rgba(255,121,0,{alpha})"),
            go.Bar(name="大储", x=names, y=d2, marker_color=f"rgba(110,146,255,{alpha})"),
            go.Bar(name="工商业", x=names, y=d3, marker_color=f"rgba(85,186,190,{alpha})")
        ])
    fig.update_layout(barmode="stack")
    if is_forecast:
        fig.update_layout(title=dict(text="▨ 预测", font=dict(size=10, color="#FF7900"),
                                     x=1, y=0.99, xanchor="right"))
    return _base_layout(fig)


# ================================================================
#  财务对比柱状图 — 年度对比
# ================================================================

def fin_bar_chart(competitors, data_map, field="revenue", year1="2024", year2="2025"):
    names = [c["name"] for c in competitors]
    v1 = [data_map.get(c["cid"], {}).get(year1, {}).get(field) or 0 for c in competitors]
    v2 = [data_map.get(c["cid"], {}).get(year2, {}).get(field) or 0 for c in competitors]

    y2_is_fcst = (year2 == FORECAST_PERIOD)
    y2_label = f"{year2}" if y2_is_fcst else year2

    traces = [go.Bar(name=year1, x=names, y=v1, marker_color=GRAY)]
    if y2_is_fcst:
        traces.append(go.Bar(
            name=y2_label, x=names, y=v2,
            marker_color=f"rgba(255,121,0,{FORECAST_BAR_ALPHA})",
            marker_line=dict(width=1.5, color="rgba(255,121,0,0.5)"),
            marker_pattern_shape="/",
        ))
    else:
        traces.append(go.Bar(name=y2_label, x=names, y=v2, marker_color=ORANGE))

    fig = go.Figure(data=traces)
    fig.update_layout(barmode="group")
    if y2_is_fcst:
        fig.update_layout(title=dict(text="▨ 预测", font=dict(size=10, color="#FF7900"),
                                     x=1, y=0.99, xanchor="right"))
    return _base_layout(fig)


# ================================================================
#  季度堆积柱状图 — 多公司 × Q1-Q4（核心新图表）
# ================================================================

def quarterly_stack_chart(competitors, qdata_map, metric_label="GWh"):
    """x = Q1..Q4，每个季度的柱子按公司堆积。
    qdata_map: {cid: {"Q1": v, "Q2": v, "Q3": v, "Q4": v}}
    已完成季度实色，未来季度半透明（预测）。"""
    quarters = ["Q1", "Q2", "Q3", "Q4"]
    completed = current_completed_quarters()
    fig = go.Figure()

    for comp in competitors:
        qd = qdata_map.get(comp["cid"], {})
        vals = [qd.get(q) or 0 for q in quarters]
        if not any(vals):
            continue
        # 每根柱子按季度调整透明度（未来季度=预测=半透明）
        color_hex = comp["color"]
        bar_colors = [
            hex_to_rgba(color_hex, 0.92) if q in completed else hex_to_rgba(color_hex, 0.42)
            for q in quarters
        ]
        fig.add_trace(go.Bar(
            name=comp["name"], x=quarters, y=vals,
            marker=dict(color=bar_colors),
        ))

    fig.update_layout(barmode="stack")
    fig.update_layout(
        annotations=[dict(
            text="半透明 = 未来季度预测", xref="paper", yref="paper",
            x=1, y=1.06, xanchor="right", showarrow=False,
            font=dict(size=10, color="#FF7900"))])
    return _base_layout(fig)


# ================================================================
#  年度+季度组合图 — 单公司（历史年度柱 + 2026E 季度堆积）
# ================================================================

def combo_annual_quarterly(annual_data, quarters_data, color, label="GWh", unit=""):
    """单公司：2022-2025 年度柱 + 2026E 一根堆积柱（Q1-Q4 分段）。
    annual_data: {"2022": v, "2023": v, ...}
    quarters_data: {"Q1": v, "Q2": v, "Q3": v, "Q4": v}
    """
    years = ["2022", "2023", "2024", "2025"]
    quarters = ["Q1", "Q2", "Q3", "Q4"]
    completed = current_completed_quarters()

    fig = go.Figure()

    # 历史年度柱（实色）
    annual_vals = [annual_data.get(y) for y in years]
    fig.add_trace(go.Bar(
        x=years, y=annual_vals, name=label,
        marker_color=hex_to_rgba(color, 0.85),
    ))

    # 2026E 季度堆积
    q_colors = []
    for i, q in enumerate(quarters):
        base = Q_COLORS[i]
        if q in completed:
            q_colors.append(base)
        else:
            q_colors.append(Q_COLORS_FUTURE[i])

    for i, q in enumerate(quarters):
        v = quarters_data.get(q)
        fig.add_trace(go.Bar(
            x=["2026E"], y=[v or 0], name=f"2026 {q}",
            marker_color=q_colors[i],
        ))

    fig.update_layout(barmode="relative")
    fig.update_layout(
        annotations=[dict(
            text="2026E = Q1+Q2+Q3+Q4 堆积", xref="paper", yref="paper",
            x=1, y=1.06, xanchor="right", showarrow=False,
            font=dict(size=10, color="#FF7900"))])
    if unit:
        fig.update_layout(yaxis_title=unit)
    return _base_layout(fig)


# ================================================================
#  季度利润率趋势 — 2026 动态展示
# ================================================================

def margin_quarterly_chart(fin_2026, hist_fin, color):
    """季度净利率折线（2026 各季度）+ 年度毛利率参考线 + 历史净利率点。
    fin_2026: {"rv_q1":.., "np_q1":.., "gross_margin":..}
    hist_fin: {"2022": {"net_margin":..}, ...}
    """
    quarters = ["Q1", "Q2", "Q3", "Q4"]
    completed = current_completed_quarters()
    fig = go.Figure()

    # 季度净利率（计算值）
    nm_q = []
    for i in range(1, 5):
        rv = fin_2026.get(f"rv_q{i}") or 0
        np_ = fin_2026.get(f"np_q{i}")
        nm_q.append(np_ / rv * 100 if (np_ is not None and rv) else None)

    # 已完成季度实线
    done_x = [q for q in quarters if q in completed]
    done_y = [nm_q[quarters.index(q)] for q in done_x]
    if any(v is not None for v in done_y):
        fig.add_trace(go.Scatter(
            x=done_x, y=done_y, name="季度净利率",
            line=dict(color=hex_to_rgba(color, 0.95), width=2.5),
            mode="lines+markers", marker=dict(size=7),
        ))

    # 未来季度虚线（从最后一个已完成点连接）
    fcst_x = [q for q in quarters if q not in completed]
    if fcst_x:
        fx = ([done_x[-1]] if done_x else []) + fcst_x
        fy = ([done_y[-1]] if done_y else []) + [nm_q[quarters.index(q)] for q in fcst_x]
        fig.add_trace(go.Scatter(
            x=fx, y=fy, name="净利率 (预测)",
            line=dict(color=hex_to_rgba(color, 0.5), width=2.5, dash="dash"),
            mode="lines+markers", marker=dict(size=7, color=hex_to_rgba(color, 0.5)),
        ))

    # 2026E 毛利率参考线（年度预测值）
    gm = fin_2026.get("gross_margin")
    if gm:
        fig.add_hline(y=gm, line=dict(color="rgba(238,184,63,0.6)", width=1.5, dash="dot"),
                      annotation_text=f"毛利率 {gm:.1f}%", annotation_font=dict(size=9, color="#EEB83F"),
                      annotation_position="top right")

    fig.update_layout(yaxis_title="%")
    return _base_layout(fig)


# ================================================================
#  季度收入柱状图（旧版兼容，内部使用）
# ================================================================

def qtr_bar_chart(competitors, data_map, field="rv", year="2025"):
    names = [c["name"] for c in competitors]
    is_forecast = (year == FORECAST_PERIOD)
    alpha = FORECAST_BAR_ALPHA if is_forecast else 0.92

    q_colors = [
        f"rgba(255,121,0,{alpha})",
        f"rgba(238,184,63,{alpha})",
        f"rgba(85,186,190,{alpha})",
        f"rgba(110,146,255,{alpha})",
    ]

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
        fig.update_layout(title=dict(text="▨ 预测", font=dict(size=10, color="#FF7900"),
                                     x=1, y=0.99, xanchor="right"))
    return _base_layout(fig)


# ================================================================
#  成本-毛利散点
# ================================================================

def cost_margin_scatter(competitors, cost_map, margin_map, period="2025"):
    names, xs, ys, colors = [], [], [], []
    for c in competitors:
        co = cost_map.get(c["cid"], {}).get(period, {})
        if co.get("system_cost"):
            names.append(c["name"]); xs.append(co["system_cost"])
            ys.append(co.get("domestic_margin") or 0); colors.append(c["color"])
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="markers+text", text=names, textposition="top center",
                             marker=dict(size=12, color=colors, line=dict(width=1, color="#2a2f36")),
                             textfont=dict(size=10, color=FONT_COLOR)))
    fig.update_layout(xaxis_title="系统成本 (元/Wh)", yaxis_title="国内毛利率 (%)")
    if period == FORECAST_PERIOD:
        fig.update_layout(title=dict(text="▨ 预测", font=dict(size=10, color="#FF7900"),
                                     x=1, y=0.99, xanchor="right"))
    return _base_layout(fig)


# ================================================================
#  行业图表
# ================================================================

def industry_chart(data_list, title=""):
    if not data_list:
        return go.Figure()
    df = pd.DataFrame(data_list)
    fig = px.line(df, x="period", y="metric_value", color="metric_name", title=title, markers=True)
    return _base_layout(fig)


# ================================================================
#  排名图
# ================================================================

def ranking_chart(rankings):
    top10 = sorted(rankings, key=lambda x: x.get("year_2025") or 0, reverse=True)[:10]
    names = [r["company_name"] for r in top10]
    v24 = [r.get("year_2024") or 0 for r in top10]
    v25 = [r.get("year_2025") or 0 for r in top10]

    traces = [
        go.Bar(name="2024", y=names, x=v24, orientation="h", marker_color=GRAY),
        go.Bar(name="2025", y=names, x=v25, orientation="h", marker_color=ORANGE),
    ]

    if any(r.get("year_2026") for r in top10):
        v26 = [r.get("year_2026") or 0 for r in top10]
        traces.append(go.Bar(
            name="2026E", y=names, x=v26, orientation="h",
            marker_color=f"rgba(255,121,0,{FORECAST_BAR_ALPHA})",
            marker_line=dict(width=1.5, color="rgba(255,121,0,0.5)"),
            marker_pattern_shape="/",
        ))

    fig = go.Figure(data=traces)
    fig.update_layout(barmode="group", yaxis=dict(autorange="reversed"))
    return _base_layout(fig)


# ================================================================
#  单公司趋势线（历史+预测）
# ================================================================

def company_trend_chart(data, periods, color, label="GWh", y_key="total"):
    hist_periods, fcst_periods = _split_periods(periods)
    fig = go.Figure()

    hist_vals = [data.get(y, {}).get(y_key) for y in hist_periods]
    if any(v is not None for v in hist_vals):
        fig.add_trace(go.Scatter(
            x=hist_periods, y=hist_vals, name=label,
            line=dict(color=color, width=2.5), mode="lines+markers",
            fill="tozeroy", fillcolor=hex_to_rgba(color, 0.10),
            marker=dict(size=5),
        ))

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
            fill="tozeroy", fillcolor=hex_to_rgba(color, FORECAST_FILL_ALPHA),
        ))

    return _base_layout(fig)


# ================================================================
#  成本/价格/毛利线
# ================================================================

def cost_price_chart(cost_data, periods, color):
    fig = go.Figure()
    hist_periods, fcst_periods = _split_periods(periods)

    line_configs = [
        ("system_cost", "系统成本", "solid"),
        ("domestic_price", "国内均价", "dash"),
        ("export_price", "海外均价", "dot"),
    ]

    for key, name, dash_style in line_configs:
        hist_ys = [p for p in hist_periods if p in cost_data]
        hist_vals = [cost_data.get(y, {}).get(key) for y in hist_ys]
        if any(v is not None for v in hist_vals):
            fig.add_trace(go.Scatter(
                x=hist_ys, y=hist_vals, name=name,
                line=dict(dash=dash_style, width=2), mode="lines+markers",
                legendgroup=name,
            ))

        fcst_ys = [p for p in fcst_periods if p in cost_data]
        fcst_vals = [cost_data.get(y, {}).get(key) for y in fcst_ys]
        if any(v is not None for v in fcst_vals):
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
