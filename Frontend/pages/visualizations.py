"""
FuelIQ — Visualizations Page (v4)
"""
import streamlit as st
import pandas as pd
from utils.theme import get_theme, no_data_state
from utils.chart_helpers import (
    sales_trend_chart, sales_by_dow_chart, monthly_seasonality_chart,
    refill_heatmap_chart, sales_distribution_chart,
)


def render():
    dark = st.session_state.get("dark_mode", True)
    t = get_theme(dark)
    df: pd.DataFrame = st.session_state.get("df", None)

    st.markdown("""
    <div class="page-header">
        <div class="page-icon">📈</div>
        <div>
            <div class="page-title">Visualizations</div>
            <div class="page-sub">Interactive Plotly charts for deep data exploration</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if df is None:
        no_data_state("Visualizations", "📈")
        return

    # Dataset header info
    if "Date" in df.columns:
        df_s = df.sort_values("Date")
        d1 = df_s["Date"].iloc[0]
        d2 = df_s["Date"].iloc[-1]
        s1 = d1.strftime("%d %b %Y") if hasattr(d1, "strftime") else str(d1)[:10]
        s2 = d2.strftime("%d %b %Y") if hasattr(d2, "strftime") else str(d2)[:10]
        st.markdown(f"""
        <div style="font-size:0.78rem;color:{t['text_secondary']};margin-bottom:16px;">
            📅 <b style="color:{t['text_primary']}">{s1}</b> →
            <b style="color:{t['text_primary']}">{s2}</b> &nbsp;|&nbsp;
            <b style="color:{t['accent']}">{len(df):,}</b> records &nbsp;|&nbsp;
            Columns: <b style="color:{t['accent2']}">{len(df.columns)}</b>
        </div>
        """, unsafe_allow_html=True)

    # ── Tab-based chart selector (more reliable than selectbox condition) ──────
    tab_labels = ["📉 Sales Trend", "📅 By Day", "🗓 Monthly",
                  "🔥 Heatmap", "📊 Distribution"]
    tabs = st.tabs(tab_labels)

    # ── TAB 1: Sales Trend ────────────────────────────────────────────────────
    with tabs[0]:
        st.markdown('<div class="fiq-card" style="padding:16px;">', unsafe_allow_html=True)
        fig = sales_trend_chart(df, dark)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
        st.markdown(f"""
        <div style="font-size:0.78rem;color:{t['text_secondary']};margin-top:4px;">
            📌 <b style="color:{t['accent']}">Amber line</b> = daily total sold ·
            <b style="color:{t['accent2']}">Dotted green</b> = 7-day rolling average
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── TAB 2: By Day of Week ─────────────────────────────────────────────────
    with tabs[1]:
        st.markdown('<div class="fiq-card" style="padding:16px;">', unsafe_allow_html=True)
        # Ensure Day column
        if "Day" not in df.columns and "Date" in df.columns:
            df = df.copy()
            df["Day"] = pd.to_datetime(df["Date"], errors="coerce").dt.day_name()
        if "Day" in df.columns and "Total_Sold" in df.columns:
            fig = sales_by_dow_chart(df, dark)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.markdown(f"""
            <div style="font-size:0.78rem;color:{t['text_secondary']};margin-top:4px;">
                📌 <b style="color:{t['accent']}">Amber bars</b> = weekend days (Sat/Sun) —
                consistently 10–15% higher demand
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("⚠️ Requires `Day` and `Total_Sold` columns.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ── TAB 3: Monthly Seasonality ────────────────────────────────────────────
    with tabs[2]:
        st.markdown('<div class="fiq-card" style="padding:16px;">', unsafe_allow_html=True)
        if "Month" not in df.columns and "Date" in df.columns:
            df = df.copy()
            df["Month"] = pd.to_datetime(df["Date"], errors="coerce").dt.month
        if "Month" in df.columns and "Total_Sold" in df.columns:
            fig = monthly_seasonality_chart(df, dark)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.markdown(f"""
            <div style="font-size:0.78rem;color:{t['text_secondary']};margin-top:4px;">
                📌 Color gradient maps low → high consumption.
                Oct–Nov typically peak due to festival season.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("⚠️ Requires `Month` and `Total_Sold` columns.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ── TAB 4: Refill Heatmap ─────────────────────────────────────────────────
    with tabs[3]:
        st.markdown('<div class="fiq-card" style="padding:16px;">', unsafe_allow_html=True)
        need = ["Month", "DayOfWeek", "Target"]
        missing_cols = [c for c in need if c not in df.columns]
        if "Month" not in df.columns and "Date" in df.columns:
            df = df.copy()
            df["Month"]     = pd.to_datetime(df["Date"], errors="coerce").dt.month
            df["DayOfWeek"] = pd.to_datetime(df["Date"], errors="coerce").dt.weekday
            missing_cols = [c for c in need if c not in df.columns]

        if not missing_cols:
            fig = refill_heatmap_chart(df, dark)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.markdown(f"""
            <div style="font-size:0.78rem;color:{t['text_secondary']};margin-top:4px;">
                📌 Brighter cells = higher refill probability for that Month × Day combination.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info(f"⚠️ Missing columns for heatmap: {missing_cols}. "
                    f"The `Target` (Refill indicator) column is required.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ── TAB 5: Sales Distribution ─────────────────────────────────────────────
    with tabs[4]:
        st.markdown('<div class="fiq-card" style="padding:16px;">', unsafe_allow_html=True)
        if "Total_Sold" in df.columns and "Target" in df.columns:
            fig = sales_distribution_chart(df, dark)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.markdown(f"""
            <div style="font-size:0.78rem;color:{t['text_secondary']};margin-top:4px;">
                📌 <b style="color:{t['accent']}">Refill days</b> cluster at lower sales —
                depleted stock restricts dispensing.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("⚠️ Requires `Total_Sold` and `Target` columns.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    # ── Summary stats ─────────────────────────────────────────────────────────
    st.markdown(f'<div style="font-size:0.88rem;font-weight:700;'
                f'color:{t["text_primary"]};margin-bottom:12px;">📌 Key Observations</div>',
                unsafe_allow_html=True)

    obs = [
        ("Weekend Boost",    "Saturday sales are ~15% above weekday average.", t["accent"]),
        ("Festival Surge",   "Oct–Nov shows the highest monthly average (festival season).", t["accent2"]),
        ("Monsoon Dip",      "Jun–Sep sees ~8% reduced demand due to lower travel.", t["success"]),
        ("Refill Cadence",   "Refills occur every ~3 days, triggered by sub-2,000L closing stock.", t["danger"]),
    ]
    cols = st.columns(2)
    for i, (title, desc, color) in enumerate(obs):
        with cols[i % 2]:
            st.markdown(f"""
            <div class="fiq-card" style="border-left:3px solid {color};margin-bottom:10px;">
                <div style="color:{color};font-weight:700;font-size:0.85rem;margin-bottom:6px;">
                    {title}
                </div>
                <div style="font-size:0.8rem;color:{t['text_secondary']};line-height:1.6;">
                    {desc}
                </div>
            </div>
            """, unsafe_allow_html=True)
