"""可视化 — 高级莫兰迪色系 Plotly 图表
参考 BCG / McKinsey 机构风格：低饱和、克制、信息密度高
2026E: 季度堆积柱状图（Q1-Q4 相加 = 全年预测）
"""

import datetime
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# ——— 主题常量 ———
BG = "rgba(0,0,0,0)"
FONT_COLOR = "#9a9a9a"
TITLE_COLOR = "#ECECEC"
GRID_COLOR = "rgba(58,64,72,0.35)"
MARGIN = dict(l=20, r=20, t=50, b=20)
LEGEND_TOP = dict(
    orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
    font=dict(color=FONT_COLOR, size=10), bgcolor="rgba(0,0,0,0)",
    bordercolor="rgba(0,0,0,0)", borderwidth=0
)
LEGEND_RIGHT = dict(
    orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02,
    font=dict(color=FONT_COLOR, size=10), bgcolor="rgba(0,0,0,0)"
)

# ——— 品牌色板（莫兰迪 / 低饱和） ———
ORANGE = "#C9702A"       # 主橙（克制）
ORANGE_LIGHT = "#DDA470"  # 浅橙
YELLOW = "#C9A227"
GREEN = "#7A9B76"
TEAL = "#5A9A8F"
BLUE = "#5A7A96"
PURPLE = "#8B7DA8"
RED = "#B85C5C"
TAN = "#A68B6A"
STEEL = "#6A7B8A"
GRAY = "#6B7280"         # 历史对比/次要

# 季度配色（Q1→Q4：暖 → 冷，时间推进感，均低饱和）
Q_COLORS = {
    "Q1": "#C9702A",   # 暖橙
    "Q2": "#C9A227",   # 暖黄
    "Q3": "#5A9A8F",   # 青绿
    "Q4": "#5A7A96",   # 雾蓝
}
# 未来季度（预测）：同色相但更浅更柔和，避免在深色背景变浑浊
Q_COLORS_FUTURE = {
    "Q1": "#DDA470",
    "Q2": "#D6B85A",
    "Q3": "#85B5AC",
    "Q4": "#8AA3B8",
}

FORECAST_PERIOD = "2026E"
FORECAST_DASH = "dash"
FORECAST_FILL_ALPHA = 0.08
FORECAST_MARKER_ALPHA = 0.55
FORECAST_BAR_ALPHA = 0.55


def current_completed_quarters():
    """根据当前日期计算 2026 已结束的季度（Q3进行中 → Q1,Q2已完成）"""
    now = datetime.datetime.now()
    if now.year > 2026:
        return ["Q1", "Q2", "Q3", "Q4"]
    if now.year < 2026:
        return []
    current_q = (now.month - 1) // 3 + 1
    return [f"Q{i}" for i in range(1, current_q)]


def hex_to_rgba(hex_color, alpha=0.2):
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join([c * 2 for c in hex_color])
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def _base_layout(fig, height=420, legend=None, y_title=None, x_title=None, **kw):
    fig.update_layout(
        height=height,
        hovermode="x unified",
        margin=MARGIN,
        legend=legend or LEGEND_TOP,
        plot_bgcolor=BG,
        paper_bgcolor=BG,
        font=dict(color=FONT_COLOR, size=11, family="Inter, -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif"),
        xaxis=dict(gridcolor=GRID_COLOR, zeroline=False, title=x_title),
        yaxis=dict(gridcolor=GRID_COLOR, zeroline=False, title=y_title),
        **kw
    )
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
                line=dict(color=color, width=2.4), mode="lines+markers",
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
                line=dict(color=hex_to_rgba(color, 0.70), width=2.4, dash=FORECAST_DASH),
                mode="lines+markers",
                marker=dict(size=5, color=hex_to_rgba(color, 0.70)),
                fill="tozeroy", fillcolor=hex_to_rgba(color, FORECAST_FILL_ALPHA),
                legendgroup=comp["name"], showlegend=True,
            ))

    return _base_layout(fig, height=380, y_title="GWh")


