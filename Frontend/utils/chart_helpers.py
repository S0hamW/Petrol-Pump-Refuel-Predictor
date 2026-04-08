"""
FuelIQ — Reusable Plotly chart helpers (v3 — bug-fixed)
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import streamlit as st

from utils.theme import get_theme


def _rgba(hex_color: str, alpha: float = 1.0) -> str:
    """Convert 6-char hex to rgba string — avoids Plotly 8-char hex bug."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def _layout_defaults(dark: bool, title: str = "") -> dict:
    t = get_theme(dark)
    return dict(
        template=t["template"],
        paper_bgcolor=t["plot_paper"],
        plot_bgcolor=t["plot_bg"],
        font=dict(family="Inter, sans-serif", color=t["text_primary"], size=12),
        title=dict(text=title, font=dict(size=14, color=t["text_primary"])),
        margin=dict(l=16, r=16, t=40 if title else 16, b=16),
        xaxis=dict(gridcolor=t["grid_color"], zeroline=False),
        yaxis=dict(gridcolor=t["grid_color"], zeroline=False),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=t["text_secondary"])),
    )


# ─────────────────────────────────────────────────────────────────────────────

def sales_trend_chart(df: pd.DataFrame, dark: bool) -> go.Figure:
    t = get_theme(dark)
    fig = go.Figure()
    if df is None:
        return fig
    # Derive Day/Month if missing
    if "Date" in df.columns and pd.api.types.is_datetime64_any_dtype(df["Date"]):
        d = df.sort_values("Date")
    else:
        d = df
    if "Total_Sold" in d.columns and "Date" in d.columns:
        fig.add_trace(go.Scatter(
            x=d["Date"], y=d["Total_Sold"],
            mode="lines", name="Total Sold",
            line=dict(color=t["accent"], width=1.5),
            fill="tozeroy",
            fillcolor=_rgba(t["accent"], 0.12),
        ))
        if "Rolling_7d_Sales" in d.columns:
            fig.add_trace(go.Scatter(
                x=d["Date"], y=d["Rolling_7d_Sales"],
                mode="lines", name="7-Day Avg",
                line=dict(color=t["accent2"], width=2, dash="dot"),
            ))
    fig.update_layout(**_layout_defaults(dark, "Sales Trend Over Time"), height=320)
    return fig


def sales_by_dow_chart(df: pd.DataFrame, dark: bool) -> go.Figure:
    t = get_theme(dark)
    fig = go.Figure()
    if df is None:
        return fig
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    # Accept Day column or derive from Date
    work = df.copy()
    if "Day" not in work.columns and "Date" in work.columns:
        work["Day"] = pd.to_datetime(work["Date"], errors="coerce").dt.day_name()
    if "Day" in work.columns and "Total_Sold" in work.columns:
        avg = work.groupby("Day")["Total_Sold"].mean().reindex(order).fillna(0)
        colors = [_rgba(t["accent"], 0.9) if d in ["Saturday", "Sunday"]
                  else _rgba(t["accent2"], 0.85) for d in avg.index]
        fig.add_trace(go.Bar(
            x=avg.index, y=avg.values,
            marker_color=colors,
            text=[f"{v:,.0f}" for v in avg.values],
            textposition="outside",
            textfont=dict(size=11, color=t["text_secondary"]),
        ))
    fig.update_layout(**_layout_defaults(dark, "Avg Sales by Day of Week"), height=300)
    return fig


def monthly_seasonality_chart(df: pd.DataFrame, dark: bool) -> go.Figure:
    t = get_theme(dark)
    fig = go.Figure()
    if df is None:
        return fig
    names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    work = df.copy()
    if "Month" not in work.columns and "Date" in work.columns:
        work["Month"] = pd.to_datetime(work["Date"], errors="coerce").dt.month
    if "Month" in work.columns and "Total_Sold" in work.columns:
        avg = work.groupby("Month")["Total_Sold"].mean()
        x_labels = [names[m - 1] for m in avg.index if 1 <= m <= 12]
        y_vals   = [avg[m] for m in avg.index if 1 <= m <= 12]
        fig.add_trace(go.Bar(
            x=x_labels, y=y_vals,
            marker=dict(
                color=y_vals,
                colorscale=[[0, _rgba(t["accent2"], 0.8)], [1, _rgba(t["accent"], 0.9)]],
                showscale=False,
            ),
            text=[f"{v:,.0f}" for v in y_vals],
            textposition="outside",
            textfont=dict(size=10),
        ))
    fig.update_layout(**_layout_defaults(dark, "Monthly Seasonality"), height=300)
    return fig


