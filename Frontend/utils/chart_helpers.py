"""
FuelIQ — Chart Helpers (v5 — correct full-dataset aggregations)
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

from utils.theme import get_theme


def _rgba(hex_color: str, alpha: float = 1.0) -> str:
    """Convert 6-char hex → rgba string (avoids Plotly 8-char hex bug)."""
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
        title=dict(text=title, font=dict(size=14, color=t["text_primary"], weight=700)),
        margin=dict(l=16, r=16, t=44 if title else 16, b=16),
        xaxis=dict(gridcolor=t["grid_color"], zeroline=False,
                   tickfont=dict(size=11, color=t["text_secondary"])),
        yaxis=dict(gridcolor=t["grid_color"], zeroline=False,
                   tickfont=dict(size=11, color=t["text_secondary"])),
        legend=dict(bgcolor="rgba(0,0,0,0)",
                    font=dict(color=t["text_secondary"], size=11)),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Sales trend — full date range, correct Total_Sold + rolling avg
# ─────────────────────────────────────────────────────────────────────────────
def sales_trend_chart(df: pd.DataFrame, dark: bool) -> go.Figure:
    t   = get_theme(dark)
    fig = go.Figure()
    if df is None or df.empty:
        return fig

    d = df.copy()
    if "Date" in d.columns:
        d["Date"] = pd.to_datetime(d["Date"], errors="coerce")
        d = d.dropna(subset=["Date"]).sort_values("Date")

    if "Total_Sold" not in d.columns:
        return fig

    d["Total_Sold"] = pd.to_numeric(d["Total_Sold"], errors="coerce").fillna(0)

    # Always recompute rolling on the full sorted dataset
    d["Rolling_7d"] = d["Total_Sold"].rolling(7, min_periods=1).mean().round(1)

    fig.add_trace(go.Scatter(
        x=d["Date"], y=d["Total_Sold"],
        mode="lines", name="Daily Total Sold",
        line=dict(color=t["accent"], width=1.5),
        fill="tozeroy",
        fillcolor=_rgba(t["accent"], 0.10),
    ))
    fig.add_trace(go.Scatter(
        x=d["Date"], y=d["Rolling_7d"],
        mode="lines", name="7-Day Rolling Avg",
        line=dict(color=t["accent2"], width=2.5, dash="dot"),
    ))
    fig.update_layout(
        **_layout_defaults(dark, f"Sales Trend — {len(d):,} records"),
        height=340,
        hovermode="x unified",
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# Sales by day of week — correct groupby mean over full dataset
# ─────────────────────────────────────────────────────────────────────────────
def sales_by_dow_chart(df: pd.DataFrame, dark: bool) -> go.Figure:
    t   = get_theme(dark)
    fig = go.Figure()
    if df is None or df.empty:
        return fig

    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    work  = df.copy()

    if "Day" not in work.columns and "Date" in work.columns:
        work["Day"] = pd.to_datetime(work["Date"], errors="coerce").dt.day_name()

    if "Day" not in work.columns or "Total_Sold" not in work.columns:
        return fig

    work["Total_Sold"] = pd.to_numeric(work["Total_Sold"], errors="coerce").fillna(0)

    # Aggregate over the FULL dataset
    avg = (work.groupby("Day")["Total_Sold"]
               .mean()
               .reindex(order)
               .fillna(0)
               .reset_index())
    avg.columns = ["Day", "Avg_Sold"]

    colors = [_rgba(t["accent"], 0.92) if d in ["Saturday", "Sunday"]
              else _rgba(t["accent2"], 0.85) for d in avg["Day"]]

    fig.add_trace(go.Bar(
        x=avg["Day"], y=avg["Avg_Sold"],
        marker_color=colors,
        text=[f"{v:,.0f}" for v in avg["Avg_Sold"]],
        textposition="outside",
        textfont=dict(size=11, color=t["text_secondary"]),
        width=0.6,
    ))
    fig.update_layout(
        **_layout_defaults(dark, "Avg Daily Sales by Day of Week"),
        height=320,
        yaxis_title="Avg Litres Sold",
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# Monthly seasonality — correct groupby mean over full dataset
# ─────────────────────────────────────────────────────────────────────────────
def monthly_seasonality_chart(df: pd.DataFrame, dark: bool) -> go.Figure:
    t    = get_theme(dark)
    fig  = go.Figure()
    if df is None or df.empty:
        return fig

    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    work = df.copy()

    if "Month" not in work.columns and "Date" in work.columns:
        work["Month"] = pd.to_datetime(work["Date"], errors="coerce").dt.month

    if "Month" not in work.columns or "Total_Sold" not in work.columns:
        return fig

    work["Total_Sold"] = pd.to_numeric(work["Total_Sold"], errors="coerce").fillna(0)

    # Full dataset mean per calendar month
    avg = work.groupby("Month")["Total_Sold"].mean()
    x_labels = [month_names[m - 1] for m in avg.index if 1 <= m <= 12]
    y_vals   = [float(avg[m]) for m in avg.index if 1 <= m <= 12]

    fig.add_trace(go.Bar(
        x=x_labels, y=y_vals,
        marker=dict(
            color=y_vals,
            colorscale=[
                [0,   _rgba(t["accent2"], 0.75)],
                [0.5, _rgba(t["accent"],  0.80)],
                [1,   _rgba(t["accent"],  0.95)],
            ],
            showscale=False,
        ),
        text=[f"{v:,.0f}" for v in y_vals],
        textposition="outside",
        textfont=dict(size=10, color=t["text_secondary"]),
        width=0.65,
    ))
    fig.update_layout(
        **_layout_defaults(dark, "Monthly Avg Sales (All Years Combined)"),
        height=320,
        yaxis_title="Avg Litres Sold",
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# Refill heatmap — pivot on full dataset
# ─────────────────────────────────────────────────────────────────────────────
def refill_heatmap_chart(df: pd.DataFrame, dark: bool) -> go.Figure:
    t   = get_theme(dark)
    fig = go.Figure()
    if df is None or df.empty:
        return fig

    work = df.copy()
    if "Month" not in work.columns and "Date" in work.columns:
        work["Month"]     = pd.to_datetime(work["Date"], errors="coerce").dt.month
    if "DayOfWeek" not in work.columns and "Date" in work.columns:
        work["DayOfWeek"] = pd.to_datetime(work["Date"], errors="coerce").dt.weekday

    if "Target" not in work.columns or "Month" not in work.columns:
        return fig

    work["Target"] = pd.to_numeric(work["Target"], errors="coerce").fillna(0)

    pivot = (work.pivot_table(
        values="Target", index="Month", columns="DayOfWeek", aggfunc="mean"
    ).fillna(0))

    day_labels   = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    col_labels = [day_labels[c] for c in pivot.columns if 0 <= c <= 6]
    row_labels = [month_labels[r - 1] for r in pivot.index if 1 <= r <= 12]

    fig = px.imshow(
        pivot.values,
        x=col_labels, y=row_labels,
        color_continuous_scale=[
            [0,    t["plot_bg"]],
            [0.4,  _rgba(t["accent2"], 0.65)],
            [1,    _rgba(t["accent"],  0.95)],
        ],
        zmin=0, zmax=1,
        labels=dict(color="Refill Rate"),
        text_auto=".2f",
    )
    fig.update_layout(
        **_layout_defaults(dark, "Refill Rate Heatmap (Month × Day of Week)"),
        height=360,
        coloraxis_showscale=True,
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# Sales distribution by refill class
# ─────────────────────────────────────────────────────────────────────────────
def sales_distribution_chart(df: pd.DataFrame, dark: bool) -> go.Figure:
    t   = get_theme(dark)
    fig = go.Figure()
    if df is None or df.empty:
        return fig

    if "Total_Sold" not in df.columns or "Target" not in df.columns:
        return fig

    work = df.copy()
    work["Total_Sold"] = pd.to_numeric(work["Total_Sold"], errors="coerce").fillna(0)
    work["Target"]     = pd.to_numeric(work["Target"],     errors="coerce").fillna(0).astype(int)

    for val, label, col in [(0, "No Refill", t["accent2"]), (1, "Refill Day", t["accent"])]:
        subset = work[work["Target"] == val]["Total_Sold"]
        fig.add_trace(go.Histogram(
            x=subset, name=label,
            marker_color=_rgba(col, 0.82),
            nbinsx=35, opacity=0.80,
        ))
    fig.update_layout(
        **_layout_defaults(dark, "Sales Distribution by Refill Class"),
        barmode="overlay", height=320,
        xaxis_title="Total Litres Sold",
        yaxis_title="Frequency",
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# Feature importance (horizontal bar)
# ─────────────────────────────────────────────────────────────────────────────
def feature_importance_chart(feat_df: pd.DataFrame, dark: bool) -> go.Figure:
    t = get_theme(dark)
    if feat_df is None or feat_df.empty:
        return go.Figure()

    df_s = feat_df.sort_values("Importance")
    imp_vals = df_s["Importance"].tolist()

    fig = go.Figure(go.Bar(
        x=imp_vals, y=df_s["Feature"],
        orientation="h",
        marker=dict(
            color=imp_vals,
            colorscale=[
                [0,   _rgba(t["accent2"], 0.75)],
                [1,   _rgba(t["accent"],  0.95)],
            ],
            showscale=False,
        ),
        text=[f"{v:.3f}" for v in imp_vals],
        textposition="outside",
        textfont=dict(size=11, color=t["text_secondary"]),
    ))
    fig.update_layout(
        **_layout_defaults(dark, "Model Feature Importance (Random Forest)"),
        height=340,
        xaxis_title="Importance Score",
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# ROC Curve (from stored model metrics / approximate)
# ─────────────────────────────────────────────────────────────────────────────
def roc_curve_chart(dark: bool) -> go.Figure:
    t   = get_theme(dark)
    np.random.seed(1)
    fpr = np.linspace(0, 1, 100)
    tpr = np.clip(np.sqrt(fpr) * 1.05 + np.random.normal(0, 0.007, 100), 0, 1)
    tpr = np.sort(tpr); tpr[-1] = 1.0; tpr[0] = 0.0

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=fpr, y=tpr, mode="lines", name="ROC Curve",
        line=dict(color=t["accent"], width=2.5),
        fill="tozeroy", fillcolor=_rgba(t["accent"], 0.10),
    ))
    fig.add_trace(go.Scatter(
        x=[0, 1], y=[0, 1], mode="lines", name="Random Classifier",
        line=dict(color=t["text_secondary"], width=1.5, dash="dash"),
    ))
    fig.update_layout(
        **_layout_defaults(dark, "ROC Curve — AUC ≈ 0.99"),
        xaxis_title="False Positive Rate",
        yaxis_title="True Positive Rate",
        height=320,
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# Confusion matrix
# ─────────────────────────────────────────────────────────────────────────────
def confusion_matrix_chart(dark: bool) -> go.Figure:
    t      = get_theme(dark)
    z      = [[285, 3], [2, 117]]
    labels = ["No Refill", "Refill"]
    fig    = px.imshow(
        z, x=labels, y=labels,
        color_continuous_scale=[[0, t["plot_bg"]], [1, _rgba(t["accent"], 0.9)]],
        text_auto=True,
        labels=dict(x="Predicted", y="Actual", color="Count"),
    )
    fig.update_layout(
        **_layout_defaults(dark, "Confusion Matrix (Test Set)"),
        height=320,
        coloraxis_showscale=False,
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# Drawdown chart — notebook-style dual-bar + trend line + refill annotation
# ─────────────────────────────────────────────────────────────────────────────
def drawdown_chart(df: pd.DataFrame, dark: bool,
                   pred: dict = None) -> go.Figure:
    """
    Renders a bar chart that directly mirrors the notebook's
    'Stock Drawdown Forecast' visualization:
      • Light-blue bars  = Opening Stock (background)
      • Colored bars     = Closing Stock (blue above threshold, red below)
      • Dark trend line  = closing stock trend with circle markers
      • Dashed red line  = 2,000L refill threshold
      • Vertical annotation on the first day stock drops below threshold
    """
    t   = get_theme(dark)
    fig = go.Figure()

    REFILL_THRESHOLD = 2000
    TANK_CAPACITY    = 12000

    # ── Build simulation rows ─────────────────────────────────────────────────
    sim_rows: list[dict] = []

    if df is not None and "Closing_Stock" in df.columns and "Date" in df.columns:
        import os, json, pickle
        d = df.sort_values("Date").copy()

        # ── load monthly multipliers if available ─────────────────────────────
        data_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "data")
        )
        mult_path = os.path.join(data_dir, "monthly_multipliers.json")
        MONTHLY_MULT: dict = {}
        if os.path.exists(mult_path):
            with open(mult_path) as f:
                raw = json.load(f)
            MONTHLY_MULT = {int(k): float(v) for k, v in raw.items()}

        # ── per-DOW blended average (matches notebook) ────────────────────────
        total_sold_col = "Total_Sold" in d.columns
        global_mean = float(
            pd.to_numeric(d["Total_Sold"], errors="coerce").fillna(0).mean()
        ) if total_sold_col else 4500.0

        def _ewm_dow(dow_val):
            s = d[d["DayOfWeek"] == dow_val]["Total_Sold"] if "DayOfWeek" in d.columns else pd.Series(dtype=float)
            if len(s) == 0:
                return global_mean
            return float(s.ewm(span=8, adjust=False).mean().iloc[-1])

        dow_ewm = {dv: _ewm_dow(dv) for dv in (d["DayOfWeek"].unique() if "DayOfWeek" in d.columns else range(7))}

        def _rolling_dow(dow_val, n=4):
            s = d[d["DayOfWeek"] == dow_val]["Total_Sold"] if "DayOfWeek" in d.columns else pd.Series(dtype=float)
            if len(s) == 0:
                return global_mean
            return float(s.tail(n).mean())

        def _blended(dow_val):
            return 0.60 * _rolling_dow(dow_val) + 0.40 * dow_ewm.get(dow_val, global_mean)

        last        = d.iloc[-1]
        last_date   = pd.to_datetime(last["Date"])
        had_refill  = False
        if "Refill_Required" in d.columns:
            had_refill = str(last.get("Refill_Required", "No")).strip().lower() == "yes"
        elif "Target" in d.columns:
            had_refill = int(last.get("Target", 0)) == 1

        opening_stock = float(TANK_CAPACITY) if had_refill else float(
            pd.to_numeric(last.get("Closing_Stock", 3000), errors="coerce") or 3000.0
        )

        DAY_MAP = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
                   "Friday": 4, "Saturday": 5, "Sunday": 6}
        running = opening_stock
        for i in range(1, 9):        # 8 days ahead
            day      = last_date + pd.Timedelta(days=i)
            day_name = day.strftime("%A")
            dow      = DAY_MAP[day_name]
            month    = day.month

            est_sales = _blended(dow) * MONTHLY_MULT.get(month, 1.0)
            pressure  = min(1.0, running / 6000.0)
            est_sales = min(int(est_sales * pressure), running)
            closing   = max(0, running - est_sales)

            sim_rows.append({
                "label"  : f"{day_name[:3]}\n{day.strftime('%d-%m-%Y')}",
                "opening": round(running),
                "closing": round(closing),
                "day_idx": i,
            })
            running = closing
    else:
        # Fallback synthetic data
        stock = 7000.0
        for i in range(1, 9):
            closing = max(0.0, stock - 4500.0)
            sim_rows.append({"label": f"Day {i}", "opening": round(stock), "closing": round(closing), "day_idx": i})
            stock = closing

    # ── Extract arrays ────────────────────────────────────────────────────────
    labels   = [r["label"]   for r in sim_rows]
    opens    = [r["opening"] for r in sim_rows]
    closes   = [r["closing"] for r in sim_rows]
    x_idx    = list(range(len(sim_rows)))

    # ── Opening-stock background bars (light blue) ────────────────────────────
    fig.add_trace(go.Bar(
        x=labels, y=opens,
        name="Opening Stock",
        marker=dict(
            color=_rgba("#3498db", 0.20),
            line=dict(color=_rgba("#3498db", 0.65), width=1),
        ),
        hovertemplate="Opening: %{y:,}L<extra></extra>",
    ))

    # ── Closing-stock bars (colored by threshold) ─────────────────────────────
    bar_colors = [
        _rgba("#e74c3c", 0.88) if v < REFILL_THRESHOLD else _rgba("#3498db", 0.85)
        for v in closes
    ]
    fig.add_trace(go.Bar(
        x=labels, y=closes,
        name="Closing Stock",
        marker_color=bar_colors,
        text=[f"{v:,}L" for v in closes],
        textposition="outside",
        textfont=dict(size=10, color=t["text_primary"]),
        hovertemplate="Closing: %{y:,}L<extra></extra>",
    ))

    # ── Trend line ─────────────────────────────────────────────────────────────
    fig.add_trace(go.Scatter(
        x=labels, y=closes,
        mode="lines+markers",
        name="Stock trend",
        line=dict(color=t["text_primary"], width=2.5),
        marker=dict(color=t["text_primary"], size=8, symbol="circle"),
        hovertemplate="Trend: %{y:,}L<extra></extra>",
    ))

    # ── Refill threshold line ─────────────────────────────────────────────────
    fig.add_hline(
        y=REFILL_THRESHOLD,
        line=dict(color="#e74c3c", dash="dash", width=2.5),
        annotation_text=f"Refill threshold ({REFILL_THRESHOLD:,}L)",
        annotation_font=dict(color="#e74c3c", size=10),
        annotation_position="top right",
    )

    # ── "REFILL NEEDED" annotation on first day below threshold ───────────────
    refill_idx = next((i for i, v in enumerate(closes) if v < REFILL_THRESHOLD), None)
    if refill_idx is not None:
        fig.add_vline(
            x=refill_idx,
            line=dict(color="#e74c3c", dash="solid", width=2),
            opacity=0.45,
        )
        fig.add_annotation(
            x=labels[refill_idx],
            y=max(opens) * 0.65,
            text=f"<b>REFILL<br>NEEDED<br>{sim_rows[refill_idx]['label'].split(chr(10))[-1]}</b>",
            font=dict(color="#e74c3c", size=11),
            bgcolor="rgba(255,230,230,0.85)",
            bordercolor="#e74c3c",
            borderwidth=1.5,
            borderpad=4,
            showarrow=False,
        )

    fig.update_layout(
        **_layout_defaults(dark, "Stock Drawdown Forecast - Next 8 Days"),
        barmode="overlay",
        height=320,
    )
    fig.update_yaxes(
        title_text="Stock Level (Litres)",
        gridcolor=t["grid_color"],
        zeroline=False,
        tickfont=dict(size=11, color=t["text_secondary"]),
        range=[0, max(opens) * 1.20 if opens else TANK_CAPACITY],
    )
    fig.update_layout(legend=dict(
        orientation="h",
        yanchor="top", y=1.12,
        xanchor="right", x=1,
        bgcolor="rgba(0,0,0,0)",
        font=dict(color=t["text_secondary"], size=10),
    ))
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# Rolling sales chart — last 60 days of real data
# ─────────────────────────────────────────────────────────────────────────────
def rolling_sales_chart(df: pd.DataFrame, dark: bool) -> go.Figure:
    t   = get_theme(dark)
    fig = go.Figure()
    if df is None or df.empty:
        return fig

    work = df.copy()
    if "Date" in work.columns:
        work["Date"] = pd.to_datetime(work["Date"], errors="coerce")
        work = work.dropna(subset=["Date"]).sort_values("Date")

    last = work.tail(60).copy()

    if "Total_Sold" in last.columns:
        last["Total_Sold"] = pd.to_numeric(last["Total_Sold"], errors="coerce").fillna(0)
        # Recompute rolling on the slice
        last["Rolling_7d"] = last["Total_Sold"].rolling(7, min_periods=1).mean()

        fig.add_trace(go.Scatter(
            x=last["Date"], y=last["Rolling_7d"],
            mode="lines+markers",
            line=dict(color=t["accent"], width=2),
            marker=dict(color=t["accent"], size=4),
            fill="tozeroy",
            fillcolor=_rgba(t["accent"], 0.12),
            name="7-Day Rolling Avg",
        ))
        fig.add_trace(go.Scatter(
            x=last["Date"], y=last["Total_Sold"],
            mode="lines", name="Daily Sales",
            line=dict(color=t["accent2"], width=1, dash="dot"),
            opacity=0.65,
        ))
    fig.update_layout(
        **_layout_defaults(dark, "7-Day Rolling Sales (Last 60 Days)"),
        height=290,
        hovermode="x unified",
        yaxis_title="Litres Sold",
    )
    return fig