# ================================================================
#  出货结构堆积（区域/应用）
# ================================================================

def ship_stack_chart(competitors, data_map, period="2025", mode="region"):
    names = [c["name"] for c in competitors]
    is_forecast = (period == FORECAST_PERIOD)
    alpha = FORECAST_BAR_ALPHA if is_forecast else 1.0

    def _color(hex_c, a):
        return hex_to_rgba(hex_c, a)

    if mode == "region":
        d1 = [data_map.get(c["cid"], {}).get(period, {}).get("domestic", 0) or 0 for c in competitors]
        d2 = [data_map.get(c["cid"], {}).get(period, {}).get("export", 0) or 0 for c in competitors]
        fig = go.Figure(data=[
            go.Bar(name="国内", x=names, y=d1, marker_color=_color(ORANGE, alpha)),
            go.Bar(name="海外", x=names, y=d2, marker_color=_color(BLUE, alpha))
        ])
    else:
        d1 = [data_map.get(c["cid"], {}).get(period, {}).get("residential", 0) or 0 for c in competitors]
        d2 = [data_map.get(c["cid"], {}).get(period, {}).get("utility", 0) or 0 for c in competitors]
        d3 = [data_map.get(c["cid"], {}).get(period, {}).get("commercial", 0) or 0 for c in competitors]
        fig = go.Figure(data=[
            go.Bar(name="户用", x=names, y=d1, marker_color=_color(ORANGE, alpha)),
            go.Bar(name="大储", x=names, y=d2, marker_color=_color(BLUE, alpha)),
            go.Bar(name="工商业", x=names, y=d3, marker_color=_color(TEAL, alpha))
        ])
    fig.update_layout(barmode="stack")
    if is_forecast:
        fig.add_annotation(
            text="预测", xref="paper", yref="paper",
            x=0.98, y=0.98, showarrow=False,
            font=dict(size=10, color=ORANGE),
            bgcolor="rgba(17,20,23,0.7)", bordercolor=ORANGE, borderwidth=1, borderpad=3
        )
    return _base_layout(fig, height=380, y_title="GWh")


# ================================================================
#  财务对比柱状图 — 年度对比
# ================================================================

def fin_bar_chart(competitors, data_map, field="revenue", year1="2024", year2="2025"):
    names = [c["name"] for c in competitors]
    v1 = [data_map.get(c["cid"], {}).get(year1, {}).get(field) or 0 for c in competitors]
    v2 = [data_map.get(c["cid"], {}).get(year2, {}).get(field) or 0 for c in competitors]

    y2_is_fcst = (year2 == FORECAST_PERIOD)

    traces = [go.Bar(name=year1, x=names, y=v1, marker_color=GRAY)]
    if y2_is_fcst:
        traces.append(go.Bar(
            name=year2, x=names, y=v2,
            marker_color=hex_to_rgba(ORANGE, FORECAST_BAR_ALPHA),
            marker_line=dict(width=1.5, color=ORANGE),
            marker_pattern_shape="+",
        ))
    else:
        traces.append(go.Bar(name=year2, x=names, y=v2, marker_color=ORANGE))

    fig = go.Figure(data=traces)
    fig.update_layout(barmode="group")
    if y2_is_fcst:
        fig.add_annotation(
            text="预测", xref="paper", yref="paper",
            x=0.98, y=0.98, showarrow=False,
            font=dict(size=10, color=ORANGE),
            bgcolor="rgba(17,20,23,0.7)", bordercolor=ORANGE, borderwidth=1, borderpad=3
        )
    return _base_layout(fig, height=380)


# ================================================================
#  季度堆积柱状图 — 多公司 × Q1-Q4（核心新图表）
# ================================================================

