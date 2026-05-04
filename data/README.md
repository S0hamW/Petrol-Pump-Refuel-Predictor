# 📁 data/ — Datasets, Model Artifacts & Configuration

This directory is the **central data store** for the PetroPredict Business Analytics platform. It holds everything the ML pipeline and Streamlit dashboard need to operate: raw historical spreadsheets, cleaned datasets, engineered feature manifests, a trained model binary, pre-computed performance metrics, seasonal configuration, and pre-rendered visualisation images.

---

## 📂 Directory Contents

```
data/
├── petrol_pump_2011_2025.xlsx          ← Primary raw dataset (tracked in git)
├── petrol_pump_data_2024_2026.xlsx     ← Recent supplementary dataset
├── clean_data.csv                      ← Pre-processed feature-rich dataset (git-ignored)
├── selected_features.csv               ← Feature importance table (tracked in git)
├── model_features.json                 ← Ordered 19-feature list for inference (tracked)
├── model_metrics.json                  ← Model evaluation scores (tracked)
├── monthly_multipliers.json            ← Seasonal demand scaling factors (tracked)
├── final_model.pkl                     ← Serialised Random Forest Classifier (git-ignored)
│
└── [Generated Visualisation Images]
    ├── viz_01_class_distribution.png   ← Refill vs No-Refill class balance
    ├── viz_02_sales_by_day.png         ← Average daily sales by day of week
    ├── viz_03_seasonal_pattern.png     ← Monthly average sales pattern
    ├── viz_04_yearly_growth.png        ← Year-over-year sales growth
    ├── viz_05_opening_stock.png        ← Opening stock trend over time
    ├── viz_06_refill_heatmap.png       ← Refill event heatmap (month × day)
    ├── viz_07_sales_distribution.png   ← Distribution of daily total sales
    ├── viz_confusion_matrix.png        ← Model confusion matrix (test set)
    ├── viz_next_refill_prediction.png  ← Next refill date prediction plot
    ├── viz_roc_curve.png               ← ROC curve for classifier
    ├── correlation_plot.png            ← Feature–target correlation chart
    ├── feature_importance_plot.png     ← Bar chart of feature importances
    └── heatmap.png                     ← Feature correlation heatmap
```

---

## 📊 Raw Data Files

### `petrol_pump_2011_2025.xlsx` _(Tracked in git)_
- **Description**: The primary historical dataset spanning **14+ years** (2011–2025) of daily petrol pump operations.
- **Format**: Multi-sheet Excel workbook — each sheet typically represents one year or operational period.
- **Loading Strategy**: The `data_loader.py` utility combines **all sheets** using `pd.concat`, deduplicates on exact-match rows, and sorts chronologically. This prevents partial-load bugs where only the largest sheet is read.
- **Key Columns** (after normalisation):

| Column | Type | Description |
|---|---|---|
| `Date` | datetime | Date of operation (auto-parsed, day-first) |
| `Opening_Stock` | float | Fuel stock at the start of the day (litres) |
| `Closing_Stock` | float | Fuel stock at end of day (litres) |
| `Total_Sold` | float | Total fuel sold that day (litres) |
| `MS_Sold` | float | Motor Spirit (petrol) quantity sold |
| `HSD1_Sold` | float | High Speed Diesel grade 1 sold |
| `HSD2_Sold` | float | High Speed Diesel grade 2 sold |
| `HSD3_Sold` | float | High Speed Diesel grade 3 sold |
| `Cash` | float | Revenue collected via cash (₹) |
| `Online` | float | Revenue collected via UPI/online (₹) |
| `Card` | float | Revenue collected via card (₹) |
| `Dip` | float | Physical tank dip measurement |
| `Refill_Required` | str | "Yes" / "No" — whether a refill occurred |

### `petrol_pump_data_2024_2026.xlsx` _(Git-ignored by default)_
- **Description**: Supplementary dataset for recent operations (2024–2026). Used as an alternate demo data source.
- **Loading**: Same multi-sheet strategy as the primary file. `load_demo_data()` picks whichever source has the most rows.

---

## ⚙️ Processed / Engineered Data

### `clean_data.csv` _(Git-ignored — generate locally)_
- **Description**: The fully normalised and feature-engineered dataset produced by `01_data_preparation.ipynb` and `02_feature_selection.ipynb`.
- **Contents**: All raw columns plus the 19 engineered features listed below.
- **Regenerate**: Run notebooks `01` and `02` in order, or let `data_loader.py` generate it on first load.
- **Size**: ~97 KB for a typical 800+ row dataset.

