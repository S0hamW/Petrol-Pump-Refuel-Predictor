import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="⛽ Refill Predictor",
    page_icon="⛽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DATA_PATH = r'D:\Petrol-Pump-Refuel-Predictor-main\Petrol-Pump-Refuel-Predictor-main\data'

# Theme toggle
with st.sidebar:
    theme = st.radio("🎨 Theme", ["Dark", "Light"])

if theme == "Light":
    bg        = "#ffffff"
    card_bg   = "#f5f5f5"
    text      = "#111111"
    border    = "#dddddd"
    subtitle  = "#888888"
    grid_col  = "#dddddd"
    inp_bg    = "#ffffff"
else:
    bg        = "#080810"
    card_bg   = "#0f0f1a"
    text      = "#e0e0e0"
    border    = "#1e1e2e"
    subtitle  = "#555555"
    grid_col  = "#1e1e2e"
    inp_bg    = "#0f0f1a"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;800&display=swap');
* {{ font-family: 'Syne', sans-serif; }}
.stApp {{ background: {bg}; color: {text}; }}
.big-title {{ font-size: 3.2rem; font-weight: 800; color: #f7941d; letter-spacing: -2px; line-height: 1.1; margin-bottom: 0.5rem; }}
.subtitle {{ color: {subtitle}; font-family: 'Space Mono', monospace; font-size: 0.85rem; margin-bottom: 3rem; }}
.upload-box {{ background: {card_bg}; border: 2px dashed #f7941d44; border-radius: 20px; padding: 3rem 2rem; margin-bottom: 1.5rem; }}
.card {{ background: {card_bg}; border: 1px solid {border}; border-radius: 16px; padding: 1.5rem; margin-bottom: 1rem; }}
.card-title {{ font-size: 0.7rem; color: #f7941d; text-transform: uppercase; letter-spacing: 3px; font-family: 'Space Mono', monospace; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 1px solid #f7941d22; }}
.big-num {{ font-size: 2.8rem; font-weight: 800; font-family: 'Space Mono', monospace; color: #f7941d; }}
.refill-yes {{ background: linear-gradient(135deg, #1a0800, #200e00); border: 1.5px solid #f7941d66; border-radius: 12px; padding: 1rem 1.5rem; margin: 0.4rem 0; display: flex; justify-content: space-between; align-items: center; }}
.refill-no {{ background: {card_bg}; border: 1px solid {border}; border-radius: 12px; padding: 1rem 1.5rem; margin: 0.4rem 0; display: flex; justify-content: space-between; align-items: center; }}
.stButton > button {{ background: #f7941d !important; color: #000 !important; font-weight: 700 !important; font-family: 'Syne', sans-serif !important; border: none !important; border-radius: 10px !important; padding: 0.75rem 2rem !important; font-size: 1rem !important; width: 100% !important; }}
.stButton > button:hover {{ opacity: 0.85 !important; }}
div[data-testid="stSidebarContent"] {{ background: {card_bg}; }}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def load_model():
    model    = joblib.load(os.path.join(DATA_PATH, 'refill_model.pkl'))
    features = joblib.load(os.path.join(DATA_PATH, 'feature_list.pkl'))
    return model, features

try:
    model, features = load_model()
except Exception as e:
    st.error(f"Model not found: {e}")
    st.info("Run all notebook cells first to generate model files.")
    st.stop()

if 'page' not in st.session_state:
    st.session_state.page = 'upload'
if 'result_df' not in st.session_state:
    st.session_state.result_df = None

# ── PAGE 1 — UPLOAD ──────────────────────────────────────────
if st.session_state.page == 'upload':

    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        st.markdown('<br><br>', unsafe_allow_html=True)
        st.markdown('<div class="big-title">⛽ Refill<br>Predictor</div>', unsafe_allow_html=True)
        st.markdown('<div class="subtitle">Upload your petrol pump Excel file<br>and get instant refill predictions with graphs</div>', unsafe_allow_html=True)

        st.markdown('<div class="upload-box">', unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Drop your Excel file here", type=['xlsx', 'xls'])
        st.markdown('</div>', unsafe_allow_html=True)

        if uploaded_file:
            st.success(f"✅ File ready: **{uploaded_file.name}**")
            if st.button("⚡ Run Predictions →"):
                with st.spinner("Analysing your data..."):
                    try:
                        df = pd.read_excel(uploaded_file)
                        df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce', format='mixed')
                        int_cols = ['Opening_Stock','MS_Sold','HSD1_Sold','HSD2_Sold','HSD3_Sold',
                                    'Total_Sold','Closing_Stock','Cash','Online','Card','Dip']
                        for col in int_cols:
                            if col in df.columns:
                                df[col] = df[col].fillna(df[col].median()).astype(int)

                        df['DayOfWeek']  = df['Date'].dt.dayofweek
                        df['Month']      = df['Date'].dt.month
                        df['Total_Sold'] = df['MS_Sold'] + df['HSD1_Sold'] + df['HSD2_Sold'] + df['HSD3_Sold']

                        X     = df[features]
                        preds = model.predict(X)
                        probs = model.predict_proba(X)[:, 1]

                        df['Refill_Predicted'] = ['Yes' if p == 1 else 'No' for p in preds]
                        df['Confidence_%']     = (probs * 100).round(1)

                        st.session_state.result_df = df
                        st.session_state.page = 'results'
                        st.rerun()

                    except Exception as e:
                        st.error(f"Error: {e}")

# ── PAGE 2 — RESULTS ─────────────────────────────────────────
elif st.session_state.page == 'results':

    df = st.session_state.result_df

    col_back, col_title = st.columns([1, 5])
    with col_back:
        if st.button("← Upload New File"):
            st.session_state.page = 'upload'
            st.session_state.result_df = None
            st.rerun()
    with col_title:
        st.markdown("## ⛽ Prediction Results")

    st.markdown("---")

    total      = len(df)
    refill_yes = (df['Refill_Predicted'] == 'Yes').sum()
    refill_no  = total - refill_yes
    avg_conf   = df[df['Refill_Predicted'] == 'Yes']['Confidence_%'].mean()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="card"><div class="card-title">Total Days</div><div class="big-num">{total}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="card"><div class="card-title">Refill Days</div><div class="big-num" style="color:#f7941d">{refill_yes}</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="card"><div class="card-title">No Refill Days</div><div class="big-num" style="color:#00c853">{refill_no}</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="card"><div class="card-title">Avg Confidence</div><div class="big-num">{avg_conf:.1f}%</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    month_names = {1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'May',6:'Jun',
                   7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec'}
    monthly = df[df['Refill_Predicted']=='Yes'].groupby('Month').size().reset_index(name='Refills')
    monthly['MonthName'] = monthly['Month'].map(month_names)

    left, right = st.columns(2)

    with left:
        st.markdown('<div class="card"><div class="card-title">📅 Refills Needed Per Month</div>', unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(7, 3.5))
        fig.patch.set_facecolor(card_bg)
        ax.set_facecolor(card_bg)
        bars = ax.bar(monthly['MonthName'], monthly['Refills'], color='#f7941d', width=0.6, zorder=3)
        ax.set_xlabel('Month', color=subtitle, fontsize=9)
        ax.set_ylabel('Refill Days', color=subtitle, fontsize=9)
        ax.tick_params(colors=subtitle, labelsize=8)
        ax.spines[['top','right','left','bottom']].set_color(border)
        ax.yaxis.grid(True, color=grid_col, zorder=0)
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                    str(int(bar.get_height())), ha='center', va='bottom', color='#f7941d', fontsize=8)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="card"><div class="card-title">📈 Closing Stock Trend</div>', unsafe_allow_html=True)
        fig2, ax2 = plt.subplots(figsize=(7, 3.5))
        fig2.patch.set_facecolor(card_bg)
        ax2.set_facecolor(card_bg)
        ax2.plot(df['Date'], df['Closing_Stock'], color='#f7941d', linewidth=1.5, zorder=3)
        ax2.fill_between(df['Date'], df['Closing_Stock'], alpha=0.08, color='#f7941d')
        refill_dates = df[df['Refill_Predicted']=='Yes']
        ax2.scatter(refill_dates['Date'], refill_dates['Closing_Stock'],
                    color='#ff4444', s=25, zorder=5, label='Refill Day')
        ax2.set_xlabel('Date', color=subtitle, fontsize=9)
        ax2.set_ylabel('Closing Stock (L)', color=subtitle, fontsize=9)
        ax2.tick_params(colors=subtitle, labelsize=7)
        ax2.spines[['top','right','left','bottom']].set_color(border)
        ax2.yaxis.grid(True, color=grid_col, zorder=0)
        ax2.legend(facecolor=card_bg, labelcolor=subtitle, fontsize=8)
        plt.tight_layout()
        st.pyplot(fig2)
        plt.close()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="card-title">🔮 Monthly Refill Forecast</div>', unsafe_allow_html=True)
    for _, row in monthly.iterrows():
        mname = row['MonthName']
        count = int(row['Refills'])
        if count >= 10:
            msg   = f"🔴 High demand — expect ~{count} refill days in {mname}"
            style = "refill-yes"
        elif count >= 5:
            msg   = f"🟡 Moderate demand — plan for ~{count} refill days in {mname}"
            style = "refill-yes"
        else:
            msg   = f"🟢 Low demand — only ~{count} refill days expected in {mname}"
            style = "refill-no"
        st.markdown(f'<div class="{style}"><span style="font-weight:700;color:{text}">{mname}</span><span style="font-family:Space Mono,monospace;font-size:0.82rem;color:{subtitle}">{msg}</span></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="card-title">📋 Full Prediction Table</div>', unsafe_allow_html=True)
    display_cols = ['Date','Opening_Stock','Total_Sold','Closing_Stock','Refill_Predicted','Confidence_%']
    st.dataframe(df[display_cols], use_container_width=True, height=350)
    st.markdown('</div>', unsafe_allow_html=True)

    csv = df[display_cols].to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Download Predictions CSV", csv, "refill_predictions.csv", "text/csv")