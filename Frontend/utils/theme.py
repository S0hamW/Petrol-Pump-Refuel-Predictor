"""
FuelIQ Theme System — v5 (Dark, solid colors, no gradients on cards)
"""
import streamlit as st


DARK_THEME = {
    "bg":            "#0E1117",
    "sidebar_bg":    "#0a0d13",
    "card_bg":       "#161b27",
    "card_bg2":      "#1c2233",
    "border":        "#272f43",
    "border2":       "#323d57",
    "accent":        "#f59e0b",   # amber / gold
    "accent2":       "#22c55e",   # green
    "accent3":       "#6366f1",   # indigo
    "text_primary":  "#e8eaf0",
    "text_secondary": "#6b7a99",
    "success":       "#22c55e",
    "danger":        "#ef4444",
    "warning":       "#f97316",
    "plot_paper":    "#161b27",
    "plot_bg":       "#0e1117",
    "grid_color":    "#1e2536",
    "template":      "plotly_dark",
}

LIGHT_THEME = {
    "bg":            "#f4f6fb",
    "sidebar_bg":    "#ffffff",
    "card_bg":       "#ffffff",
    "card_bg2":      "#f8f9fc",
    "border":        "#e2e8f0",
    "border2":       "#cbd5e1",
    "accent":        "#d97706",
    "accent2":       "#16a34a",
    "accent3":       "#4f46e5",
    "text_primary":  "#0f172a",
    "text_secondary": "#64748b",
    "success":       "#16a34a",
    "danger":        "#dc2626",
    "warning":       "#ea580c",
    "plot_paper":    "#ffffff",
    "plot_bg":       "#f8f9fc",
    "grid_color":    "#e2e8f0",
    "template":      "plotly_white",
}


def get_theme(dark: bool) -> dict:
    return DARK_THEME if dark else LIGHT_THEME


def apply_theme(dark: bool):
    t = get_theme(dark)
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* ── Hide Streamlit default page navigation ── */
[data-testid="stSidebarNav"],
section[data-testid="stSidebarNav"] {{
    display: none !important;
}}

/* ── Root ── */
html, body, [data-testid="stApp"] {{
    background: {t['bg']} !important;
    color: {t['text_primary']} !important;
    font-family: 'Inter', sans-serif !important;
}}

/* ── Sidebar ── */
[data-testid="stSidebar"] > div:first-child,
[data-testid="stSidebar"] {{
    background: {t['sidebar_bg']} !important;
    border-right: 1px solid {t['border']} !important;
}}

/* ── Main content ── */
.main .block-container {{
    padding: 1.5rem 2rem 2rem 2rem !important;
    max-width: 100% !important;
}}

/* ══════════════════════════════
   BRAND HEADER
══════════════════════════════ */
.brand-wrap {{
    padding: 20px 18px 14px 18px;
    border-bottom: 1px solid {t['border']};
    margin-bottom: 12px;
}}
.brand-title {{
    font-size: 1.35rem;
    font-weight: 900;
    color: {t['accent']};
    letter-spacing: -0.5px;
    line-height: 1.15;
}}
.brand-sub {{
    font-size: 0.56rem;
    color: {t['text_secondary']};
    margin-top: 3px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1.3px;
}}

/* ── Nav labels ── */
.nav-label {{
    font-size: 0.54rem;
    font-weight: 800;
    color: {t['text_secondary']};
    letter-spacing: 2px;
    text-transform: uppercase;
    margin: 16px 0 4px 8px;
}}

/* ══════════════════════════════
   NAV BUTTONS
══════════════════════════════ */
[data-testid="stSidebar"] button {{
    background: transparent !important;
    border: none !important;
    color: {t['text_secondary']} !important;
    text-align: left !important;
    font-size: 0.84rem !important;
    font-weight: 500 !important;
    padding: 9px 14px !important;
    border-radius: 8px !important;
    transition: all 0.12s ease !important;
    margin-bottom: 2px !important;
    width: 100% !important;
}}
[data-testid="stSidebar"] button:hover {{
    background: {t['card_bg2']} !important;
    color: {t['text_primary']} !important;
}}
[data-testid="stSidebar"] button[kind="primary"] {{
    background: {t['accent']}18 !important;
    color: {t['accent']} !important;
    font-weight: 700 !important;
    border-left: 3px solid {t['accent']} !important;
}}

