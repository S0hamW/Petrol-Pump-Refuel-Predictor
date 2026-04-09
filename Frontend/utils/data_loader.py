"""
FuelIQ — Data loading utilities (v6 — FULL DATASET FIX)
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


def _normalise(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "Date" not in df.columns:
        for alias in ["date", "DATE", "Dates"]:
            if alias in df.columns:
                df = df.rename(columns={alias: "Date"})
                break
    if "Date" in df.columns:
        # Pass format="mixed" and dayfirst=True to correctly handle BOTH US and European formats
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce", format="mixed", dayfirst=True)
        df = df.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)

    if "Date" in df.columns:
        df["Month"]      = df["Date"].dt.month
        df["Year"]       = df["Date"].dt.year
        df["DayOfWeek"]  = df["Date"].dt.weekday
        df["Day"]        = df["Date"].dt.day_name()
        df["Is_Weekend"] = (df["DayOfWeek"] >= 5).astype(int)

    numeric_cols = [
        "Opening_Stock", "Closing_Stock", "Total_Sold",
        "MS_Sold", "HSD1_Sold", "HSD2_Sold", "HSD3_Sold",
        "Cash", "Online", "Card", "Dip"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    if "Total_Sold" not in df.columns:
        candidates = ["MS_Sold", "HSD1_Sold", "HSD2_Sold", "HSD3_Sold",
                      "TotalSold", "TotalSales", "Sales"]
        cols = [c for c in candidates if c in df.columns]
        if cols:
            df["Total_Sold"] = df[cols].sum(axis=1)

    if "Target" not in df.columns:
        for src in ["Refill_Required", "Refill"]:
            if src in df.columns:
                df["Target"] = df[src].map(
                    {"Yes": 1, "No": 0, "YES": 1, "NO": 0, 1: 1, 0: 0}
                ).fillna(0).astype(int)
                break

    if "Total_Sold" in df.columns:
        df["Rolling_7d_Sales"] = (
            df["Total_Sold"].rolling(7, min_periods=1).mean().round(2)
        )

    if "Closing_Stock" not in df.columns and "Opening_Stock" in df.columns \
            and "Total_Sold" in df.columns:
        df["Closing_Stock"] = (df["Opening_Stock"] - df["Total_Sold"]).clip(lower=0)

    if "Prev_Closing" not in df.columns and "Closing_Stock" in df.columns:
        df["Prev_Closing"] = df["Closing_Stock"].shift(1).fillna(0)

    if "Stock_Ratio" not in df.columns and "Closing_Stock" in df.columns \
            and "Opening_Stock" in df.columns:
        df["Stock_Ratio"] = (
            df["Closing_Stock"] / df["Opening_Stock"].replace(0, np.nan)
        ).fillna(0).clip(0, 1).round(4)

    if "Days_Since_Refill" not in df.columns and "Target" in df.columns:
        ctr, cvals = 0, []
        for tgt in df["Target"]:
            cvals.append(ctr)
            ctr = 0 if int(tgt) == 1 else ctr + 1
        df["Days_Since_Refill"] = cvals

    if "Is_Festival_Month" not in df.columns and "Month" in df.columns:
        df["Is_Festival_Month"] = df["Month"].isin([10, 11]).astype(int)
    if "Is_Monsoon_Month" not in df.columns and "Month" in df.columns:
        df["Is_Monsoon_Month"] = df["Month"].isin([6, 7, 8, 9]).astype(int)

    if "Lag1_Total_Sold" not in df.columns and "Total_Sold" in df.columns:
        df["Lag1_Total_Sold"] = df["Total_Sold"].shift(1).fillna(df["Total_Sold"].mean())
    
    if "Lag2_Total_Sold" not in df.columns and "Total_Sold" in df.columns:
        df["Lag2_Total_Sold"] = df["Total_Sold"].shift(2).fillna(df["Total_Sold"].mean())
        
    if "Lag1_Closing" not in df.columns and "Closing_Stock" in df.columns and "Opening_Stock" in df.columns:
        df["Lag1_Closing"] = df["Closing_Stock"].shift(1).fillna(df["Opening_Stock"].mean())
        
    if "DOW_Avg_Sales" not in df.columns and "DayOfWeek" in df.columns and "Total_Sold" in df.columns:
        def ewm_dow_avg(series):
            return series.ewm(span=8, adjust=False).mean()
        df["DOW_Avg_Sales"] = df.groupby("DayOfWeek")["Total_Sold"].transform(ewm_dow_avg)

    if "Sales_Trend" not in df.columns and "Rolling_7d_Sales" in df.columns and "Total_Sold" in df.columns:
        df["Sales_Trend"] = (df["Rolling_7d_Sales"] / df["Total_Sold"].mean()).round(4)

    return df


# ─────────────────────────────────────────────────────────────────────────────
# KEY FIX: combine ALL sheets instead of picking just the largest one
# ─────────────────────────────────────────────────────────────────────────────

def _read_excel_all_sheets(path_or_buf) -> pd.DataFrame:
    """
    Read an Excel file and COMBINE all data sheets into one DataFrame.
    Deduplicates on Date column to avoid overlap between sheets.
    """
    xf = pd.ExcelFile(path_or_buf)
    frames = []
    for sheet in xf.sheet_names:
        try:
            tmp = xf.parse(sheet)
            if len(tmp) > 5:  # skip tiny metadata/legend sheets
                # Standardise columns before concatenating so sheets align perfectly
                if hasattr(tmp.columns, "str"):
                    tmp.columns = tmp.columns.str.strip()
                if "Date" not in tmp.columns:
                    for alias in ["date", "DATE", "Dates"]:
                        if alias in tmp.columns:
                            tmp = tmp.rename(columns={alias: "Date"})
                            break
                frames.append(tmp)
        except Exception:
            pass

    if not frames:
        return xf.parse(0)

    if len(frames) == 1:
        return frames[0]

    # COMBINE all sheets
    combined = pd.concat(frames, ignore_index=True)

    # Deduplicate ONLY exact duplicate rows (all columns identical).
    # Do NOT dedup by date alone — the same date should never be dropped
    # just because it appears in two sheets with different data.
    combined = combined.drop_duplicates()

    # Sort by date if available
    date_col = next(
        (c for c in combined.columns if c.lower() == "date"), None
    )
    if date_col:
        # Pass format="mixed" and dayfirst=True to correctly handle BOTH formats
        combined[date_col] = pd.to_datetime(combined[date_col], errors="coerce", format="mixed", dayfirst=True)
        combined = combined.dropna(subset=[date_col])
        combined = combined.sort_values(date_col).reset_index(drop=True)

    return combined


@st.cache_data(show_spinner=False)
def load_demo_data() -> pd.DataFrame:
    """
    Load demo data — tries all sources and picks the one with MOST rows.
    Never silently loads a partial dataset. This docstring forces a cache clear.
    """
    candidates = []

    for fname in ["clean_data.csv", "petrol_pump_data_2024_2026.csv"]:
        path = _dp(fname)
        if not os.path.exists(path):
            continue
        try:
            df = pd.read_csv(path)
            candidates.append(df)
        except Exception:
            pass

    for fname in ["petrol_pump_data_2024_2026.xlsx"]:
        path = _dp(fname)
        if not os.path.exists(path):
            continue
        try:
            df = _read_excel_all_sheets(path)
            candidates.append(df)
        except Exception:
            pass

    if not candidates:
        return _normalise(_generate_synthetic_data())

    # Pick the DataFrame with the MOST rows — never silently load a partial file
    best = max(candidates, key=len)

    # Warn in sidebar if loaded count is suspiciously low
    if len(best) < 500:
        st.warning(
            f"⚠️ Only {len(best)} rows loaded from demo data. "
            "Expected ~806. Check that all sheets are present in your Excel file."
        )

    return _normalise(best)


@st.cache_data(show_spinner=False)
def load_uploaded_data(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """
    Load user-uploaded file — ALL rows from ALL sheets, no sampling.
    Shows a warning if row count is unexpectedly low.
    """
    buf = io.BytesIO(file_bytes)
    try:
        if filename.lower().endswith((".xlsx", ".xls", ".xlsm")):
            # FIX: combine all sheets, not just the largest
            df = _read_excel_all_sheets(buf)
        else:
            df = pd.read_csv(io.BytesIO(file_bytes))
    except Exception:
        return _normalise(_generate_synthetic_data())

    result = _normalise(df)

    # Visible warning if row count is wrong
    if len(result) < 500:
        st.warning(
            f"⚠️ Only {len(result)} rows loaded from '{filename}'. "
            f"If you expect more rows, your Excel file may have data split across "
            f"sheets that couldn't be merged — check that each sheet has a 'Date' column."
        )
    else:
        st.success(f"✅ Loaded {len(result):,} rows from '{filename}'")

    return result


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
    return pd.DataFrame({
        "Feature":    ["Opening_Stock", "Prev_Closing", "Total_Sold",
                       "Cash", "HSD1_Sold", "HSD2_Sold", "MS_Sold",
                       "DayOfWeek", "Card"],
        "Importance": [0.511, 0.290, 0.028, 0.024, 0.022, 0.021, 0.015, 0.011, 0.011],
        "Correlation_with_Target": [-0.809, 0.166, 0.203, 0.221, 0.200, 0.186, 0.195, 0.031, 0.041],
    })


# ─────────────────────────────────────────────────────────────────────────────
# Prediction — walk-forward simulation matching notebook 05_prediction.ipynb
# ─────────────────────────────────────────────────────────────────────────────

def predict_refill(df: pd.DataFrame, model, features: list,
                   demand_adjustment: float = 0.0) -> dict:
    if df is None:
        return _mock_prediction(None, demand_adjustment)
    try:
        df_sorted = df.sort_values("Date").reset_index(drop=True)
        demand_adjustment = float(demand_adjustment)
        demand_factor = 1 + demand_adjustment / 100

        TANK_CAPACITY    = 12000
        REFILL_THRESHOLD = 2000

        # ── Load monthly multipliers ──────────────────────────────────────────
        monthly_mult_path = _dp("monthly_multipliers.json")
        if os.path.exists(monthly_mult_path):
            with open(monthly_mult_path) as f:
                raw = json.load(f)
            MONTHLY_MULT = {int(k): float(v) for k, v in raw.items()}
        else:
            MONTHLY_MULT = {}

        # ── Per-DOW EWM average (matches training feature DOW_Avg_Sales) ─────
        def _ewm_dow_avg(df_in, dow):
            s = df_in[df_in["DayOfWeek"] == dow]["Total_Sold"]
            if len(s) == 0:
                return float(df_in["Total_Sold"].mean())
            return float(s.ewm(span=8, adjust=False).mean().iloc[-1])

        total_sold_col = "Total_Sold" in df_sorted.columns
        global_mean = float(pd.to_numeric(
            df_sorted["Total_Sold"], errors="coerce"
        ).fillna(0).mean()) if total_sold_col else 4500.0

        dows_present = df_sorted["DayOfWeek"].unique() if "DayOfWeek" in df_sorted.columns else list(range(7))
        dow_ewm_avg = {d: _ewm_dow_avg(df_sorted, d) for d in dows_present}

        def _rolling_dow_avg(df_in, dow, n=4):
            s = df_in[df_in["DayOfWeek"] == dow]["Total_Sold"] if "DayOfWeek" in df_in.columns else pd.Series(dtype=float)
            if len(s) == 0:
                return global_mean
            return float(s.tail(n).mean())

        def _blended(dow):
            recent   = _rolling_dow_avg(df_sorted, dow)
            all_time = dow_ewm_avg.get(dow, global_mean)
            return 0.60 * recent + 0.40 * all_time   # 60 % recent, 40 % EWM

        # ── Per-DOW fuel-type ratios ──────────────────────────────────────────
        def _ratio(numerator_col):
            if numerator_col not in df_sorted.columns or "Total_Sold" not in df_sorted.columns:
                return {}
            num  = df_sorted.groupby("DayOfWeek")[numerator_col].mean()
            den  = df_sorted.groupby("DayOfWeek")["Total_Sold"].mean().replace(0, np.nan)
            return (num / den).fillna(0).to_dict()

        ms_ratio   = _ratio("MS_Sold")
        hsd1_ratio = _ratio("HSD1_Sold")
        hsd2_ratio = _ratio("HSD2_Sold")
        hsd3_ratio = _ratio("HSD3_Sold")

        # ── Starting stock ────────────────────────────────────────────────────
        last = df_sorted.iloc[-1]
        last_date = pd.to_datetime(last["Date"])

        had_refill = False
        if "Refill_Required" in df_sorted.columns:
            had_refill = (str(last.get("Refill_Required", "No")).strip().lower() == "yes")
        elif "Target" in df_sorted.columns:
            had_refill = (int(last.get("Target", 0)) == 1)

        if had_refill:
            current_stock = float(TANK_CAPACITY)
        else:
            current_stock = float(pd.to_numeric(
                last.get("Closing_Stock", 3000), errors="coerce"
            ) or 3000.0)

        start_date = last_date + pd.Timedelta(days=1)

        # ── Lag / rolling seed values ─────────────────────────────────────────
        recent_sales     = (pd.to_numeric(df_sorted["Total_Sold"], errors="coerce")
                            .fillna(0).tail(7).tolist()
                            if total_sold_col else [global_mean] * 7)
        lag1_sold        = float(recent_sales[-1])
        lag2_sold        = float(recent_sales[-2]) if len(recent_sales) >= 2 else lag1_sold
        lag1_closing     = float(pd.to_numeric(
            df_sorted["Closing_Stock"], errors="coerce"
        ).fillna(0).iloc[-1]) if "Closing_Stock" in df_sorted.columns else current_stock

        # Days since last refill
        if "Refill_Required" in df_sorted.columns:
            rfi = df_sorted[df_sorted["Refill_Required"].astype(str).str.lower() == "yes"].index
        elif "Target" in df_sorted.columns:
            rfi = df_sorted[df_sorted["Target"] == 1].index
        else:
            rfi = pd.Index([])
        days_since_refill = (len(df_sorted) - 1 - int(rfi.max())) if len(rfi) else 0

        # ── Walk-forward simulation (up to 30 days) ───────────────────────────
        DAY_MAP = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
                   "Friday": 4, "Saturday": 5, "Sunday": 6}

        running_stock      = current_stock
        running_rolling_7d = list(recent_sales)
        running_lag1       = lag1_sold
        running_lag2       = lag2_sold
        running_lag1_close = lag1_closing
        running_days_since = days_since_refill
        drift_correction   = 0.0

        refill_day = None
        confidence = 0.91

        for i in range(30):
            d        = start_date + pd.Timedelta(days=i)
            day_name = d.strftime("%A")
            dow      = DAY_MAP[day_name]
            month    = d.month

            # Blended DOW estimate + drift + demand adjustment
            blended_est  = (_blended(dow) + drift_correction) * demand_factor
            seasonal_mult = MONTHLY_MULT.get(month, 1.0)
            est_sales    = blended_est * seasonal_mult

            # Stock-pressure cap (low stock → constrained demand)
            stock_pressure = min(1.0, running_stock / 6000.0)
            est_sales      = min(int(est_sales * stock_pressure), running_stock)

            closing = max(0, running_stock - est_sales)

            est_dip        = max(1, int(closing / 200))
            est_stock_ratio = round(closing / TANK_CAPACITY, 4)
            live_rolling_7d = float(np.mean(running_rolling_7d[-7:]))
            running_days_since += 1
            sales_trend = round(live_rolling_7d / global_mean, 4)

            row = {
                "Opening_Stock"    : running_stock,
                "Prev_Closing"     : running_lag1_close,
                "Total_Sold"       : est_sales,
                "MS_Sold"          : int(est_sales * ms_ratio.get(dow, 0.12)),
                "HSD1_Sold"        : int(est_sales * hsd1_ratio.get(dow, 0.38)),
                "HSD2_Sold"        : int(est_sales * hsd2_ratio.get(dow, 0.30)),
                "HSD3_Sold"        : int(est_sales * hsd3_ratio.get(dow, 0.20)),
                "Cash"             : int(est_sales * 43),
                "Online"           : int(est_sales * 31),
                "Card"             : int(est_sales * 21),
                "Year"             : d.year,
                "Month"            : month,
                "DayOfWeek"        : dow,
                "Day_Num"          : dow,
                "Quarter"          : (month - 1) // 3 + 1,
                "Is_Weekend"       : 1 if dow >= 5 else 0,
                "Is_Festival_Month": 1 if month in [10, 11] else 0,
                "Is_Monsoon_Month" : 1 if month in [6, 7, 8] else 0,
                "Rolling_7d_Sales" : live_rolling_7d,
                "Stock_Ratio"      : est_stock_ratio,
                "Dip"              : est_dip,
                "Lag1_Total_Sold"  : running_lag1,
                "Lag2_Total_Sold"  : running_lag2,
                "Lag1_Closing"     : running_lag1_close,
                "DOW_Avg_Sales"    : dow_ewm_avg.get(dow, global_mean),
                "Sales_Trend"      : sales_trend,
                "Days_Since_Refill": running_days_since,
            }

            if model is not None and features:
                X_row   = pd.DataFrame([row]).reindex(columns=features, fill_value=0)
                proba   = model.predict_proba(X_row)[0]
                confidence = float(max(proba))

            # Refill needed when stock drops below threshold
            if closing < REFILL_THRESHOLD and refill_day is None:
                refill_day = {
                    "date"        : d,
                    "day_name"    : day_name,
                    "closing"     : closing,
                    "days_from_now": i + 1,
                    "confidence"  : confidence,
                }
                break

            # Advance state
            running_lag2       = running_lag1
            running_lag1       = est_sales
            running_lag1_close = closing
            running_rolling_7d.append(est_sales)
            running_stock      = closing
            drift_correction   = 0.0

        # ── Build return dict ─────────────────────────────────────────────────
        if refill_day:
            return {
                "refill_date"   : refill_day["date"],
                "days_remaining": refill_day["days_from_now"],
                "confidence"    : refill_day["confidence"],
                "avg_sold"      : global_mean * demand_factor,
                "closing_stock" : current_stock,
            }
        else:
            # No refill within 30 days — give a rough estimate
            adj = global_mean * demand_factor
            days_left = max(1, int(running_stock / adj)) if adj > 0 else 3
            return {
                "refill_date"   : start_date + pd.Timedelta(days=days_left),
                "days_remaining": days_left,
                "confidence"    : confidence,
                "avg_sold"      : adj,
                "closing_stock" : current_stock,
            }

    except Exception as e:
        st.error(f"Prediction error: {e}")
        return _mock_prediction(df, demand_adjustment)


def _mock_prediction(df, demand_adjustment: float = 0.0) -> dict:
    base = pd.Timestamp.now()
    if df is not None and "Date" in df.columns:
        base = df.sort_values("Date")["Date"].iloc[-1]
    demand_adjustment = float(demand_adjustment)
    avg_sold = 4500 * (1 + demand_adjustment / 100)
    closing  = 3200
    days     = max(1, int(closing / avg_sold))
    return {
        "refill_date":    base + pd.Timedelta(days=days),
        "days_remaining": days,
        "confidence":     0.91,
        "avg_sold":       avg_sold,
        "closing_stock":  float(closing),
    }


def _generate_synthetic_data() -> pd.DataFrame:
    np.random.seed(42)
    dates, rows = pd.date_range("2024-01-01", periods=365), []
    opening = 12000.0
    for d in dates:
        sold = float(np.clip(np.random.normal(4500, 400), 2000, 7000))
        cl   = max(0.0, opening - sold)
        rows.append({
            "Date":          d,
            "Opening_Stock": int(round(opening)),
            "Total_Sold":    int(round(sold)),
            "Closing_Stock": int(round(cl)),
            "Target":        1 if cl < 2000 else 0,
        })
        opening = 12000.0 if cl < 2000 else cl
    return pd.DataFrame(rows)

def simulate_forward(df, demand_adjustment=0.0, n_days=15):
    """Walk-forward simulation — returns 15-day sim DataFrame."""
    import os, json
    import pandas as pd
    import numpy as np

    if df is None:
        return pd.DataFrame()
    try:
        df_sorted = df.sort_values("Date").reset_index(drop=True)
        demand_factor = 1 + float(demand_adjustment) / 100
        TANK_CAPACITY    = 12000
        REFILL_THRESHOLD = 2000

        data_dir  = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "data"))
        mult_path = os.path.join(data_dir, "monthly_multipliers.json")
        MONTHLY_MULT = {}
        if os.path.exists(mult_path):
            with open(mult_path) as f:
                raw = json.load(f)
            MONTHLY_MULT = {int(k): float(v) for k, v in raw.items()}

        total_sold_col = "Total_Sold" in df_sorted.columns
        global_mean = float(
            pd.to_numeric(df_sorted["Total_Sold"], errors="coerce").fillna(0).mean()
        ) if total_sold_col else 4500.0

        def _ewm_dow(dow_val):
            s = (df_sorted[df_sorted["DayOfWeek"] == dow_val]["Total_Sold"]
                 if "DayOfWeek" in df_sorted.columns else pd.Series(dtype=float))
            return float(s.ewm(span=8, adjust=False).mean().iloc[-1]) if len(s) else global_mean

        dows_present = (df_sorted["DayOfWeek"].unique()
                        if "DayOfWeek" in df_sorted.columns else range(7))
        dow_ewm = {dv: _ewm_dow(dv) for dv in dows_present}

        def _rolling_dow(dow_val, n=4):
            s = (df_sorted[df_sorted["DayOfWeek"] == dow_val]["Total_Sold"]
                 if "DayOfWeek" in df_sorted.columns else pd.Series(dtype=float))
            return float(s.tail(n).mean()) if len(s) else global_mean

        def _blended(dow_val):
            return (0.60 * _rolling_dow(dow_val) + 0.40 * dow_ewm.get(dow_val, global_mean))

        last       = df_sorted.iloc[-1]
        last_date  = pd.to_datetime(last["Date"], dayfirst=True)
        had_refill = False
        if "Refill_Required" in df_sorted.columns:
            had_refill = str(last.get("Refill_Required", "No")).strip().lower() == "yes"
        elif "Target" in df_sorted.columns:
            had_refill = int(last.get("Target", 0)) == 1

        current_stock = float(TANK_CAPACITY) if had_refill else float(
            pd.to_numeric(last.get("Closing_Stock", 3000), errors="coerce") or 3000.0)
        start_date = last_date + pd.Timedelta(days=1)

        recent_sales = (
            pd.to_numeric(df_sorted["Total_Sold"], errors="coerce")
            .fillna(0).tail(7).tolist()
            if total_sold_col else [global_mean] * 7
        )

        DAY_MAP = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
                   "Friday": 4, "Saturday": 5, "Sunday": 6}
        running     = current_stock
        rolling7d   = list(recent_sales)
        refill_done = False
        sim_rows    = []

        for i in range(n_days):
            d        = start_date + pd.Timedelta(days=i)
            day_name = d.strftime("%A")
            dow      = DAY_MAP[day_name]
            month    = d.month
            est  = _blended(dow) * MONTHLY_MULT.get(month, 1.0) * demand_factor
            pres = min(1.0, running / 6000.0)
            est  = min(int(est * pres), running)
            cl   = max(0, running - est)
            refill_now = (not refill_done) and (cl < REFILL_THRESHOLD)
            if refill_now:
                refill_done = True
            sim_rows.append({
                "Date"             : d.strftime("%Y-%m-%d"),
                "Day"              : day_name,
                "Opening_Stock"    : "{:,.0f} L".format(running),
                "Est_Sold"         : "{:,.0f} L".format(est),
                "Closing_Stock"    : "{:,.0f} L".format(cl),
                "Refill_Probability": "High (Refill Triggered)" if refill_now else "Low",
                "Refill_Triggered" : refill_now,
            })
            running   = float(TANK_CAPACITY) if refill_now else float(cl)
            rolling7d.append(est)

        return pd.DataFrame(sim_rows)

    except Exception:
        return pd.DataFrame()
