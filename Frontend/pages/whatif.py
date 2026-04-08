"""
FuelIQ — What-If Analysis Page (v4)
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.theme import get_theme, no_data_state
from utils.data_loader import load_model, load_features, predict_refill, simulate_15_days
from utils.chart_helpers import simulation_chart, _rgba, _layout_defaults


def render():
    dark = st.session_state.get("dark_mode", True)
    t = get_theme(dark)
    df: pd.DataFrame = st.session_state.get("df", None)

    st.markdown("""
    <div class="page-header">
        <div class="page-icon">⚡</div>
        <div>
            <div class="page-title">What-If Analysis</div>
            <div class="page-sub">Explore how demand changes affect the refill date &amp; stock</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if df is None:
        no_data_state("What-If Analysis", "⚡")
        return

    model    = load_model()
    features = load_features()

    # ── Controls ──────────────────────────────────────────────────────────────
    st.markdown('<div class="fiq-card">', unsafe_allow_html=True)
    st.markdown('<div class="fiq-card-header">🎛️ SCENARIO PARAMETERS</div>',
                unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        demand_adj = st.slider("📊 Demand Adjustment (%)", -30, 30, 0, 1,
                               key="wi_demand")
    with col_b:
        threshold = st.slider("🔴 Refill Threshold (L)", 500, 5000, 2000, 100,
                              key="wi_threshold")
    with col_c:
        scenario = st.selectbox("📋 Preset Scenario",
            ["Custom", "Festival Surge (+20%)", "Monsoon Dip (-15%)",
             "Holiday Peak (+30%)", "Off-season (-25%)"], key="wi_scenario")

    preset_map = {"Festival Surge (+20%)": 20, "Monsoon Dip (-15%)": -15,
                  "Holiday Peak (+30%)": 30, "Off-season (-25%)": -25, "Custom": demand_adj}
    eff_adj = preset_map.get(scenario, demand_adj)
    if scenario != "Custom":
        st.info(f"Preset **{scenario}** → demand: **{eff_adj:+d}%**")
    st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    # ── Prediction comparison ────────────────────────────────────────────────
    base_pred = predict_refill(df, model, features, 0)
    wi_pred   = predict_refill(df, model, features, eff_adj)

    def _pred_card(title, pred, color, icon):
        rd = pred["refill_date"]
        rd_s = rd.strftime("%d %b %Y") if hasattr(rd, "strftime") else str(rd)[:10]
        return f"""
        <div class="fiq-card" style="border-color:{color}40;">
            <div style="font-size:0.58rem;font-weight:800;letter-spacing:2px;
                        text-transform:uppercase;color:{color};margin-bottom:14px;">
                {icon} {title}
            </div>
            <div style="display:flex;gap:24px;flex-wrap:wrap;">
                <div>
                    <div style="font-size:0.68rem;color:{t['text_secondary']};">Refill Date</div>
                    <div style="font-size:1.5rem;font-weight:800;color:{color};">{rd_s}</div>
                </div>
                <div>
                    <div style="font-size:0.68rem;color:{t['text_secondary']};">Days Left</div>
                    <div style="font-size:1.5rem;font-weight:800;color:{t['text_primary']};">
                        {pred['days_remaining']}
                    </div>
                </div>
                <div>
                    <div style="font-size:0.68rem;color:{t['text_secondary']};">Confidence</div>
                    <div style="font-size:1.5rem;font-weight:800;color:{t['accent2']};">
                        {pred['confidence']*100:.0f}%
                    </div>
                </div>
            </div>
        </div>"""

    col_b, col_w = st.columns(2, gap="medium")
    with col_b:
        st.markdown(_pred_card("Baseline (0%)", base_pred, t["accent2"], "📊"),
                    unsafe_allow_html=True)
    with col_w:
        wi_c = t["danger"] if eff_adj > 0 else (t["success"] if eff_adj < 0 else t["accent"])
        st.markdown(_pred_card(f"What-If ({eff_adj:+d}%)", wi_pred, wi_c, "⚡"),
                    unsafe_allow_html=True)

    # Delta banner
    delta = wi_pred["days_remaining"] - base_pred["days_remaining"]
    if delta != 0:
        dc = t["success"] if delta > 0 else t["danger"]
        arrow = "↗" if delta > 0 else "↘"
        st.markdown(f"""
        <div style="text-align:center;padding:14px;background:{dc}12;
                    border:1px solid {dc}30;border-radius:10px;margin:10px 0 20px 0;">
            <span style="font-size:1.05rem;font-weight:800;color:{dc};">
                {arrow} Refill shifts by {abs(delta)} days
                {'later — less urgent ✅' if delta > 0 else 'earlier — higher urgency ⚠️'}
            </span>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # ── Side-by-side simulation charts ────────────────────────────────────────
    st.markdown(f'<div style="font-size:0.88rem;font-weight:700;'
                f'color:{t["text_primary"]};margin-bottom:14px;">'
                f'📈 15-Day Simulation Comparison</div>', unsafe_allow_html=True)

    col_c1, col_c2 = st.columns(2, gap="medium")
    with col_c1:
        st.markdown("**Baseline (0% adjustment)**")
        sim_base = simulate_15_days(df, model, features, 0)
        fig_base = simulation_chart(sim_base, dark, threshold)
        fig_base.update_layout(title=dict(text="Baseline"), height=310)
        st.plotly_chart(fig_base, use_container_width=True,
                        config={"displayModeBar": False})

    with col_c2:
        st.markdown(f"**What-If ({eff_adj:+d}% demand)**")
        sim_wi = simulate_15_days(df, model, features, eff_adj)
        fig_wi = simulation_chart(sim_wi, dark, threshold)
        fig_wi.update_layout(title=dict(text=f"What-If ({eff_adj:+d}%)"), height=310)
        st.plotly_chart(fig_wi, use_container_width=True,
                        config={"displayModeBar": False})

    st.divider()

    # ── Sensitivity sweep ─────────────────────────────────────────────────────
    st.markdown(f'<div style="font-size:0.88rem;font-weight:700;'
                f'color:{t["text_primary"]};margin-bottom:12px;">'
                f'🔄 Sensitivity — Days Remaining vs Demand Change</div>',
                unsafe_allow_html=True)

    sweep_vals = list(range(-30, 35, 5))
    sweep_days = [predict_refill(df, model, features, v)["days_remaining"]
                  for v in sweep_vals]
    bar_colors = [_rgba(t["success"], 0.85) if d > base_pred["days_remaining"]
                  else _rgba(t["danger"], 0.85) for d in sweep_days]

    fig_sw = go.Figure(go.Bar(
        x=[f"{v:+d}%" for v in sweep_vals],
        y=sweep_days,
        marker_color=bar_colors,
        text=sweep_days,
        textposition="outside",
        textfont=dict(size=10),
    ))
    fig_sw.add_hline(y=base_pred["days_remaining"],
                     line_dash="dot", line_color=t["text_secondary"],
                     annotation_text="Baseline",
                     annotation_font=dict(color=t["text_secondary"], size=10))
    fig_sw.update_layout(
        **_layout_defaults(dark, "Sensitivity: Days Until Refill vs Demand Change"),
        height=300,
        xaxis_title="Demand Adjustment (%)",
        yaxis_title="Days Remaining",
        showlegend=False,
    )
    st.plotly_chart(fig_sw, use_container_width=True, config={"displayModeBar": False})
