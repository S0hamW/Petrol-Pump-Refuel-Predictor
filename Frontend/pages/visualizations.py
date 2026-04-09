"""
FuelIQ — Visualizations Page (v5 — full-dataset accurate charts)
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
    t    = get_theme(dark)
    df: pd.DataFrame = st.session_state.get("df", None)

    st.markdown("""
    <div class="page-header">
        <div class="page-icon">📈</div>
        <div>
            <div class="page-title">Visualizations</div>
            <div class="page-sub">Interactive charts built from the full dataset · All aggregations recomputed live</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if df is None:
        no_data_state("Visualizations", "📈")
        return

    # Dataset info bar
    if "Date" in df.columns:
        df_s = df.sort_values("Date")
        d1   = df_s["Date"].iloc[0]
        d2   = df_s["Date"].iloc[-1]
        s1   = d1.strftime("%d %b %Y") if hasattr(d1, "strftime") else str(d1)[:10]
        s2   = d2.strftime("%d %b %Y") if hasattr(d2, "strftime") else str(d2)[:10]
        st.markdown(f"""
        <div style="font-size:0.78rem;color:{t['text_secondary']};
                    margin-bottom:18px;padding:10px 14px;
                    background:{t['card_bg']};border:1px solid {t['border']};
                    border-radius:8px;">
            📅 <b style="color:{t['text_primary']}">{s1}</b> →
               <b style="color:{t['text_primary']}">{s2}</b>
            &nbsp;|&nbsp;
            <b style="color:{t['accent']}">{len(df):,}</b> records
            &nbsp;|&nbsp;
            Columns: <b style="color:{t['accent2']}">{len(df.columns)}</b>
        </div>
        """, unsafe_allow_html=True)

    # Ensure derived columns exist on this df slice
    work = df.copy()
    if "Date" in work.columns:
        work["Date"] = pd.to_datetime(work["Date"], errors="coerce")
        work = work.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)
    if "Day" not in work.columns and "Date" in work.columns:
        work["Day"] = work["Date"].dt.day_name()
    if "Month" not in work.columns and "Date" in work.columns:
        work["Month"] = work["Date"].dt.month
    if "DayOfWeek" not in work.columns and "Date" in work.columns:
        work["DayOfWeek"] = work["Date"].dt.weekday

    # ── Tab layout ─────────────────────────────────────────────────────────────
    tabs = st.tabs(["📉 Sales Trend", "📅 By Day of Week", "🗓 Monthly",
                    "🔥 Refill Heatmap", "📊 Distribution"])

    # ── TAB 1: Sales Trend ─────────────────────────────────────────────────────
    with tabs[0]:
        st.markdown('<div class="fiq-card" style="padding:16px;">', unsafe_allow_html=True)
        if "Total_Sold" in work.columns and "Date" in work.columns:
            fig = sales_trend_chart(work, dark)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
            st.markdown(f"""
            <div style="font-size:0.77rem;color:{t['text_secondary']};margin-top:6px;">
                📌 <b style="color:{t['accent']}">Amber fill</b> = daily total sales &nbsp;·&nbsp;
                <b style="color:{t['accent2']}">Green dotted</b> = 7-day rolling average.<br>
                All <b style="color:{t['text_primary']}">{len(work):,} records</b> plotted.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("⚠️ Requires `Total_Sold` and `Date` columns.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ── TAB 2: Day of Week ─────────────────────────────────────────────────────
    with tabs[1]:
        st.markdown('<div class="fiq-card" style="padding:16px;">', unsafe_allow_html=True)
        if "Day" in work.columns and "Total_Sold" in work.columns:
            fig = sales_by_dow_chart(work, dark)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            # Compute actual weekend uplift from data
            work["Total_Sold"] = pd.to_numeric(work["Total_Sold"], errors="coerce").fillna(0)
            weekday_avg = work[~work["DayOfWeek"].isin([5, 6])]["Total_Sold"].mean() \
                          if "DayOfWeek" in work.columns else None
            weekend_avg = work[work["DayOfWeek"].isin([5, 6])]["Total_Sold"].mean() \
                          if "DayOfWeek" in work.columns else None
            if weekday_avg and weekend_avg and weekday_avg > 0:
                uplift = (weekend_avg - weekday_avg) / weekday_avg * 100
                st.markdown(f"""
                <div style="font-size:0.77rem;color:{t['text_secondary']};margin-top:6px;">
                    📌 <b style="color:{t['accent']}">Amber bars</b> = weekends (Sat/Sun) —
                    <b style="color:{t['text_primary']}">{uplift:+.1f}%</b> vs weekday average
                    (computed from full {len(work):,}-row dataset).
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("⚠️ Requires `Day` and `Total_Sold` columns.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ── TAB 3: Monthly ────────────────────────────────────────────────────────
    with tabs[2]:
        st.markdown('<div class="fiq-card" style="padding:16px;">', unsafe_allow_html=True)
        if "Month" in work.columns and "Total_Sold" in work.columns:
            fig = monthly_seasonality_chart(work, dark)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            # Find actual peak month
            work["Total_Sold"] = pd.to_numeric(work["Total_Sold"], errors="coerce").fillna(0)
            mon_avg = work.groupby("Month")["Total_Sold"].mean()
            peak_m  = int(mon_avg.idxmax()) if not mon_avg.empty else 10
            month_names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
            peak_name = month_names[peak_m - 1] if 1 <= peak_m <= 12 else "Oct"

            st.markdown(f"""
            <div style="font-size:0.77rem;color:{t['text_secondary']};margin-top:6px;">
                📌 Color gradient maps low → high consumption.
                Peak month: <b style="color:{t['accent']}">{peak_name}</b>
                ({mon_avg.max():,.0f} L/day avg).
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("⚠️ Requires `Month` and `Total_Sold` columns.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ── TAB 4: Refill Heatmap ─────────────────────────────────────────────────
    with tabs[3]:
        st.markdown('<div class="fiq-card" style="padding:16px;">', unsafe_allow_html=True)
        if "Month" in work.columns and "DayOfWeek" in work.columns and "Target" in work.columns:
            fig = refill_heatmap_chart(work, dark)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.markdown(f"""
            <div style="font-size:0.77rem;color:{t['text_secondary']};margin-top:6px;">
                📌 Each cell = refill rate for that Month × Day combination.
                Brighter = more refill events. Computed over {len(work):,} records.
            </div>
            """, unsafe_allow_html=True)
        else:
            missing = [c for c in ["Month", "DayOfWeek", "Target"] if c not in work.columns]
            st.info(f"⚠️ Missing columns: {missing}. `Target` (refill indicator) is required.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ── TAB 5: Distribution ───────────────────────────────────────────────────
    with tabs[4]:
        st.markdown('<div class="fiq-card" style="padding:16px;">', unsafe_allow_html=True)
        if "Total_Sold" in work.columns and "Target" in work.columns:
            fig = sales_distribution_chart(work, dark)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            work["Total_Sold"] = pd.to_numeric(work["Total_Sold"], errors="coerce").fillna(0)
            work["Target"]     = pd.to_numeric(work["Target"],     errors="coerce").fillna(0).astype(int)
            no_ref_avg = work[work["Target"] == 0]["Total_Sold"].mean()
            ref_avg    = work[work["Target"] == 1]["Total_Sold"].mean()
            st.markdown(f"""
            <div style="font-size:0.77rem;color:{t['text_secondary']};margin-top:6px;">
                📌 <b style="color:{t['accent2']}">Green</b> = no refill days (avg {no_ref_avg:,.0f} L) &nbsp;·&nbsp;
                <b style="color:{t['accent']}">Amber</b> = refill days (avg {ref_avg:,.0f} L).
                Lower sales on refill days = depleted stock restricts dispensing.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("⚠️ Requires `Total_Sold` and `Target` columns.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    # ── Key Observations ───────────────────────────────────────────────────────
    st.markdown(f'<div style="font-size:0.88rem;font-weight:700;'
                f'color:{t["text_primary"]};margin-bottom:14px;">📌 Key Observations</div>',
                unsafe_allow_html=True)

    # Compute real stats from full dataset
    obs_data = []
    if "DayOfWeek" in work.columns and "Total_Sold" in work.columns:
        work["Total_Sold"] = pd.to_numeric(work["Total_Sold"], errors="coerce").fillna(0)
        wd_avg = work[~work["DayOfWeek"].isin([5, 6])]["Total_Sold"].mean()
        we_avg = work[work["DayOfWeek"].isin([5, 6])]["Total_Sold"].mean()
        uplift = (we_avg - wd_avg) / wd_avg * 100 if wd_avg > 0 else 0
        obs_data.append((
            "Weekend Sales Uplift",
            f"Weekend avg = {we_avg:,.0f} L/day vs {wd_avg:,.0f} L/day on weekdays ({uplift:+.1f}%)",
            t["accent"]
        ))

    if "Month" in work.columns and "Total_Sold" in work.columns:
        mon_avg  = work.groupby("Month")["Total_Sold"].mean()
        peak_m   = int(mon_avg.idxmax()) if not mon_avg.empty else 10
        month_nm = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        obs_data.append((
            "Peak Month",
            f"{month_nm[peak_m-1]} has the highest avg daily sales: {mon_avg.max():,.0f} L/day",
            t["accent2"]
        ))

    if "Target" in work.columns:
        work["Target"] = pd.to_numeric(work["Target"], errors="coerce").fillna(0).astype(int)
        rc  = int(work["Target"].sum())
        avg_days = len(work) / rc if rc > 0 else 0
        obs_data.append((
            "Refill Cadence",
            f"{rc} refill events in {len(work):,} days — avg every {avg_days:.1f} days",
            t["danger"]
        ))

    if "Closing_Stock" in work.columns:
        work["Closing_Stock"] = pd.to_numeric(work["Closing_Stock"], errors="coerce").fillna(0)
        avg_close = work["Closing_Stock"].mean()
        obs_data.append((
            "Avg Closing Stock",
            f"Average closing stock = {avg_close:,.0f} L across all records",
            t["accent3"] if "accent3" in t else t["warning"]
        ))

    cols = st.columns(2)
    for i, (title, desc, color) in enumerate(obs_data):
        with cols[i % 2]:
            st.markdown(f"""
            <div class="fiq-card" style="border-left:3px solid {color};margin-bottom:10px;">
                <div style="color:{color};font-weight:700;font-size:0.85rem;margin-bottom:5px;">
                    {title}
                </div>
                <div style="font-size:0.8rem;color:{t['text_secondary']};line-height:1.6;">
                    {desc}
                </div>
            </div>
            """, unsafe_allow_html=True)