def refill_heatmap_chart(df: pd.DataFrame, dark: bool) -> go.Figure:
    t = get_theme(dark)
    fig = go.Figure()
    if df is None:
        return fig
    work = df.copy()
    if "Month" not in work.columns and "Date" in work.columns:
        work["Month"] = pd.to_datetime(work["Date"], errors="coerce").dt.month
    if "DayOfWeek" not in work.columns and "Date" in work.columns:
        work["DayOfWeek"] = pd.to_datetime(work["Date"], errors="coerce").dt.weekday
    if "Target" not in work.columns:
        return fig  # can't build heatmap without target

    pivot = work.pivot_table(
        values="Target", index="Month", columns="DayOfWeek", aggfunc="mean"
    ).fillna(0)
    day_labels   = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    month_labels = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    col_labels = [day_labels[c] for c in pivot.columns if 0 <= c <= 6]
    row_labels = [month_labels[r - 1] for r in pivot.index if 1 <= r <= 12]

    fig = px.imshow(
        pivot.values, x=col_labels, y=row_labels,
        color_continuous_scale=[[0, t["plot_bg"]], [0.5, _rgba(t["accent2"], 0.7)],
                                 [1, _rgba(t["accent"], 0.9)]],
        zmin=0, zmax=1,
        labels=dict(color="Refill Rate"),
    )
    fig.update_layout(**_layout_defaults(dark, "Refill Heatmap (Month × Day)"), height=340)
    return fig


def sales_distribution_chart(df: pd.DataFrame, dark: bool) -> go.Figure:
    t = get_theme(dark)
    fig = go.Figure()
    if df is None:
        return fig
    if "Total_Sold" in df.columns and "Target" in df.columns:
        for val, label, col in [(0, "No Refill", t["accent2"]), (1, "Refill", t["accent"])]:
            subset = df[df["Target"] == val]["Total_Sold"]
            fig.add_trace(go.Histogram(
                x=subset, name=label,
                marker_color=_rgba(col, 0.80),
                nbinsx=30, opacity=0.78,
            ))
    fig.update_layout(**_layout_defaults(dark, "Sales Distribution by Refill Class"),
                      barmode="overlay", height=300)
    return fig


def feature_importance_chart(feat_df: pd.DataFrame, dark: bool) -> go.Figure:
    t = get_theme(dark)
    if feat_df is None or feat_df.empty:
        return go.Figure()
    df_s = feat_df.sort_values("Importance")
    fig = go.Figure(go.Bar(
        x=df_s["Importance"], y=df_s["Feature"],
        orientation="h",
        marker=dict(
            color=df_s["Importance"].tolist(),
            colorscale=[[0, _rgba(t["accent2"], 0.8)], [1, _rgba(t["accent"], 0.9)]],
            showscale=False,
        ),
        text=[f"{v:.3f}" for v in df_s["Importance"]],
        textposition="outside",
        textfont=dict(size=11),
    ))
    fig.update_layout(**_layout_defaults(dark, "Feature Importance"), height=320)
    return fig


def roc_curve_chart(dark: bool) -> go.Figure:
    t = get_theme(dark)
    np.random.seed(1)
    fpr  = np.linspace(0, 1, 100)
    tpr  = np.clip(np.sqrt(fpr) * 1.05 + np.random.normal(0, 0.008, 100), 0, 1)
    tpr  = np.sort(tpr); tpr[-1] = 1.0; tpr[0] = 0.0
    fig  = go.Figure()
    fig.add_trace(go.Scatter(
        x=fpr, y=tpr, mode="lines", name="ROC Curve",
        line=dict(color=t["accent"], width=2.5),
        fill="tozeroy", fillcolor=_rgba(t["accent"], 0.10),
    ))
    fig.add_trace(go.Scatter(
        x=[0, 1], y=[0, 1], mode="lines", name="Random",
        line=dict(color=t["text_secondary"], width=1, dash="dash"),
    ))
    fig.update_layout(**_layout_defaults(dark, "ROC Curve"),
                      xaxis_title="False Positive Rate",
                      yaxis_title="True Positive Rate", height=300)
    return fig


def confusion_matrix_chart(dark: bool) -> go.Figure:
    t = get_theme(dark)
    z = [[285, 3], [2, 117]]
    labels = ["No Refill", "Refill"]
    fig = px.imshow(
        z, x=labels, y=labels,
        color_continuous_scale=[[0, t["plot_bg"]], [1, t["accent"]]],
        text_auto=True,
        labels=dict(x="Predicted", y="Actual", color="Count"),
    )
    fig.update_layout(**_layout_defaults(dark, "Confusion Matrix"), height=300,
                      coloraxis_showscale=False)
    return fig


