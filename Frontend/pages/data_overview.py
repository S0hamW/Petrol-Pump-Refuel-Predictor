"""
FuelIQ — Data Overview Page (v5)
"""
import streamlit as st
import pandas as pd
from utils.theme import get_theme, no_data_state


def render():
    dark = st.session_state.get("dark_mode", True)
    t = get_theme(dark)
    df: pd.DataFrame = st.session_state.get("df", None)

    st.markdown("""
    <div class="page-header">
        <div class="page-icon">📋</div>
        <div>
            <div class="page-title">Data Overview</div>
            <div class="page-sub">Full dataset exploration · Schema validation · Export</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if df is None:
        no_data_state("Data Overview", "📋")
        return

    # ── Dataset summary banner ─────────────────────────────────────────────────
    d1_str, d2_str = "—", "—"
    if "Date" in df.columns:
        df_s = df.sort_values("Date")
        d1, d2 = df_s["Date"].iloc[0], df_s["Date"].iloc[-1]
        d1_str = d1.strftime("%d %b %Y") if hasattr(d1, "strftime") else str(d1)[:10]
        d2_str = d2.strftime("%d %b %Y") if hasattr(d2, "strftime") else str(d2)[:10]

    refill_cnt = int(df["Target"].sum()) if "Target" in df.columns else 0
    null_total = int(df.isnull().sum().sum())

    st.markdown(f"""
    <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-bottom:20px;">
        <div style="background:{t['card_bg']};border:1px solid {t['border']};border-radius:10px;padding:14px 16px;">
            <div style="font-size:0.55rem;font-weight:800;letter-spacing:1.4px;text-transform:uppercase;
                        color:{t['text_secondary']};margin-bottom:5px;">Total Rows</div>
            <div style="font-size:1.6rem;font-weight:800;color:{t['accent']}">{len(df):,}</div>
        </div>
        <div style="background:{t['card_bg']};border:1px solid {t['border']};border-radius:10px;padding:14px 16px;">
            <div style="font-size:0.55rem;font-weight:800;letter-spacing:1.4px;text-transform:uppercase;
                        color:{t['text_secondary']};margin-bottom:5px;">Columns</div>
            <div style="font-size:1.6rem;font-weight:800;color:{t['text_primary']}">{len(df.columns)}</div>
        </div>
        <div style="background:{t['card_bg']};border:1px solid {t['border']};border-radius:10px;padding:14px 16px;">
            <div style="font-size:0.55rem;font-weight:800;letter-spacing:1.4px;text-transform:uppercase;
                        color:{t['text_secondary']};margin-bottom:5px;">Start Date</div>
            <div style="font-size:0.95rem;font-weight:700;color:{t['text_primary']}">{d1_str}</div>
        </div>
        <div style="background:{t['card_bg']};border:1px solid {t['border']};border-radius:10px;padding:14px 16px;">
            <div style="font-size:0.55rem;font-weight:800;letter-spacing:1.4px;text-transform:uppercase;
                        color:{t['text_secondary']};margin-bottom:5px;">End Date</div>
            <div style="font-size:0.95rem;font-weight:700;color:{t['text_primary']}">{d2_str}</div>
        </div>
        <div style="background:{t['card_bg']};border:1px solid {t['border']};border-radius:10px;padding:14px 16px;">
            <div style="font-size:0.55rem;font-weight:800;letter-spacing:1.4px;text-transform:uppercase;
                        color:{t['text_secondary']};margin-bottom:5px;">Missing Values</div>
            <div style="font-size:1.6rem;font-weight:800;
                        color:{t['danger'] if null_total > 0 else t['success']}">{null_total}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Column schema ──────────────────────────────────────────────────────────
    st.markdown(f'<div style="font-size:0.88rem;font-weight:700;'
                f'color:{t["text_primary"]};margin-bottom:10px;">📊 Dataset Schema</div>',
                unsafe_allow_html=True)

    col_types = pd.DataFrame({
        "Column":        df.columns,
        "Data Type":     df.dtypes.astype(str),
        "Non-Null":      df.notnull().sum().values,
        "Missing":       df.isnull().sum().values,
        "% Missing":     (df.isnull().sum() / len(df) * 100).round(2).values,
        "Sample Value":  [str(df[c].dropna().iloc[0]) if df[c].notna().any() else "—"
                          for c in df.columns],
    })

    st.dataframe(col_types, use_container_width=True, hide_index=True, height=300)

    st.divider()

    # ── Full dataset preview ───────────────────────────────────────────────────
    st.markdown(f'<div style="font-size:0.88rem;font-weight:700;'
                f'color:{t["text_primary"]};margin-bottom:10px;">'
                f'🔍 Dataset Preview <span style="color:{t["text_secondary"]};'
                f'font-size:0.75rem;font-weight:500">'
                f'({len(df):,} total rows — scroll to explore)</span></div>',
                unsafe_allow_html=True)

    st.dataframe(df, use_container_width=True, height=450)

    st.divider()

    # ── Descriptive statistics ─────────────────────────────────────────────────
    st.markdown(f'<div style="font-size:0.88rem;font-weight:700;'
                f'color:{t["text_primary"]};margin-bottom:10px;">📈 Descriptive Statistics</div>',
                unsafe_allow_html=True)

    numeric_df = df.select_dtypes(include="number")
    if not numeric_df.empty:
        desc = numeric_df.describe().round(2)
        st.dataframe(desc, use_container_width=True, height=220)

    st.divider()

    # ── Export & last-entry verification ──────────────────────────────────────
    col1, col2 = st.columns([1, 1], gap="medium")

    with col1:
        st.markdown(f'<div style="font-size:0.88rem;font-weight:700;'
                    f'color:{t["text_primary"]};margin-bottom:8px;">📥 Export Processed Data</div>',
                    unsafe_allow_html=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download Cleaned CSV",
            data=csv,
            file_name="fueliq_processed_data.csv",
            mime="text/csv",
            type="primary",
            use_container_width=True,
        )

    with col2:
        with st.expander("🔎 Verify Last Entry"):
            if "Date" in df.columns:
                last_row = df.sort_values("Date").iloc[-1]
                for col in ["Date", "Opening_Stock", "Total_Sold",
                            "Closing_Stock", "Target", "Refill_Required"]:
                    if col in last_row.index:
                        val = last_row[col]
                        disp = f"{val:,.2f}" if isinstance(val, float) else str(val)
                        col_c = t["accent"] if col == "Target" else t["text_secondary"]
                        st.markdown(f"""
                        <div style="display:flex;justify-content:space-between;
                                    padding:5px 0;border-bottom:1px solid {t['border']};
                                    font-size:0.8rem;">
                            <span style="color:{t['text_primary']}">{col}</span>
                            <span style="font-weight:700;color:{col_c}">{disp}</span>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("No Date column found.")