/* ══════════════════════════════
   PAGE HEADER
══════════════════════════════ */
.page-header {{
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 22px;
    padding-bottom: 16px;
    border-bottom: 1px solid {t['border']};
}}
.page-icon {{
    width: 44px; height: 44px;
    background: {t['accent']}18;
    border: 1px solid {t['accent']}30;
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.3rem;
    flex-shrink: 0;
}}
.page-title {{
    font-size: 1.5rem;
    font-weight: 800;
    color: {t['text_primary']};
    letter-spacing: -0.5px;
    line-height: 1.2;
}}
.page-sub {{
    font-size: 0.79rem;
    color: {t['text_secondary']};
    margin-top: 3px;
}}

/* ══════════════════════════════
   STAT CARDS
══════════════════════════════ */
.stat-row {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-bottom: 20px;
}}
.stat-card {{
    background: {t['card_bg']};
    border: 1px solid {t['border']};
    border-radius: 12px;
    padding: 18px 18px 14px 18px;
    transition: border-color .2s, transform .15s;
    position: relative;
    overflow: hidden;
}}
.stat-card:hover {{
    border-color: {t['border2']};
    transform: translateY(-2px);
}}
.stat-label {{
    font-size: 0.6rem;
    font-weight: 700;
    letter-spacing: 1.4px;
    text-transform: uppercase;
    color: {t['text_secondary']};
    margin-bottom: 8px;
}}
.stat-value {{
    font-size: 1.65rem;
    font-weight: 800;
    color: {t['text_primary']};
    line-height: 1.1;
    letter-spacing: -0.5px;
}}
.stat-delta {{ font-size: 0.72rem; font-weight: 600; margin-top: 5px; }}
.delta-up   {{ color: {t['success']}; }}
.delta-warn {{ color: {t['warning']}; }}
.delta-down {{ color: {t['danger']}; }}
.delta-mute {{ color: {t['text_secondary']}; }}

/* ══════════════════════════════
   PREDICTION CARD — solid, no gradient
══════════════════════════════ */
.pred-card {{
    background: {t['card_bg']};
    border: 1px solid {t['accent2']}45;
    border-radius: 14px;
    padding: 24px 26px;
    margin-bottom: 16px;
    position: relative;
    overflow: hidden;
}}
.pred-ai-badge {{
    position: absolute; top: 16px; right: 18px;
    background: {t['accent2']}20;
    border: 1px solid {t['accent2']}50;
    color: {t['accent2']};
    padding: 3px 11px;
    border-radius: 20px;
    font-size: 0.63rem;
    font-weight: 700;
    letter-spacing: 0.4px;
}}
.pred-header {{
    font-size: 0.6rem;
    font-weight: 800;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: {t['accent']};
    margin-bottom: 18px;
}}
.pred-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
    margin-bottom: 20px;
}}
.pred-col-label {{
    font-size: 0.68rem;
    color: {t['text_secondary']};
    font-weight: 500;
    margin-bottom: 5px;
}}
.pred-col-value {{
    font-size: 1.85rem;
    font-weight: 800;
    line-height: 1.1;
    letter-spacing: -0.5px;
}}
.pred-col-sub {{
    font-size: 0.68rem;
    color: {t['text_secondary']};
    margin-top: 4px;
}}
.conf-bar-label {{
    display: flex;
    justify-content: space-between;
    font-size: 0.72rem;
    color: {t['text_secondary']};
    margin-bottom: 6px;
}}
.conf-bar-track {{
    height: 6px;
    background: {t['border']};
    border-radius: 4px;
    overflow: hidden;
}}
.conf-bar-fill {{
    height: 100%;
    border-radius: 4px;
    background: {t['accent']};
}}