def quarterly_stack_chart(competitors, qdata_map, metric_label="GWh"):
    """以公司为 X 轴，每家公司一根堆积柱，柱内按 Q1-Q4 分段。
    已完成季度用实色，未来季度用浅色（预测）。
    这才是正确的竞对分析视角：先看公司维度，再看季度拆分。"""
    quarters = ["Q1", "Q2", "Q3", "Q4"]
    completed = current_completed_quarters()
    names = [c["name"] for c in competitors]

    fig = go.Figure()

    for qi, q in enumerate(quarters):
        vals = []
        for comp in competitors:
            qd = qdata_map.get(comp["cid"], {})
            vals.append(qd.get(q) or 0)

        if not any(vals):
            continue

        # 已完成季度用季度色，未来季度用浅色
        q_color = Q_COLORS[q] if q in completed else Q_COLORS_FUTURE[q]
        fig.add_trace(go.Bar(
            name=q, x=names, y=vals,
            marker_color=q_color,
        ))

    fig.update_layout(barmode="stack")
    fig.add_annotation(
        text="▨ 浅色 = 未来季度预测", xref="paper", yref="paper",
        x=0.99, y=0.02, showarrow=False, xanchor="right", yanchor="bottom",
        font=dict(size=9, color=FONT_COLOR),
        bgcolor="rgba(17,20,23,0.6)", borderpad=3
    )
    return _base_layout(fig, height=420, y_title=metric_label)


# ================================================================
#  年度+季度组合图 — 单公司（历史年度柱 + 2026E 季度堆积）
# ================================================================

def combo_annual_quarterly(annual_data, quarters_data, color, label="GWh", unit=""):
    """单公司：2022-2025 年度柱 + 2026E 一根堆积柱（Q1-Q4 分段）。"""
    years = ["2022", "2023", "2024", "2025"]
    quarters = ["Q1", "Q2", "Q3", "Q4"]
    completed = current_completed_quarters()

    fig = go.Figure()

    # 历史年度柱（实色）
    annual_vals = [annual_data.get(y) for y in years]
    fig.add_trace(go.Bar(
        x=years, y=annual_vals, name=label,
        marker_color=color,
        width=0.55,
    ))

    # 2026E 季度堆积
    for q in quarters:
        v = quarters_data.get(q)
        q_color = Q_COLORS[q] if q in completed else Q_COLORS_FUTURE[q]
        fig.add_trace(go.Bar(
            x=["2026E"], y=[v or 0], name=q,
            marker_color=q_color,
            width=0.55,
        ))

    fig.update_layout(barmode="relative")
    fig.add_annotation(
        text="2026E = Q1+Q2+Q3+Q4", xref="paper", yref="paper",
        x=0.99, y=1.02, showarrow=False, xanchor="right", yanchor="bottom",
        font=dict(size=9, color=FONT_COLOR)
    )
    return _base_layout(fig, height=420, y_title=unit or label)


# ================================================================
#  季度利润率趋势 — 2026 动态展示
# ================================================================

def margin_quarterly_chart(fin_2026, hist_fin, color):
    """季度净利率折线（2026 各季度）+ 年度毛利率参考线 + 历史净利率点。"""
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
            line=dict(color=color, width=2.5),
            mode="lines+markers", marker=dict(size=7),
        ))

    # 未来季度虚线（从最后一个已完成点连接）
    fcst_x = [q for q in quarters if q not in completed]
    if fcst_x:
        fx = ([done_x[-1]] if done_x else []) + fcst_x
        fy = ([done_y[-1]] if done_y else []) + [nm_q[quarters.index(q)] for q in fcst_x]
        fig.add_trace(go.Scatter(
            x=fx, y=fy, name="季度净利率 (预测)",
            line=dict(color=hex_to_rgba(color, 0.55), width=2.5, dash="dash"),
            mode="lines+markers", marker=dict(size=7, color=hex_to_rgba(color, 0.55)),
        ))

    # 2026E 毛利率参考线（年度预测值）
    gm = fin_2026.get("gross_margin")
    if gm:
        fig.add_hline(y=gm, line=dict(color=YELLOW, width=1.5, dash="dot"),
                      annotation_text=f"毛利率 {gm:.1f}%",
                      annotation_font=dict(size=9, color=YELLOW),
                      annotation_position="top right")

    # 历史年度净利率点
    hist_years = ["2022", "2023", "2024", "2025"]
    hist_x, hist_y = [], []
    for y in hist_years:
        nm = hist_fin.get(y, {}).get("net_margin")
        if nm is not None:
            hist_x.append(y)
            hist_y.append(nm)
    if hist_y:
        fig.add_trace(go.Scatter(
            x=hist_x, y=hist_y, name="年度净利率",
            mode="markers", marker=dict(size=8, color=GRAY, symbol="diamond"),
        ))

    fig.add_annotation(
        text="虚线/浅色 = 预测", xref="paper", yref="paper",
        x=0.99, y=0.02, showarrow=False, xanchor="right", yanchor="bottom",
        font=dict(size=9, color=FONT_COLOR),
        bgcolor="rgba(17,20,23,0.6)", borderpad=3
    )

    return _base_layout(fig, height=420, y_title="%")


