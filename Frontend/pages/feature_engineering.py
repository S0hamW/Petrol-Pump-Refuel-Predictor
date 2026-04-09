"""
FuelIQ — Feature Engineering Page (v5)
"""
import streamlit as st
import pandas as pd
from utils.theme import get_theme, no_data_state
from utils.data_loader import load_selected_features
from utils.chart_helpers import feature_importance_chart


def render():
    dark = st.session_state.get("dark_mode", True)
    t    = get_theme(dark)
    df: pd.DataFrame = st.session_state.get("df", None)

    st.markdown("""
    <div class="page-header">
        <div class="page-icon">🔧</div>
        <div>
            <div class="page-title">Feature Engineering</div>
            <div class="page-sub">Engineered features that power the Random Forest classifier</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if df is None:
        no_data_state("Feature Engineering", "🔧")
        return

    st.markdown(f"""
    <div class="fiq-card-accent">
        <div style="font-size:0.86rem;color:{t['text_secondary']};line-height:1.8;">
            The pipeline engineers <b style="color:{t['accent']}">12+ derived features</b> from raw
            petrol pump logs — capturing stock dynamics, temporal patterns, and lagged sales signals.<br>
            <span style="font-size:0.78rem;">
                Dataset loaded: <b style="color:{t['text_primary']}">{len(df):,} rows ×
                {len(df.columns)} columns</b>
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Feature Importance + Table ─────────────────────────────────────────────
    feat_df  = load_selected_features()
    has_corr = ("Correlation_with_Target" in feat_df.columns and
                feat_df["Correlation_with_Target"].abs().sum() > 0)

    col_ch, col_table = st.columns([3, 2], gap="medium")

    with col_ch:
        st.markdown('<div class="fiq-card" style="padding:16px;">', unsafe_allow_html=True)
        st.markdown('<div class="fiq-card-header">MODEL FEATURE IMPORTANCE (RANDOM FOREST)</div>',
                    unsafe_allow_html=True)
        fig = feature_importance_chart(feat_df, dark)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    with col_table:
        st.markdown('<div class="fiq-card" style="padding:16px;">', unsafe_allow_html=True)
        st.markdown('<div class="fiq-card-header">IMPORTANCE SCORES</div>',
                    unsafe_allow_html=True)
        top = feat_df.sort_values("Importance", ascending=False)
        for _, row in top.iterrows():
            imp    = float(row["Importance"])
            bar_w  = min(int(imp * 400), 100)
            corr   = float(row.get("Correlation_with_Target", 0))
            corr_color = (t["danger"] if corr < -0.1 else
                          (t["success"] if corr > 0.1 else t["text_secondary"]))
            corr_str = (f'<span style="color:{corr_color};">{corr:+.3f}</span>'
                        if has_corr else "")
            st.markdown(f"""
            <div style="margin-bottom:10px;">
                <div style="display:flex;justify-content:space-between;
                            font-size:0.78rem;margin-bottom:4px;">
                    <b style="color:{t['text_primary']}">{row['Feature']}</b>
                    <span style="color:{t['accent']};font-weight:700">{imp:.3f}
                        {'&nbsp;&nbsp;' + corr_str if has_corr else ''}
                    </span>
                </div>
                <div style="background:{t['border']};border-radius:4px;height:5px;overflow:hidden;">
                    <div style="width:{bar_w}%;max-width:100%;height:100%;
                                background:{t['accent']};border-radius:4px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    # ── Feature Groups ─────────────────────────────────────────────────────────
    BADGE_COLORS = {
        "Continuous": t["accent"],  "Lagged":   t["accent2"], "Counter": t["danger"],
        "Rolling":    t["success"], "Ordinal":  "#8b5cf6",    "Binary":  "#06b6d4",
        "Numeric":    t["text_secondary"],
    }

    GROUPS = {
        "📦 Stock Features": [
            ("Stock_Ratio",        "Continuous",
             "Closing_Stock / Opening_Stock",
             "Core signal — near-zero ratio strongly predicts next-day refill."),
            ("Prev_Closing",       "Lagged",
             "df['Closing_Stock'].shift(1)",
             "Yesterday's closing stock provides continuity context."),
            ("Days_Since_Refill",  "Counter",
             "Resets to 0 on each Refill_Required == Yes entry",
             "#1 importance feature. Long streaks signal impending refill."),
        ],
        "📈 Sales Rolling Features": [
            ("Rolling_7d_Sales",   "Rolling",
             "df['Total_Sold'].rolling(7).mean()",
             "Smooths daily noise — captures weekly demand momentum."),
            ("Prev_Total_Sold",    "Lagged",
             "df['Total_Sold'].shift(1)",
             "Yesterday's sold detects sharp day-over-day anomalies."),
        ],
        "📅 Temporal / Calendar Features": [
            ("DayOfWeek",          "Ordinal", "0=Mon → 6=Sun",
             "Weekends show 10–15% higher sales."),
            ("Is_Weekend",         "Binary",  "1 if DayOfWeek >= 5 else 0",
             "Binary Sat/Sun flag — directly captures weekend demand spike."),
            ("Is_Festival_Month",  "Binary",  "1 if Month in [10, 11] else 0",
             "Oct–Nov festival season drives significantly higher consumption."),
            ("Is_Monsoon_Month",   "Binary",  "1 if Month in [6, 7, 8, 9] else 0",
             "Monsoon season shows ~8% lower average sales."),
        ],
        "💰 Revenue Feature": [
            ("Cash",               "Numeric", "Raw daily cash collection (₹)",
             "Correlates with sales volume — useful proxy for demand."),
        ],
    }

    for group_name, features in GROUPS.items():
        with st.expander(group_name, expanded=True):
            for feat_name, badge, formula, why in features:
                in_df = feat_name in df.columns
                bc    = BADGE_COLORS.get(badge, t["accent"])
                st.markdown(f"""
                <div class="feat-row" style="border-color:{bc}30">
                    <span style="background:{bc}18;color:{bc};border-radius:7px;
                                 padding:3px 9px;font-size:0.7rem;font-weight:700;
                                 white-space:nowrap;flex-shrink:0;margin-top:2px;">
                        {badge}
                    </span>
                    <div>
                        <div class="feat-name">
                            {feat_name}
                            {'&nbsp;<span style="font-size:0.65rem;color:' + t["success"] + ';">✓ in dataset</span>'
                             if in_df else
                             '&nbsp;<span style="font-size:0.65rem;color:' + t["danger"] + ';">✗ derived</span>'}
                        </div>
                        <div class="feat-formula">formula: {formula}</div>
                        <div class="feat-why">💡 {why}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.divider()

    # ── Column presence check ──────────────────────────────────────────────────
    st.markdown(f'<div style="font-size:0.88rem;font-weight:700;'
                f'color:{t["text_primary"]};margin-bottom:10px;">📋 Column Presence in Loaded Dataset</div>',
                unsafe_allow_html=True)

    expected = ["Date", "Opening_Stock", "Closing_Stock", "Total_Sold", "Target",
                "Refill_Required", "Rolling_7d_Sales", "Days_Since_Refill", "Stock_Ratio",
                "DayOfWeek", "Is_Weekend", "Month", "Day",
                "Is_Festival_Month", "Is_Monsoon_Month"]
    cols_status = []
    for col in expected:
        present = col in df.columns
        sample  = str(df[col].dropna().iloc[0]) if present and df[col].notna().any() else "—"
        cols_status.append({
            "Column":  col,
            "Status":  "✅ Present" if present else "⬜ Missing",
            "Sample":  sample[:30],
        })
    st.dataframe(pd.DataFrame(cols_status), use_container_width=True,
                 hide_index=True, height=380)
