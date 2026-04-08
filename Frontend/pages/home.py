"""
FuelIQ — Dashboard Home Page (v4)
"""
import streamlit as st
import pandas as pd
from utils.theme import get_theme, no_data_state
from utils.data_loader import (
    load_demo_data, load_model, load_metrics, load_features,
    predict_refill, simulate_15_days, load_uploaded_data,
)
from utils.chart_helpers import drawdown_chart, rolling_sales_chart


def render():
    dark = st.session_state.get("dark_mode", True)
    t = get_theme(dark)

    if "df" not in st.session_state:
        st.session_state.df = None
    if "demand_adj" not in st.session_state:
        st.session_state.demand_adj = 0

    df = st.session_state.df

    # ── Page header ───────────────────────────────────────────────────────────
    source = st.session_state.get("data_source", None)
    fname  = st.session_state.get("uploaded_filename", "")
    if df is not None:
        flabel = "📂 Demo Dataset" if source == "demo" \
                 else (f"📂 {fname[:22]}…" if len(fname) > 24 else f"📂 {fname}") \
                 if fname else "📂 Uploaded Data"
        badge_color = t["accent2"] if source == "demo" else t["accent"]
        file_badge  = f'<span style="background:{badge_color}18;border:1px solid {badge_color}40;' \
                      f'color:{badge_color};border-radius:20px;padding:4px 12px;' \
                      f'font-size:0.72rem;font-weight:700;">{flabel}</span>'
    else:
        file_badge = ""

    st.markdown(f"""
    <div class="page-header">
        <div class="page-icon">🏠</div>
        <div>
            <div class="page-title">Dashboard &nbsp;{file_badge}</div>
            <div class="page-sub">Live predictions · Quick stats · AI-powered refill insights</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════
    # FILE UPLOAD
    # ═══════════════════════════════════════════════════════════════════════
    with st.container():
        st.markdown('<div class="fiq-card">', unsafe_allow_html=True)
        st.markdown('<div class="fiq-card-header">📂 DATA SOURCE</div>',
                    unsafe_allow_html=True)
        col_up, col_demo = st.columns([3, 1])
        with col_up:
            uploaded = st.file_uploader(
                "Upload petrol pump CSV or XLSX",
                type=["csv", "xlsx", "xls"],
                key="file_uploader",
                label_visibility="visible",
            )
        with col_demo:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("⚡ Use Demo Data", key="demo_btn",
                         use_container_width=True, type="primary"):
                with st.spinner("Loading demo dataset..."):
                    st.session_state.df = load_demo_data()
                    st.session_state.data_source = "demo"
                    st.session_state.uploaded_filename = ""
                st.rerun()

        if uploaded is not None:
            with st.spinner(f"Reading **{uploaded.name}**..."):
                result = load_uploaded_data(uploaded.read(), uploaded.name)
                st.session_state.df = result
                st.session_state.data_source = "upload"
                st.session_state.uploaded_filename = uploaded.name
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    df = st.session_state.df

    if df is None:
        no_data_state("Dashboard", "⛽")
        return

    # ═══════════════════════════════════════════════════════════════════════
    # STAT CARDS
    # ═══════════════════════════════════════════════════════════════════════
    df_s   = df.sort_values("Date") if "Date" in df.columns else df
    n_rows = len(df)

    # date range
    if "Date" in df_s.columns:
        d1 = df_s["Date"].iloc[0]
        d2 = df_s["Date"].iloc[-1]
        dr_s = d1.strftime("%b %Y") if hasattr(d1, "strftime") else str(d1)[:7]
        dr_e = d2.strftime("%b %Y") if hasattr(d2, "strftime") else str(d2)[:7]
        date_range = f"{dr_s} – {dr_e}"
    else:
        date_range = ""

    avg_sales   = df["Total_Sold"].mean() if "Total_Sold" in df.columns else 0
    refill_cnt  = int(df["Target"].sum()) if "Target" in df.columns else 0
    refill_pct  = refill_cnt / n_rows * 100 if n_rows else 0

    if "Closing_Stock" in df_s.columns:
        cur_stock = float(df_s["Closing_Stock"].iloc[-1])
    else:
        cur_stock = 0
    stock_pct = cur_stock / 12000 * 100

    stock_color = t["danger"] if stock_pct < 25 else (t["warning"] if stock_pct < 50 else t["success"])
    stock_delta_cls = "delta-down" if stock_pct < 25 else ("delta-warn" if stock_pct < 50 else "delta-up")

    st.markdown(f"""
    <div class="stat-row">
        <div class="stat-card">
            <div class="stat-label">📋 Total Rows</div>
            <div class="stat-value">{n_rows:,}</div>
            <div class="stat-delta delta-mute">{date_range}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">⛽ Avg Daily Sales</div>
            <div class="stat-value">{avg_sales:,.0f}
                <span style="font-size:1rem;font-weight:400;color:{t['text_secondary']}">L</span>
            </div>
            <div class="stat-delta delta-up">per day</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">📦 Current Stock</div>
            <div class="stat-value" style="color:{stock_color}">{cur_stock:,.0f}
                <span style="font-size:1rem;font-weight:400;color:{t['text_secondary']}">L</span>
            </div>
            <div class="stat-delta {stock_delta_cls}">{stock_pct:.0f}% of capacity</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">🔄 Refill Events</div>
            <div class="stat-value">{refill_cnt:,}</div>
            <div class="stat-delta delta-warn">{refill_pct:.1f}% of days</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ═══════════════════════════════════════════════════════════════════════
    # PREDICTION CARD (from actual model)
    # ═══════════════════════════════════════════════════════════════════════
    model    = load_model()
    features = load_features()
    metrics  = load_metrics()
    demand_adj = st.session_state.get("demand_adj", 0)
    pred = predict_refill(df, model, features, demand_adj)

    conf_pct = pred["confidence"] * 100
    rd       = pred["refill_date"]
    rd_str   = rd.strftime("%d %b %Y") if hasattr(rd, "strftime") else str(rd)[:10]
    rd_dow   = rd.strftime("%A")       if hasattr(rd, "strftime") else ""
    days_rem = pred["days_remaining"]
    days_color = t["danger"] if days_rem <= 2 else (t["warning"] if days_rem <= 5 else t["accent2"])
    cl_stock   = pred["closing_stock"]
    cl_color   = t["danger"] if cl_stock < 2000 else (t["warning"] if cl_stock < 4000 else t["accent2"])

    st.markdown(f"""
    <div class="pred-card">
        <div class="pred-ai-badge">🤖 AI Powered</div>
        <div class="pred-header">🔮 NEXT REFILL PREDICTION</div>
        <div class="pred-grid">
            <div>
                <div class="pred-col-label">Predicted Refill Date</div>
                <div class="pred-col-value" style="color:{t['accent2']}">{rd_str}</div>
                <div class="pred-col-sub">{rd_dow}</div>
            </div>
            <div>
                <div class="pred-col-label">Days Remaining</div>
                <div class="pred-col-value" style="color:{days_color}">{days_rem}</div>
                <div class="pred-col-sub">days from latest record</div>
            </div>
            <div>
                <div class="pred-col-label">Closing Stock (last record)</div>
                <div class="pred-col-value" style="color:{cl_color}">{cl_stock:,.0f}
                    <span style="font-size:1.1rem;font-weight:400">L</span>
                </div>
                <div class="pred-col-sub">
                    {'⚠️ below 2,000L — refill soon' if cl_stock < 2000 else '✅ above threshold'}
                </div>
            </div>
        </div>
        <div>
            <div class="conf-bar-label">
                <span>Model confidence</span>
                <span style="color:{t['accent']};font-weight:700">{conf_pct:.0f}%</span>
            </div>
            <div class="conf-bar-track">
                <div class="conf-bar-fill" style="width:{conf_pct:.0f}%"></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Why this prediction
    avg7 = df_s.tail(7)["Total_Sold"].mean() if "Total_Sold" in df.columns else pred["avg_sold"]
    st.markdown(f"""
    <div class="why-card">
        <div style="font-size:0.85rem;font-weight:700;color:{t['text_primary']};margin-bottom:2px;">
            💡 Why this prediction?
        </div>
        <div class="why-item">
            <div class="why-dot" style="background:{t['danger']}"></div>
            <div>
                <b style="color:{t['text_primary']}">Closing stock: {cl_stock:,.0f}L</b> —
                {'critically low, only ' + str(round(cl_stock/12000*100)) + '% of tank capacity'
                 if cl_stock < 4000 else 'at moderate level, monitoring recommended'}.
            </div>
        </div>
        <div class="why-item">
            <div class="why-dot" style="background:{t['accent']}"></div>
            <div>
                <b style="color:{t['text_primary']}">7-day avg sales: {avg7:,.0f} L/day</b> —
                {'above overall average, accelerating depletion' if avg7 > pred['avg_sold']
                 else 'within normal range'}.
            </div>
        </div>
        <div class="why-item">
            <div class="why-dot" style="background:{t['accent2']}"></div>
            <div>
                <b style="color:{t['text_primary']}">Random Forest signal:</b>
                {metrics.get('accuracy',0)*100:.0f}% accuracy model flags refill
                at <b style="color:{t['accent']}">{conf_pct:.0f}%</b> confidence.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ═══════════════════════════════════════════════════════════════════════
    # QUICK CHARTS — using real data
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown(f'<div style="font-size:0.88rem;font-weight:700;'
                f'color:{t["text_primary"]};margin-bottom:12px;">📊 Quick Charts</div>',
                unsafe_allow_html=True)

    col_c1, col_c2 = st.columns(2, gap="medium")
    with col_c1:
        st.markdown('<div class="fiq-card" style="padding:14px 14px 6px 14px;">',
                    unsafe_allow_html=True)
        st.markdown('<div class="fiq-card-header">STOCK FORECAST — NEXT 8 DAYS</div>',
                    unsafe_allow_html=True)
        fig_dd = drawdown_chart(df, dark)           # ← real df passed
        st.plotly_chart(fig_dd, use_container_width=True,
                        config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    with col_c2:
        st.markdown('<div class="fiq-card" style="padding:14px 14px 6px 14px;">',
                    unsafe_allow_html=True)
        st.markdown('<div class="fiq-card-header">7-DAY ROLLING SALES (LAST 60 DAYS)</div>',
                    unsafe_allow_html=True)
        fig_rs = rolling_sales_chart(df, dark)      # ← real df passed
        st.plotly_chart(fig_rs, use_container_width=True,
                        config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    # ═══════════════════════════════════════════════════════════════════════
    # QUICK WHAT-IF SLIDER
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown(f'<div style="font-size:0.88rem;font-weight:700;'
                f'color:{t["text_primary"]};margin-bottom:8px;">'
                f'⚡ Quick What-If: Demand Adjustment</div>',
                unsafe_allow_html=True)
    adj = st.slider("Demand adjustment (%)", -30, 30, 0, 5,
                    key="home_demand_slider",
                    help="Simulate how changed demand affects refill date")
    if adj != st.session_state.get("demand_adj", 0):
        st.session_state.demand_adj = adj

    if adj != 0:
        adj_pred = predict_refill(df, model, features, adj)
        delta    = adj_pred["days_remaining"] - pred["days_remaining"]
        direction = "later ✅" if delta > 0 else "earlier ⚠️"
        adj_rd    = adj_pred["refill_date"]
        adj_rd_str = adj_rd.strftime("%d %b %Y") if hasattr(adj_rd, "strftime") else str(adj_rd)[:10]
        st.info(
            f"With **{adj:+d}% demand**: Refill on **{adj_rd_str}**  "
            f"({abs(delta)} days {direction} vs baseline)"
        )
