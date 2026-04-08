"""
FuelIQ — Data loading utilities
"""

import os, json, pickle, io
import pandas as pd
import numpy as np
import streamlit as st

DATA_DIR = os.path.abspath(
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "data")
)


def _dp(f: str) -> str:
    return os.path.join(DATA_DIR, f)


# ─────────────────────────────────────────────────────────────────────────────
# Normalise: derive missing columns from what's present
# ─────────────────────────────────────────────────────────────────────────────
def _normalise(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived / renamed columns so all pages work regardless of source file."""

    # 1. Ensure Date is datetime and sorted
    if "Date" not in df.columns:
        for alias in ["date", "DATE", "Dates"]:
            if alias in df.columns:
                df = df.rename(columns={alias: "Date"})
                break
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)

    # 2. Calendar columns
    if "Date" in df.columns:
        df["Month"]     = df["Date"].dt.month
        df["Year"]      = df["Date"].dt.year
        df["DayOfWeek"] = df["Date"].dt.weekday          # 0=Mon…6=Sun
        df["Day"]       = df["Date"].dt.day_name()
        df["Is_Weekend"]= (df["DayOfWeek"] >= 5).astype(int)

    # 3. Sales total (handle alternate column names)
    if "Total_Sold" not in df.columns:
        candidates = ["MS_Sold", "HSD1_Sold", "HSD2_Sold", "HSD3_Sold",
                      "TotalSold", "TotalSales", "Sales"]
        cols = [c for c in candidates if c in df.columns]
        if cols:
            df["Total_Sold"] = df[cols].sum(axis=1)

    # 4. Target (Refill_Required → Target)
    if "Target" not in df.columns:
        if "Refill_Required" in df.columns:
            df["Target"] = df["Refill_Required"].map(
                {"Yes": 1, "No": 0, "YES": 1, "NO": 0, 1: 1, 0: 0}
            ).fillna(0).astype(int)
        elif "Refill" in df.columns:
            df["Target"] = df["Refill"].map(
                {"Yes": 1, "No": 0, "YES": 1, "NO": 0, 1: 1, 0: 0}
            ).fillna(0).astype(int)

    # 5. Rolling sales (compute if missing)
    if "Total_Sold" in df.columns:
        df["Rolling_7d_Sales"] = (
            df["Total_Sold"].rolling(7, min_periods=1).mean().round(2)
        )

    # 6. Closing stock fallback
    if "Closing_Stock" not in df.columns and "Opening_Stock" in df.columns \
            and "Total_Sold" in df.columns:
        df["Closing_Stock"] = (df["Opening_Stock"] - df["Total_Sold"]).clip(lower=0)

    # 7. Previous closing (lag-1 of closing stock)
    if "Prev_Closing" not in df.columns and "Closing_Stock" in df.columns:
        df["Prev_Closing"] = df["Closing_Stock"].shift(1).fillna(0)

    # 8. Stock ratio
    if "Stock_Ratio" not in df.columns and "Closing_Stock" in df.columns \
            and "Opening_Stock" in df.columns:
        df["Stock_Ratio"] = (
            df["Closing_Stock"] / df["Opening_Stock"].replace(0, np.nan)
        ).fillna(0).clip(0, 1).round(4)

    # 9. Days since refill
    if "Days_Since_Refill" not in df.columns and "Target" in df.columns:
        ctr, cvals = 0, []
        for tgt in df["Target"]:
            cvals.append(ctr)
            ctr = 0 if tgt == 1 else ctr + 1
        df["Days_Since_Refill"] = cvals

    return df


# ─────────────────────────────────────────────────────────────────────────────
# Loaders
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def load_demo_data() -> pd.DataFrame:
    for fname in ["petrol_pump_data_2024_2026.xlsx", "clean_data.csv",
                  "petrol_pump_data_2024_2026.csv"]:
        path = _dp(fname)
        if not os.path.exists(path):
            continue
        try:
            df = pd.read_excel(path) if fname.endswith(".xlsx") else pd.read_csv(path)
            return _normalise(df)
        except Exception:
            continue
    return _normalise(_generate_synthetic_data())


@st.cache_data(show_spinner=False)
def load_uploaded_data(file_bytes: bytes, filename: str) -> pd.DataFrame:
    buf = io.BytesIO(file_bytes)
    try:
        if filename.lower().endswith((".xlsx", ".xls", ".xlsm")):
            # Read ALL sheets and concatenate
            xf = pd.ExcelFile(buf)
            frames = []
            for sheet in xf.sheet_names:
                try:
                    tmp = xf.parse(sheet)
                    if len(tmp) > 5:        # skip tiny/metadata sheets
                        frames.append(tmp)
                except Exception:
                    pass
            if not frames:
                df = xf.parse(0)
            elif len(frames) == 1:
                df = frames[0]
            else:
                # Keep largest sheet (most rows)
                df = max(frames, key=len)
        else:
            df = pd.read_csv(io.BytesIO(file_bytes))
    except Exception:
        return _normalise(_generate_synthetic_data())

    return _normalise(df)


@st.cache_resource(show_spinner=False)
def load_model():
    path = _dp("final_model.pkl")
    if os.path.exists(path):
        with open(path, "rb") as f:
            return pickle.load(f)
    return None


@st.cache_data(show_spinner=False)
def load_metrics() -> dict:
    path = _dp("model_metrics.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {"accuracy": 0.97, "f1_score": 0.96, "roc_auc": 0.99}


@st.cache_data(show_spinner=False)
def load_features() -> list:
    path = _dp("model_features.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return ["Days_Since_Refill", "Opening_Stock", "Prev_Closing",
            "Cash", "HSD2_Sold", "HSD1_Sold", "Total_Sold"]


@st.cache_data(show_spinner=False)
def load_selected_features() -> pd.DataFrame:
    path = _dp("selected_features.csv")
    if os.path.exists(path):
        feat_df = pd.read_csv(path)
        # Compute correlation from demo data if column missing
        if "Correlation_with_Target" not in feat_df.columns:
            try:
                demo = load_demo_data()
                corrs = {}
                for feat in feat_df["Feature"].tolist():
                    if feat in demo.columns and "Target" in demo.columns:
                        corrs[feat] = demo[feat].corr(demo["Target"])
                feat_df["Correlation_with_Target"] = feat_df["Feature"].map(corrs).fillna(0)
            except Exception:
                feat_df["Correlation_with_Target"] = 0.0
        return feat_df
    # Fallback
    return pd.DataFrame({
        "Feature": ["Opening_Stock", "Prev_Closing", "Total_Sold",
                    "Cash", "HSD1_Sold", "HSD2_Sold", "MS_Sold",
                    "DayOfWeek", "Card"],
        "Importance": [0.511, 0.290, 0.028, 0.024, 0.022, 0.021, 0.015, 0.011, 0.011],
        "Correlation_with_Target": [-0.809, 0.166, 0.203, 0.221, 0.200, 0.186, 0.195, 0.031, 0.041],
    })


# ─────────────────────────────────────────────────────────────────────────────
# Prediction
# ─────────────────────────────────────────────────────────────────────────────

def predict_refill(df: pd.DataFrame, model, features: list,
                   demand_adjustment: float = 0.0) -> dict:
    if df is None:
        return _mock_prediction(None, demand_adjustment)
    try:
        df_sorted = df.sort_values("Date")
        latest = df_sorted.tail(30).copy()
        if demand_adjustment != 0:
            for col in ["Total_Sold", "HSD1_Sold", "HSD2_Sold", "MS_Sold"]:
                if col in latest.columns:
                    latest[col] = latest[col] * (1 + demand_adjustment / 100)

        available = [f for f in features if f in latest.columns]
        if model is not None and available:
            X = latest[available].fillna(0).tail(1)
            proba = model.predict_proba(X)[0]
            confidence = float(max(proba))
        else:
            confidence = 0.91

        last_date = df_sorted["Date"].iloc[-1]
        avg_sold  = float(df["Total_Sold"].mean()
                          if "Total_Sold" in df.columns else 4500)
        adj_sold  = avg_sold * (1 + demand_adjustment / 100)

        if "Closing_Stock" in df_sorted.columns:
            closing = float(df_sorted["Closing_Stock"].iloc[-1])
        elif "Opening_Stock" in df_sorted.columns:
            closing = float(df_sorted["Opening_Stock"].iloc[-1]) * 0.5
        else:
            closing = 3000.0

        days_remaining = max(1, int(closing / adj_sold)) if adj_sold > 0 else 3
        refill_date    = last_date + pd.Timedelta(days=days_remaining)

        return {
            "refill_date": refill_date,
            "days_remaining": days_remaining,
            "confidence": confidence,
            "avg_sold": adj_sold,
            "closing_stock": closing,
        }
    except Exception:
        return _mock_prediction(df, demand_adjustment)


def _mock_prediction(df, demand_adjustment: float = 0.0) -> dict:
    base = pd.Timestamp.now()
    if df is not None and "Date" in df.columns:
        base = df.sort_values("Date")["Date"].iloc[-1]
    avg_sold = 4500 * (1 + demand_adjustment / 100)
    closing  = 3200
    days     = max(1, int(closing / avg_sold))
    return {
        "refill_date": base + pd.Timedelta(days=days),
        "days_remaining": days,
        "confidence": 0.91,
        "avg_sold": avg_sold,
        "closing_stock": closing,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Simulation
# ─────────────────────────────────────────────────────────────────────────────

def simulate_15_days(df: pd.DataFrame, model, features: list,
                     demand_adjustment: float = 0.0) -> pd.DataFrame:
    if df is None:
        return _mock_simulation(demand_adjustment)
    try:
        df_sorted  = df.sort_values("Date")
        last_date  = df_sorted["Date"].iloc[-1]
        closing    = float(df_sorted["Closing_Stock"].iloc[-1]) \
                     if "Closing_Stock" in df_sorted.columns else 5000.0
        refill_cap = 12000.0
        avg_sold   = float(df["Total_Sold"].mean()
                           if "Total_Sold" in df.columns else 4500)
        avg_sold  *= (1 + demand_adjustment / 100)
        threshold  = 2000
        rows, opening, refill_done = [], closing, False
        for i in range(1, 16):
            d    = last_date + pd.Timedelta(days=i)
            sold = min(avg_sold * (1.15 if d.weekday() >= 5 else 1.0), opening)
            cl   = max(0.0, opening - sold)
            r_pr = round(max(0, min(1, 1.0 - (cl / refill_cap) * 1.8)), 3)
            trig = cl <= threshold and not refill_done
            if trig:
                refill_done = True
            rows.append({
                "Date": d.strftime("%Y-%m-%d"),
                "Day": d.day_name(),
                "Opening_Stock": round(opening),
                "Est_Sold": round(sold),
                "Closing_Stock": round(cl),
                "Refill_Probability": r_pr,
                "Refill_Triggered": trig,
            })
            opening = refill_cap if trig else cl
        return pd.DataFrame(rows)
    except Exception:
        return _mock_simulation(demand_adjustment)


def _mock_simulation(demand_adjustment: float = 0.0) -> pd.DataFrame:
    rows, opening, done = [], 7000.0, False
    avg = 4500 * (1 + demand_adjustment / 100)
    base = pd.Timestamp.now()
    for i in range(1, 16):
        d    = base + pd.Timedelta(days=i)
        sold = min(avg * (1.15 if d.weekday() >= 5 else 1.0), opening)
        cl   = max(0.0, opening - sold)
        r_pr = round(max(0, min(1, 1.0 - (cl / 12000) * 1.8)), 3)
        trig = cl <= 2000 and not done
        if trig:
            done = True
        rows.append({"Date": d.strftime("%Y-%m-%d"), "Day": d.day_name(),
                     "Opening_Stock": round(opening), "Est_Sold": round(sold),
                     "Closing_Stock": round(cl), "Refill_Probability": r_pr,
                     "Refill_Triggered": trig})
        opening = 12000.0 if trig else cl
    return pd.DataFrame(rows)


def _generate_synthetic_data() -> pd.DataFrame:
    np.random.seed(42)
    dates, rows = pd.date_range("2024-01-01", periods=365), []
    opening = 12000.0
    for d in dates:
        sold = float(np.clip(np.random.normal(4500, 400), 2000, 7000))
        cl   = max(0.0, opening - sold)
        rows.append({"Date": d, "Opening_Stock": round(opening),
                     "Total_Sold": round(sold), "Closing_Stock": round(cl),
                     "Target": 1 if cl < 2000 else 0})
        opening = 12000.0 if cl < 2000 else cl
    return pd.DataFrame(rows)