/* ══════════════════════════════
   GENERIC CARDS
══════════════════════════════ */
.fiq-card {{
    background: {t['card_bg']};
    border: 1px solid {t['border']};
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 14px;
}}
.fiq-card-accent {{
    background: {t['card_bg']};
    border: 1px solid {t['accent']}30;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 14px;
}}
.fiq-card-header {{
    font-size: 0.58rem;
    font-weight: 800;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: {t['text_secondary']};
    margin-bottom: 12px;
}}
.card-title {{
    font-size: 0.92rem;
    font-weight: 700;
    color: {t['text_primary']};
    margin-bottom: 4px;
}}

/* ══════════════════════════════
   WHY CARD
══════════════════════════════ */
.why-card {{
    background: {t['card_bg']};
    border: 1px solid {t['border']};
    border-radius: 12px;
    padding: 18px 20px;
    margin-bottom: 14px;
}}
.why-item {{
    display: flex;
    gap: 12px;
    padding: 11px 0;
    border-bottom: 1px solid {t['border']};
    line-height: 1.6;
    font-size: 0.83rem;
    color: {t['text_secondary']};
}}
.why-item:last-child {{ border-bottom: none; }}
.why-dot {{
    width: 8px; height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
    margin-top: 6px;
}}

/* ══════════════════════════════
   NO DATA STATE
══════════════════════════════ */
.no-data-wrap {{
    text-align: center;
    padding: 80px 20px;
}}
.no-data-icon   {{ font-size: 4rem; display: block; margin-bottom: 14px; }}
.no-data-badge  {{
    display: inline-block;
    background: {t['accent']}18;
    border: 1px solid {t['accent']}35;
    color: {t['accent']};
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 700;
    margin-bottom: 18px;
    letter-spacing: 0.5px;
}}
.no-data-title {{
    font-size: 1.2rem;
    font-weight: 800;
    color: {t['text_primary']};
    margin-bottom: 10px;
}}
.no-data-sub {{
    font-size: 0.84rem;
    color: {t['text_secondary']};
    max-width: 380px;
    margin: 0 auto;
    line-height: 1.75;
}}
.no-data-cta {{
    display: inline-block;
    margin-top: 24px;
    background: {t['accent']};
    color: #000;
    font-weight: 800;
    font-size: 0.8rem;
    padding: 10px 24px;
    border-radius: 10px;
    text-decoration: none;
    letter-spacing: 0.2px;
}}

/* ══════════════════════════════
   FEATURE ROWS
══════════════════════════════ */
.feat-row {{
    background: {t['card_bg']};
    border: 1px solid {t['border']};
    border-radius: 10px;
    padding: 13px 16px;
    margin-bottom: 7px;
    display: flex;
    align-items: flex-start;
    gap: 14px;
    transition: border-color .15s;
}}
.feat-row:hover {{ border-color: {t['accent']}35; }}
.feat-name {{
    font-size: 0.88rem;
    font-weight: 700;
    color: {t['text_primary']};
}}
.feat-formula {{
    font-size: 0.73rem;
    font-family: 'Courier New', monospace;
    color: {t['accent2']};
    margin-top: 3px;
}}
.feat-why {{
    font-size: 0.76rem;
    color: {t['text_secondary']};
    margin-top: 4px;
    line-height: 1.5;
}}

/* ══════════════════════════════
   METRIC CARDS (Model Insights)
══════════════════════════════ */
.metric-card {{
    background: {t['card_bg']};
    border: 1px solid {t['border']};
    border-radius: 12px;
    padding: 24px 18px;
    text-align: center;
    transition: transform .15s, box-shadow .15s;
}}
.metric-card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.3);
}}
.metric-value {{
    font-size: 2.5rem;
    font-weight: 900;
    color: {t['accent']};
    line-height: 1.1;
    letter-spacing: -1px;
}}
.metric-label {{
    font-size: 0.65rem;
    color: {t['text_secondary']};
    font-weight: 700;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    margin-top: 8px;
}}
.metric-delta {{
    font-size: 0.75rem;
    color: {t['success']};
    margin-top: 6px;
    font-weight: 500;
}}

