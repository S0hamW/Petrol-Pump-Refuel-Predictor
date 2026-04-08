"""
FuelIQ — Simulation Page (v4)
"""
import streamlit as st
import pandas as pd
from utils.theme import get_theme, no_data_state
from utils.data_loader import load_model, load_features, simulate_15_days
from utils.chart_helpers import simulation_chart


def render():
    dark = st.session_state.get("dark_mode", True)
    t = get_theme(dark)
    df: pd.DataFrame = st.session_state.get("df", None)

    st.markdown("""
    <div class="page-header">
        <div class="page-icon">🔮</div>
        <div>
            <div class="page-title">Simulation</div>
            <div class="page-sub">15-day stock drawdown forecast from the last data record</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if df is None:
        no_data_state("Simulation", "🔮")
        return

    model    = load_model()
    features = load_features()

    # Last record info
    if "Date" in df.columns:
        df_s  = df.sort_values("Date")
        last_d = df_s["Date"].iloc[-1]
        last_s = float(df_s["Closing_Stock"].iloc[-1]) if "Closing_Stock" in df_s.columns else 0
        last_d_str = last_d.strftime("%d %b %Y") if hasattr(last_d, "strftime") else str(last_d)[:10]
        st.markdown(f"""
        <div style="font-size:0.8rem;color:{t['text_secondary']};margin-bottom:14px;">
            📅 Starting from last record: <b style="color:{t['text_primary']}">{last_d_str}</b>
            &nbsp;|&nbsp; Closing stock:
            <b style="color:{t['accent']}">{last_s:,.0f} L</b>
        </div>
        """, unsafe_allow_html=True)

    # ── Controls ──────────────────────────────────────────────────────────────
    st.markdown('<div class="fiq-card">', unsafe_allow_html=True)
    st.markdown('<div class="fiq-card-header">🎛️ SIMULATION PARAMETERS</div>',
                unsafe_allow_html=True)
    col_d, col_t = st.columns(2)
    with col_d:
        demand_sim = st.slider("⚡ Demand Adjustment (%)", -30, 30,
                               st.session_state.get("demand_adj", 0), 5,
                               key="sim_demand",
                               help="+ve = higher demand (festival), -ve = lower (monsoon)")
    with col_t:
        threshold = st.number_input("🔴 Refill Threshold (L)", 500, 5000, 2000, 100,
                                    key="sim_threshold")
    st.markdown("</div>", unsafe_allow_html=True)
    st.divider()

    with st.spinner("Running 15-day simulation..."):
        sim_df = simulate_15_days(df, model, features, demand_sim)

    if sim_df is None or sim_df.empty:
        st.error("Simulation failed — could not process the dataset.")
        return

    # ── Chart ─────────────────────────────────────────────────────────────────
    st.markdown('<div class="fiq-card" style="padding:16px;">', unsafe_allow_html=True)
    st.markdown('<div class="fiq-card-header">📊 15-DAY STOCK DRAWDOWN FORECAST</div>',
                unsafe_allow_html=True)
    fig = simulation_chart(sim_df, dark, int(threshold))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})

    refill_rows = sim_df[sim_df["Refill_Triggered"]]
    if not refill_rows.empty:
        rfd = refill_rows.iloc[0]["Date"]
        rfd_day = refill_rows.iloc[0]["Day"]
        st.markdown(
            f'<div style="font-size:0.85rem;color:{t["danger"]};font-weight:700;">'
            f'🔴 Refill trigger expected on: <b>{rfd}</b> ({rfd_day}) — '
            f'stock drops below {int(threshold):,}L</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div style="font-size:0.85rem;color:{t["success"]};font-weight:700;">'
            f'✅ Stock remains above {int(threshold):,}L for the full 15-day window.</div>',
            unsafe_allow_html=True
        )
    st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    # ── Summary metrics ────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📦 Avg Closing", f"{sim_df['Closing_Stock'].mean():,.0f} L")
    c2.metric("⛽ Est. Total Sold", f"{sim_df['Est_Sold'].sum():,.0f} L")
    c3.metric("🔴 Max Refill Prob", f"{sim_df['Refill_Probability'].max():.1%}")
    c4.metric("🔄 Refills Triggered", f"{int(sim_df['Refill_Triggered'].sum())}")

    st.divider()

    # ── Day-by-day table ──────────────────────────────────────────────────────
    st.markdown(f'<div style="font-size:0.88rem;font-weight:700;'
                f'color:{t["text_primary"]};margin-bottom:10px;">'
                f'📋 Day-by-Day Forecast Table</div>', unsafe_allow_html=True)

    display = sim_df.copy()
    display["Refill_Probability"] = display["Refill_Probability"].apply(lambda x: f"{x:.1%}")
    display["Refill_Triggered"]   = display["Refill_Triggered"].apply(
        lambda x: "🔴 YES" if x else "✅  No")
    for col in ["Opening_Stock", "Est_Sold", "Closing_Stock"]:
        display[col] = display[col].apply(lambda x: f"{x:,}")
    display = display.rename(columns={
        "Opening_Stock": "Opening (L)", "Est_Sold": "Sold (L)",
        "Closing_Stock": "Closing (L)", "Refill_Probability": "Refill Prob",
        "Refill_Triggered": "Refill?",
    })
    st.dataframe(display, use_container_width=True, height=460, hide_index=True)
