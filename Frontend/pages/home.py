"""
FuelIQ — Dashboard Home Page (v5 Clean)
"""
import streamlit as st
import pandas as pd
from utils.theme import get_theme, no_data_state
from utils.data_loader import (
    load_demo_data, load_model, load_metrics, load_features,
    predict_refill, load_uploaded_data, simulate_forward,
)
from utils.chart_helpers import drawdown_chart, rolling_sales_chart


def render():
    dark = st.session_state.get("dark_mode", True)
    t = get_theme(dark)

    if "df" not in st.session_state:
        st.session_state.df = None

    df = st.session_state.df

    # ── Page header ────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="page-header">
        <div class="page-icon">⛽</div>
        <div>
            <div class="page-title">FuelIQ Dashboard</div>
            <div class="page-sub">AI-powered petrol pump refuel predictor · Upload data to begin</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # FILE UPLOAD CARD
    # ═══════════════════════════════════════════════════════════════════════════
    st.markdown(f'<div class="fiq-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="fiq-card-header">📂 DATA SOURCE</div>', unsafe_allow_html=True)

    col_up, col_demo = st.columns([3, 1], gap="medium")
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
        fkey = f"loaded_{uploaded.name}_{uploaded.size}"
        if st.session_state.get("_last_file_key") != fkey:
            with st.spinner(f"Reading **{uploaded.name}**..."):
                # Clear any stale cache so the fixed parser is always used
                load_uploaded_data.clear()
                file_bytes = uploaded.read()
                result = load_uploaded_data(file_bytes, uploaded.name)
                st.session_state.df = result
                st.session_state.data_source = "upload"
                st.session_state.uploaded_filename = uploaded.name
                st.session_state["_last_file_key"] = fkey
            st.rerun()

    # Dataset summary immediately after upload
    df = st.session_state.df
    if df is not None:
        source = st.session_state.get("data_source", "")
        fname  = st.session_state.get("uploaded_filename", "")
        label  = "Demo Dataset" if source == "demo" else (fname or "Uploaded File")

        d1_str, d2_str = "", ""
        if "Date" in df.columns:
            df_s   = df.sort_values("Date")
            d1, d2 = df_s["Date"].iloc[0], df_s["Date"].iloc[-1]
            d1_str = d1.strftime("%d %b %Y") if hasattr(d1, "strftime") else str(d1)[:10]
            d2_str = d2.strftime("%d %b %Y") if hasattr(d2, "strftime") else str(d2)[:10]

        refill_cnt = int(df["Target"].sum()) if "Target" in df.columns else 0

        st.markdown(f"""
        <div style="margin-top:14px;display:grid;grid-template-columns:repeat(4,1fr);gap:10px;">
            <div style="background:{t['card_bg2']};border:1px solid {t['border']};border-radius:10px;
                        padding:12px 14px;">
                <div style="font-size:0.58rem;font-weight:700;letter-spacing:1.4px;
                            text-transform:uppercase;color:{t['text_secondary']};margin-bottom:6px;">
                    📁 Source
                </div>
                <div style="font-size:0.95rem;font-weight:700;color:{t['accent']}">{label[:24]}</div>
            </div>
            <div style="background:{t['card_bg2']};border:1px solid {t['border']};border-radius:10px;
                        padding:12px 14px;">
                <div style="font-size:0.58rem;font-weight:700;letter-spacing:1.4px;
                            text-transform:uppercase;color:{t['text_secondary']};margin-bottom:6px;">
                    📋 Records
                </div>
                <div style="font-size:1.4rem;font-weight:800;color:{t['text_primary']}">{len(df):,}</div>
                <div style="font-size:0.68rem;color:{t['text_secondary']}">{len(df.columns)} columns</div>
            </div>
            <div style="background:{t['card_bg2']};border:1px solid {t['border']};border-radius:10px;
                        padding:12px 14px;">
                <div style="font-size:0.58rem;font-weight:700;letter-spacing:1.4px;
                            text-transform:uppercase;color:{t['text_secondary']};margin-bottom:6px;">
                    📅 Date Range
                </div>
                <div style="font-size:0.82rem;font-weight:700;color:{t['text_primary']}">{d1_str}</div>
                <div style="font-size:0.75rem;color:{t['text_secondary']}">→ {d2_str}</div>
            </div>
            <div style="background:{t['card_bg2']};border:1px solid {t['border']};border-radius:10px;
                        padding:12px 14px;">
                <div style="font-size:0.58rem;font-weight:700;letter-spacing:1.4px;
                            text-transform:uppercase;color:{t['text_secondary']};margin-bottom:6px;">
                    🔄 Refill Events
                </div>
                <div style="font-size:1.4rem;font-weight:800;color:{t['accent']}">{refill_cnt:,}</div>
                <div style="font-size:0.68rem;color:{t['text_secondary']}">
                    {refill_cnt/len(df)*100:.1f}% of days
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    if df is None:
        no_data_state("Dashboard", "⛽")
        return

    st.markdown("<br>", unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # KEY STATS ROW
    # ═══════════════════════════════════════════════════════════════════════════
    df_s   = df.sort_values("Date") if "Date" in df.columns else df
    n_rows = len(df)

    if "Date" in df_s.columns:
        d1 = df_s["Date"].iloc[0]
        d2 = df_s["Date"].iloc[-1]
        dr_s = d1.strftime("%b %Y") if hasattr(d1, "strftime") else str(d1)[:7]
        dr_e = d2.strftime("%b %Y") if hasattr(d2, "strftime") else str(d2)[:7]
        date_range = f"{dr_s} – {dr_e}"
    else:
        date_range = ""

    avg_sales  = float(pd.to_numeric(df["Total_Sold"], errors="coerce").fillna(0).mean()) \
                 if "Total_Sold" in df.columns else 0
    refill_cnt = int(df["Target"].sum()) if "Target" in df.columns else 0
    refill_pct = refill_cnt / n_rows * 100 if n_rows else 0

    if "Closing_Stock" in df_s.columns:
        cur_stock = float(pd.to_numeric(df_s["Closing_Stock"], errors="coerce").fillna(0).iloc[-1])
    else:
        cur_stock = 0.0
    stock_pct = cur_stock / 12000 * 100

    stock_color     = t["danger"] if stock_pct < 25 else (t["warning"] if stock_pct < 50 else t["success"])
    stock_delta_cls = "delta-down" if stock_pct < 25 else ("delta-warn" if stock_pct < 50 else "delta-up")

    st.markdown(f"""
    <div class="stat-row">
        <div class="stat-card">
            <div class="stat-label">📋 Total Records</div>
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

    # ═══════════════════════════════════════════════════════════════════════════
    # PREDICTION CARD — solid color, no gradient
    # ═══════════════════════════════════════════════════════════════════════════
    model    = load_model()
    features = load_features()
    metrics  = load_metrics()
    pred     = predict_refill(df, model, features, 0.0)

    conf_pct   = pred["confidence"] * 100
    rd         = pred["refill_date"]
    rd_str     = rd.strftime("%d %b %Y") if hasattr(rd, "strftime") else str(rd)[:10]
    rd_dow     = rd.strftime("%A")       if hasattr(rd, "strftime") else ""
    days_rem   = int(pred["days_remaining"])
    cl_stock   = float(pred["closing_stock"])
    days_color = t["danger"] if days_rem <= 2 else (t["warning"] if days_rem <= 5 else t["accent2"])
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
                <div class="pred-col-sub">days from last record</div>
            </div>
            <div>
                <div class="pred-col-label">Closing Stock (last record)</div>
                <div class="pred-col-value" style="color:{cl_color}">{cl_stock:,.0f}
                    <span style="font-size:1.1rem;font-weight:400">L</span>
                </div>
                <div class="pred-col-sub">
                    {'⚠️ Below 2,000L — refill SOON' if cl_stock < 2000 else '✅ Above safe threshold'}
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
    avg7 = float(
        pd.to_numeric(df_s.tail(7)["Total_Sold"], errors="coerce").fillna(0).mean()
    ) if "Total_Sold" in df.columns else pred["avg_sold"]

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
                <b style="color:{t['text_primary']}">Model trained on {n_rows:,} records:</b>
                {metrics.get('accuracy', 0)*100:.0f}% accuracy Random Forest flags refill at
                <b style="color:{t['accent']}">{conf_pct:.0f}%</b> confidence.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── PDF Report Download ──────────────────────────────────────────────────
    from utils.pdf_report import generate_pdf_report

    # 15-day walk-forward simulation (matches notebook logic exactly)
    sim_df = simulate_forward(df, demand_adjustment=0.0, n_days=15)

    pdf_bytes = generate_pdf_report(pred, metrics, sim_df)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.download_button(
        label="📄 Download PDF Report",
        data=pdf_bytes,
        file_name="fueliq_prediction_report.pdf",
        mime="application/pdf",
        type="primary",
    )

    st.divider()

    # ═══════════════════════════════════════════════════════════════════════════
    # QUICK CHARTS
    # ═══════════════════════════════════════════════════════════════════════════
    st.markdown(f'<div style="font-size:0.88rem;font-weight:700;'
                f'color:{t["text_primary"]};margin-bottom:12px;">📊 Quick Charts</div>',
                unsafe_allow_html=True)

    col_c1, col_c2 = st.columns(2, gap="medium")
    with col_c1:
        st.markdown('<div class="fiq-card" style="padding:14px 14px 6px 14px;">',
                    unsafe_allow_html=True)
        st.markdown('<div class="fiq-card-header">STOCK FORECAST — NEXT 8 DAYS</div>',
                    unsafe_allow_html=True)
        fig_dd = drawdown_chart(df, dark, pred=pred)
        st.plotly_chart(fig_dd, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    with col_c2:
        st.markdown('<div class="fiq-card" style="padding:14px 14px 6px 14px;">',
                    unsafe_allow_html=True)
        st.markdown('<div class="fiq-card-header">7-DAY ROLLING SALES (LAST 60 DAYS)</div>',
                    unsafe_allow_html=True)
        fig_rs = rolling_sales_chart(df, dark)
        st.plotly_chart(fig_rs, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)