/* ══════════════════════════════
   STREAMLIT NATIVE OVERRIDES
══════════════════════════════ */
[data-testid="stMetric"] {{
    background: {t['card_bg']} !important;
    border: 1px solid {t['border']} !important;
    border-radius: 12px !important;
    padding: 16px !important;
}}
[data-testid="stMetricLabel"] {{
    color: {t['text_secondary']} !important;
    font-size: 0.65rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.8px !important;
}}
[data-testid="stMetricValue"] {{
    color: {t['text_primary']} !important;
    font-size: 1.5rem !important;
    font-weight: 800 !important;
}}
div[data-testid="stProgress"] > div {{
    background: {t['border']} !important;
    border-radius: 8px !important;
}}
div[data-testid="stProgress"] > div > div {{
    background: {t['accent']} !important;
    border-radius: 8px !important;
}}
.stButton > button {{
    border-radius: 9px !important;
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    transition: all .15s ease !important;
    font-size: 0.82rem !important;
    border: 1px solid {t['border']} !important;
    color: {t['text_primary']} !important;
    background: {t['card_bg']} !important;
}}
.stButton > button:hover {{
    border-color: {t['accent']}55 !important;
    color: {t['accent']} !important;
}}
.stButton > button[kind="primary"] {{
    background: {t['accent']} !important;
    border-color: {t['accent']} !important;
    color: #000 !important;
    font-weight: 800 !important;
}}
.stButton > button[kind="primary"]:hover {{
    opacity: 0.88 !important;
    transform: translateY(-1px) !important;
}}
.stFileUploader section {{
    background: {t['card_bg']} !important;
    border: 1.5px dashed {t['border2']} !important;
    border-radius: 10px !important;
}}
.stSlider > div > div > div {{ background: {t['accent']} !important; }}
[data-testid="stExpander"] {{
    border: 1px solid {t['border']} !important;
    border-radius: 10px !important;
    background: {t['card_bg']} !important;
    overflow: hidden !important;
}}
[data-testid="stDataFrame"] {{
    border: 1px solid {t['border']} !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}}
.stSelectbox > div > div {{
    background: {t['card_bg']} !important;
    border: 1px solid {t['border']} !important;
    border-radius: 9px !important;
    color: {t['text_primary']} !important;
}}
.stTabs [data-baseweb="tab-list"] {{
    background: {t['card_bg']} !important;
    border-radius: 10px !important;
    padding: 4px !important;
    gap: 4px !important;
}}
.stTabs [data-baseweb="tab"] {{
    border-radius: 8px !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    color: {t['text_secondary']} !important;
    background: transparent !important;
}}
.stTabs [aria-selected="true"] {{
    background: {t['accent']}22 !important;
    color: {t['accent']} !important;
}}
h1, h2, h3, h4, h5, h6 {{
    color: {t['text_primary']} !important;
    font-family: 'Inter', sans-serif !important;
    letter-spacing: -0.3px !important;
}}
hr[data-testid="stDivider"] {{
    border-color: {t['border']} !important;
    margin: 1.2rem 0 !important;
}}
#MainMenu, footer, header {{ visibility: hidden !important; }}
</style>
""", unsafe_allow_html=True)


def theme_toggle():
    dark = st.session_state.get("dark_mode", True)
    label = "🌙 Dark" if dark else "☀️ Light"
    if st.button(f"{label} Mode", key="theme_toggle_btn",
                 use_container_width=True, help="Toggle dark / light mode"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()


def no_data_state(page_name: str = "this page", icon: str = "⛽"):
    dark = st.session_state.get("dark_mode", True)
    t = get_theme(dark)
    st.markdown(f"""
    <div class="no-data-wrap">
        <div class="no-data-badge">NO FILE LOADED</div>
        <div class="no-data-icon">{icon}</div>
        <div class="no-data-title">No data loaded yet</div>
        <div class="no-data-sub">
            <b style="color:{t['text_primary']}">{page_name}</b> requires petrol pump data.<br>
            Head to <b style="color:{t['accent']}">Dashboard</b> and upload a CSV / XLSX,
            or click <b style="color:{t['accent']}">Use Demo Data</b> to explore instantly.
        </div>
        <span class="no-data-cta">← Go to Dashboard</span>
    </div>
    """, unsafe_allow_html=True)