#### All Engineered Columns Added by `_normalise()`

| Feature | Formula / Logic | Business Meaning |
|---|---|---|
| `Month` | `Date.dt.month` | Calendar month (1–12) |
| `Year` | `Date.dt.year` | Calendar year |
| `DayOfWeek` | `Date.dt.weekday` (0=Mon) | Weekday index |
| `Day` | `Date.dt.day_name()` | Day name string |
| `Is_Weekend` | `DayOfWeek >= 5` | Weekend flag |
| `Rolling_7d_Sales` | 7-day rolling mean of `Total_Sold` | Short-term demand trend |
| `Closing_Stock` | `Opening_Stock − Total_Sold` | Derived if not in raw data |
| `Prev_Closing` | `Closing_Stock.shift(1)` | Yesterday's closing stock |
| `Stock_Ratio` | `Closing_Stock / Opening_Stock` | Stock depletion ratio (0–1) |
| `Days_Since_Refill` | Counter reset on each `Target=1` day | Days elapsed since last refill |
| `Is_Festival_Month` | `Month ∈ {10, 11}` | Diwali/Navratri demand spike |
| `Is_Monsoon_Month` | `Month ∈ {6, 7, 8, 9}` | Monsoon demand dip |
| `Lag1_Total_Sold` | `Total_Sold.shift(1)` | Yesterday's sales |
| `Lag2_Total_Sold` | `Total_Sold.shift(2)` | Two days ago sales |
| `Lag1_Closing` | `Closing_Stock.shift(1)` | Yesterday's closing stock |
| `DOW_Avg_Sales` | EWM (span=8) per day-of-week | Day-of-week seasonal average |
| `Sales_Trend` | `Rolling_7d_Sales / global_mean` | Momentum indicator |
| `Target` | Mapped from `Refill_Required` | Binary label (1=Refill, 0=No refill) |

### `selected_features.csv` _(Tracked in git)_
- **Description**: The 11 most important features ranked by their Random Forest importance scores.
- **Columns**: `Feature`, `Importance`
- **Usage**: Loaded by `Feature Engineering` dashboard page to render the importance chart and table.

```
Feature            | Importance
-------------------|----------
Opening_Stock      | 0.5112  ← Dominant predictor (51%)
Prev_Closing       | 0.2900  ← Second strongest (29%)
Total_Sold         | 0.0284
Cash               | 0.0240
HSD1_Sold          | 0.0224
HSD2_Sold          | 0.0208
Online             | 0.0183
HSD3_Sold          | 0.0177
MS_Sold            | 0.0150
DayOfWeek          | 0.0111
Card               | 0.0110
```

---

## 🤖 Model Artifacts

### `final_model.pkl` _(Git-ignored — generate locally)_
- **Description**: The serialised trained `RandomForestClassifier` (scikit-learn ≥ 1.3).
- **Training**: Produced by `04_model_training.ipynb` using an 80/20 stratified train-test split.
- **Hyperparameters**: `n_estimators=200`, `max_depth=12`, `min_samples_leaf=3`
- **Loading**: `load_model()` in `data_loader.py` uses `pickle.load()` with `@st.cache_resource` for one-time loading.
- **Regenerate**: Run `04_model_training.ipynb` end-to-end. The model will be saved to this directory automatically.

### `model_features.json` _(Tracked in git)_
- **Description**: The exact ordered list of **19 feature column names** the model was trained on. This is the contract between training and inference — the order matters.
- **Used By**: `predict_refill()` in `data_loader.py` to construct the inference row with `df.reindex(columns=features)`.

```json
["Opening_Stock", "Prev_Closing", "Total_Sold", "Cash", "HSD1_Sold",
 "HSD2_Sold", "Online", "HSD3_Sold", "MS_Sold", "DayOfWeek", "Card",
 "Stock_Ratio", "Dip", "Lag1_Total_Sold", "Lag2_Total_Sold",
 "Lag1_Closing", "DOW_Avg_Sales", "Sales_Trend", "Days_Since_Refill"]
```

### `model_metrics.json` _(Tracked in git)_
- **Description**: Validation performance scores computed at test time.
- **Displayed On**: Model Insights dashboard page.

```json
{
  "accuracy": 1.0,
  "f1_score": 1.0,
  "roc_auc":  1.0
}
```

> **Note**: A perfect score of 1.0 reflects a highly structured operational dataset where stock-level signals (Opening_Stock, Prev_Closing) are near-deterministic predictors of refill events. Real-world deployment should validate on unseen future data.

