"""
FuelIQ — Data Overview Page (v4)
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
            <div class="page-sub">Raw dataset exploration and column validation</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if df is None:
        no_data_state("Data Overview", "📋")
        return

    # Basic stats
    st.markdown(f"""
    <div class="fiq-card">
        <div style="font-size:0.86rem;color:{t['text_secondary']};line-height:1.7;">
            The current active dataset contains <b style="color:{t['text_primary']}">{len(df):,} rows</b> and 
            <b style="color:{t['text_primary']}">{len(df.columns)} columns</b>. The data has been 
            automatically normalized to ensure all downstream modeling and visualization features function correctly.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Quick Columns Schema ──────────────────────────────────────────────────
    st.markdown(f'<div style="font-size:0.88rem;font-weight:700;'
                f'color:{t["text_primary"]};margin-bottom:12px;">📊 Dataset Schema & Missing Values</div>',
                unsafe_allow_html=True)
    
    col_types = pd.DataFrame({
        "Column": df.columns,
        "Data Type": df.dtypes.astype(str),
        "Missing Values": df.isnull().sum(),
        "% Missing": (df.isnull().sum() / len(df) * 100).round(2)
    })
    
    # highlight missing values in red
    def color_missing(val):
        color = 'red' if val > 0 else ''
        return f'color: {color}'
    
    st.dataframe(col_types.style.map(color_missing, subset=['Missing Values', '% Missing']), 
                 use_container_width=True, hide_index=True)

    st.divider()

    # ── Dataset Preview ───────────────────────────────────────────────────────
    st.markdown(f'<div style="font-size:0.88rem;font-weight:700;'
                f'color:{t["text_primary"]};margin-bottom:12px;">🔍 Interactive Data Preview</div>',
                unsafe_allow_html=True)
    
    st.dataframe(df.head(100), use_container_width=True, height=400)

    # ── Export & Verification ──────────────────────────────────────────────────
    st.divider()
    col1, col2 = st.columns([1, 1], gap="medium")
    
    with col1:
        st.markdown(f'<div style="font-size:0.88rem;font-weight:700;'
                    f'color:{t["text_primary"]};margin-bottom:8px;">📥 Export Processed Data</div>',
                    unsafe_allow_html=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Cleaned CSV",
            data=csv,
            file_name='fueliq_processed_data.csv',
            mime='text/csv',
            type="primary",
            use_container_width=True
        )

    with col2:
        with st.expander("Verify Last Entry Computations"):
            if "Date" in df.columns:
                last_row = df.sort_values("Date").iloc[-1]
                for col in ["Date", "Opening_Stock", "Total_Sold", "Closing_Stock", "Target"]:
                    if col in last_row:
                        val = last_row[col]
                        # format floats
                        if isinstance(val, (int, float)):
                            disp = f"{val:,.2f}"
                        else:
                            disp = str(val)
                        col_c = t["accent"] if col == "Target" else t["text_secondary"]
                        st.markdown(f"""
                        <div style="display:flex; justify-content:space-between; 
                                    padding:4px 0; border-bottom:1px solid {t['border']}; 
                                    font-size:0.8rem;">
                            <span style="color:{t['text_primary']}">{col}</span>
                            <span style="font-weight:600; color:{col_c}">{disp}</span>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("No Date column found to determine last entry.")