# ================================================================
#  季度收入柱状图（旧版兼容，内部使用）
# ================================================================

def qtr_bar_chart(competitors, data_map, field="rv", year="2025"):
    names = [c["name"] for c in competitors]
    is_forecast = (year == FORECAST_PERIOD)
    alpha = FORECAST_BAR_ALPHA if is_forecast else 1.0

    q_colors = [hex_to_rgba(Q_COLORS["Q1"], alpha), hex_to_rgba(Q_COLORS["Q2"], alpha),
                hex_to_rgba(Q_COLORS["Q3"], alpha), hex_to_rgba(Q_COLORS["Q4"], alpha)]

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
        fig.add_annotation(
            text="预测", xref="paper", yref="paper",
            x=0.98, y=0.98, showarrow=False,
            font=dict(size=10, color=ORANGE),
            bgcolor="rgba(17,20,23,0.7)", bordercolor=ORANGE, borderwidth=1, borderpad=3
        )
    return _base_layout(fig, height=380)


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
        fig.add_annotation(
            text="预测", xref="paper", yref="paper",
            x=0.98, y=0.98, showarrow=False,
            font=dict(size=10, color=ORANGE),
            bgcolor="rgba(17,20,23,0.7)", bordercolor=ORANGE, borderwidth=1, borderpad=3
        )
    return _base_layout(fig, height=420)


# ================================================================
#  行业图表
# ================================================================

def industry_chart(data_list, title=""):
    if not data_list:
        return go.Figure()
    df = pd.DataFrame(data_list)
    fig = px.line(df, x="period", y="metric_value", color="metric_name", title=title, markers=True)
    fig.update_layout(title=dict(text=title, font=dict(size=12, color=TITLE_COLOR)))
    return _base_layout(fig, height=420)


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
            marker_color=hex_to_rgba(ORANGE, FORECAST_BAR_ALPHA),
            marker_line=dict(width=1.5, color=ORANGE),
            marker_pattern_shape="+",
        ))

    fig = go.Figure(data=traces)
    fig.update_layout(barmode="group", yaxis=dict(autorange="reversed"))
    return _base_layout(fig, height=460)


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
            line=dict(color=hex_to_rgba(color, 0.70),
                      width=2.5, dash=FORECAST_DASH),
            mode="lines+markers",
            marker=dict(size=5, color=hex_to_rgba(color, 0.70)),
            fill="tozeroy", fillcolor=hex_to_rgba(color, FORECAST_FILL_ALPHA),
        ))

    return _base_layout(fig, height=380)


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
                line=dict(dash=dash_style, width=2, color=color), mode="lines+markers",
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
                          color=hex_to_rgba(color, 0.70)),
                mode="lines+markers",
                marker=dict(size=5, color=hex_to_rgba(color, 0.70)),
                legendgroup=name,
            ))

    return _base_layout(fig, height=420, y_title="元/Wh")