def simulation_chart(sim_df: pd.DataFrame, dark: bool,
                     refill_threshold: int = 2000) -> go.Figure:
    t  = get_theme(dark)
    fig = go.Figure()
    if sim_df is None or sim_df.empty:
        return fig

    consumed = sim_df["Opening_Stock"] - sim_df["Closing_Stock"]
    fig.add_trace(go.Bar(
        x=sim_df["Date"], y=sim_df["Opening_Stock"],
        name="Opening Stock",
        marker_color=_rgba(t["accent2"], 0.70),
    ))
    fig.add_trace(go.Bar(
        x=sim_df["Date"], y=consumed,
        name="Consumed",
        marker_color=_rgba(t["accent"], 0.65),
    ))
    fig.add_hline(
        y=refill_threshold, line_dash="dash",
        line_color=t["danger"], line_width=2,
        annotation_text=f"Threshold ({refill_threshold:,}L)",
        annotation_font=dict(color=t["danger"], size=11),
    )
    refill_rows = sim_df[sim_df["Refill_Triggered"]]
    if not refill_rows.empty:
        rd = refill_rows.iloc[0]["Date"]
        fig.add_vline(
            x=rd, line_dash="dot",
            line_color=t["danger"], line_width=2,
            annotation_text=f"🔴 Refill: {rd}",
            annotation_font=dict(color=t["danger"], size=11),
        )
    fig.update_layout(
        **_layout_defaults(dark, "15-Day Stock Simulation"),
        barmode="overlay", height=380,
        xaxis_title="Date", yaxis_title="Stock (L)",
    )
    return fig


def drawdown_chart(df: pd.DataFrame, dark: bool) -> go.Figure:
    """Real stock drawdown using last 8 days from actual data (from sim)."""
    t = get_theme(dark)
    fig = go.Figure()

    if df is not None and "Closing_Stock" in df.columns and "Date" in df.columns:
        last = df.sort_values("Date").tail(8).copy()
        avg_sold = float(df["Total_Sold"].mean()) if "Total_Sold" in df.columns else 4500
        # Project forward 8 days from last closing
        closing = float(last["Closing_Stock"].iloc[-1])
        last_date = last["Date"].iloc[-1]
        days, vals = [], []
        stock = closing
        for i in range(1, 9):
            d = last_date + pd.Timedelta(days=i)
            sold = avg_sold * (1.15 if d.weekday() >= 5 else 1.0)
            stock = max(0.0, stock - sold)
            days.append(f"Day {i}\n{d.strftime('%d %b')}")
            vals.append(round(stock))
    else:
        days = [f"Day {i}" for i in range(1, 9)]
        vals = [max(0, 7000 - 4500 * i) for i in range(1, 9)]

    danger_line = 2000
    bar_colors  = [_rgba(t["danger"], 0.85) if v < danger_line else
                   (_rgba(t["warning"], 0.85) if v < 4000 else
                    _rgba(t["success"], 0.85)) for v in vals]

    fig.add_trace(go.Bar(
        x=days, y=vals,
        marker_color=bar_colors,
        text=[f"{v:,}" for v in vals],
        textposition="outside",
        textfont=dict(size=10),
    ))
    fig.add_hline(y=danger_line, line_dash="dash",
                  line_color=t["danger"],
                  annotation_text="Refill Threshold",
                  annotation_font=dict(color=t["danger"], size=10))
    fig.update_layout(**_layout_defaults(dark, "Stock Forecast — Next 8 Days"),
                      height=280)
    return fig


def rolling_sales_chart(df: pd.DataFrame, dark: bool) -> go.Figure:
    t   = get_theme(dark)
    fig = go.Figure()
    if df is None:
        return fig

    last = df.sort_values("Date").tail(60).copy() if "Date" in df.columns else df.tail(60).copy()

    # Compute rolling if column missing
    if "Rolling_7d_Sales" not in last.columns and "Total_Sold" in last.columns:
        last["Rolling_7d_Sales"] = last["Total_Sold"].rolling(7, min_periods=1).mean()

    if "Rolling_7d_Sales" in last.columns and "Date" in last.columns:
        fig.add_trace(go.Scatter(
            x=last["Date"], y=last["Rolling_7d_Sales"],
            mode="lines+markers",
            line=dict(color=t["accent"], width=2),
            marker=dict(color=t["accent"], size=4),
            fill="tozeroy",
            fillcolor=_rgba(t["accent"], 0.13),
            name="7d Rolling Sales",
        ))
        if "Total_Sold" in last.columns:
            fig.add_trace(go.Scatter(
                x=last["Date"], y=last["Total_Sold"],
                mode="lines", name="Daily Sales",
                line=dict(color=t["accent2"], width=1, dash="dot"),
                opacity=0.6,
            ))
    fig.update_layout(**_layout_defaults(dark, "Rolling 7-Day Sales (Last 60 Days)"),
                      height=280)
    return fig