---

## 📅 Configuration Files

### `monthly_multipliers.json` _(Tracked in git)_
- **Description**: Month-level demand scaling factors derived from historical average sales per month vs. the overall annual mean.
- **Used By**: `predict_refill()` and `simulate_forward()` in `data_loader.py` to adjust estimated daily sales for seasonal effects during walk-forward simulation.

```json
{
  "1":  0.9839,   "2":  0.9874,   "3":  1.0621,
  "4":  1.0629,   "5":  1.0037,   "6":  0.8934,
  "7":  0.8866,   "8":  0.8954,   "9":  0.9876,
  "10": 1.1194,   "11": 1.1322,   "12": 0.9843
}
```

**Key Observations**:
- 🔺 **October (1.12) & November (1.13)**: Peak demand — festival season (Diwali, Navratri)
- 🔺 **March (1.06) & April (1.06)**: Spring uptick — financial year end travel
- 🔻 **June–August (0.89)**: Monsoon season — reduced two-wheeler and vehicle movement

---

## 🖼️ Pre-Generated Visualisation Images

These PNG files are output by `03_data_visualization.ipynb` and `04_model_training.ipynb`. They are embedded as static references in the Streamlit dashboard when live chart generation is unavailable (e.g., no data loaded).

| File | Source Notebook | Description |
|---|---|---|
| `viz_01_class_distribution.png` | `03_data_visualization.ipynb` | Class imbalance bar chart |
| `viz_02_sales_by_day.png` | `03_data_visualization.ipynb` | Average sales per day of week |
| `viz_03_seasonal_pattern.png` | `03_data_visualization.ipynb` | Monthly demand seasonality |
| `viz_04_yearly_growth.png` | `03_data_visualization.ipynb` | Annual sales YoY growth |
| `viz_05_opening_stock.png` | `03_data_visualization.ipynb` | Stock level trend line |
| `viz_06_refill_heatmap.png` | `03_data_visualization.ipynb` | Month × DayOfWeek refill heatmap |
| `viz_07_sales_distribution.png` | `03_data_visualization.ipynb` | Histogram of daily sales |
| `viz_confusion_matrix.png` | `04_model_training.ipynb` | Model confusion matrix |
| `viz_next_refill_prediction.png` | `05_prediction.ipynb` | Walk-forward simulation chart |
| `viz_roc_curve.png` | `04_model_training.ipynb` | ROC curve (AUC = 1.0) |
| `correlation_plot.png` | `02_feature_selection.ipynb` | Feature–target correlation bar |
| `feature_importance_plot.png` | `04_model_training.ipynb` | Feature importance bar chart |
| `heatmap.png` | `02_feature_selection.ipynb` | Feature cross-correlation heatmap |

---

## 🔒 Version Control Strategy

The `.gitignore` in the project root is configured as follows:

```gitignore
# Excluded (too large for git)
data/*.xlsx           ← Raw Excel files
data/*.csv            ← Processed CSVs
data/*.pkl            ← Model binary

# Exceptions (small configs — always tracked)
!data/petrol_pump_2011_2025.xlsx
!data/selected_features.csv
!data/model_features.json
!data/model_metrics.json
```

**Rationale**: Large data files bloat repository history. Team members regenerate `clean_data.csv` and `final_model.pkl` by running the notebooks locally. Only lightweight configuration and manifest files are committed.

---

## 🔄 Regenerating All Data Artifacts

Run the notebooks **in order** from the `notebooks/` directory:

```bash
cd notebooks
jupyter notebook
# Run: 01 → 02 → 03 → 04 → 05
```

All outputs (CSV, PKL, PNG, JSON) will be saved to this `data/` directory automatically.

---

## ⚠️ Important Notes

1. **Never commit `.pkl` files** — they can exceed GitHub's 100 MB file limit and may contain environment-specific binary data.
2. **Date parsing is dayfirst=True** — the raw data uses DD/MM/YYYY format. The `_normalise()` function handles both US and EU date formats via `format="mixed"`.
3. **Multi-sheet Excel handling** — always use the project's `_read_excel_all_sheets()` helper, not `pd.read_excel()` directly, to avoid losing data from non-primary sheets.
4. **Tank capacity assumption** — the system assumes a maximum tank capacity of **12,000 litres** and a refill trigger threshold of **2,000 litres**. Update `TANK_CAPACITY` and `REFILL_THRESHOLD` in `data_loader.py` if your pump differs.
