"""
FuelIQ — Main App Router (v5 Clean)
"""

import streamlit as st

# MUST be the absolute first Streamlit command
st.set_page_config(
    page_title="FuelIQ Dashboard",
    page_icon="⛽",
    layout="wide",
    initial_sidebar_state="expanded"
)

from utils.theme import apply_theme, get_theme, theme_toggle
import pages.home as home
import pages.data_overview as data_overview
import pages.feature_engineering as feature_engineering
import pages.visualizations as visualizations
import pages.model_insights as model_insights


def main():
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = True

    t = get_theme(st.session_state.dark_mode)
    apply_theme(st.session_state.dark_mode)

    if "current_page" not in st.session_state:
        st.session_state.current_page = "Dashboard"

    def nav_to(page):
        st.session_state.current_page = page

    # ── SIDEBAR ──
    with st.sidebar:
        st.markdown(f"""
        <div class="brand-wrap">
            <div class="brand-title">⛽ FuelIQ</div>
            <div class="brand-sub">Petrol Pump Refuel Predictor</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="nav-label">MAIN</div>', unsafe_allow_html=True)
        st.button("🏠 Dashboard",
                  type="primary" if st.session_state.current_page == "Dashboard" else "secondary",
                  on_click=nav_to, args=("Dashboard",), use_container_width=True)
        st.button("📋 Data Overview",
                  type="primary" if st.session_state.current_page == "Data Overview" else "secondary",
                  on_click=nav_to, args=("Data Overview",), use_container_width=True)

        st.markdown('<div class="nav-label">ANALYSIS</div>', unsafe_allow_html=True)
        st.button("🔧 Feature Engineering",
                  type="primary" if st.session_state.current_page == "Feature Engineering" else "secondary",
                  on_click=nav_to, args=("Feature Engineering",), use_container_width=True)
        st.button("📈 Visualizations",
                  type="primary" if st.session_state.current_page == "Visualizations" else "secondary",
                  on_click=nav_to, args=("Visualizations",), use_container_width=True)
        st.button("🧠 Model Insights",
                  type="primary" if st.session_state.current_page == "Model Insights" else "secondary",
                  on_click=nav_to, args=("Model Insights",), use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        df = st.session_state.get("df", None)
        if df is not None:
            r, c = len(df), len(df.columns)
            st.markdown(f"""
            <div style="background:{t['success']}1A;border:1px solid {t['success']}40;
                        padding:12px;border-radius:10px;text-align:center;margin-bottom:16px;">
                <div style="color:{t['success']};font-weight:700;font-size:0.75rem;">✅ DATA READY</div>
                <div style="color:{t['text_secondary']};font-size:0.7rem;margin-top:2px;">
                    {r:,} rows × {c} features
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background:{t['danger']}1A;border:1px solid {t['danger']}40;
                        padding:12px;border-radius:10px;text-align:center;margin-bottom:16px;">
                <div style="color:{t['danger']};font-weight:700;font-size:0.75rem;">⚠️ NO DATA LOADED</div>
            </div>
            """, unsafe_allow_html=True)

        theme_toggle()

    # ── PAGE ROUTER ──
    page = st.session_state.current_page
    if page == "Dashboard":
        home.render()
    elif page == "Data Overview":
        data_overview.render()
    elif page == "Feature Engineering":
        feature_engineering.render()
    elif page == "Visualizations":
        visualizations.render()
    elif page == "Model Insights":
        model_insights.render()


if __name__ == "__main__":
    main()
