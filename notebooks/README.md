# 📓 notebooks/ — ML Experiment Lifecycle & EDA Workbooks

This directory is the **research and experimentation layer** of the FuelIQ Business Analytics platform. It contains a complete, sequential pipeline of Jupyter notebooks that take raw petrol pump Excel data through every stage of the machine learning lifecycle — from initial cleaning to live refill prediction — producing all the model artifacts, datasets, and visualisation images consumed by the production Streamlit dashboard.

---

## 📂 Directory Contents

```
notebooks/
├── 01_data_preparation.ipynb       ← Data ingestion, cleaning, deduplication
├── 02_feature_selection.ipynb      ← Correlation analysis, feature shortlisting
├── 03_data_visualization.ipynb     ← EDA charts, seasonal analysis, business insights
├── 04_model_training.ipynb         ← Random Forest training, evaluation, serialisation
└── 05_prediction.ipynb             ← Walk-forward simulation, refill date prediction
```

> **Run Order**: Notebooks are numbered and **must be executed sequentially** (01 → 02 → 03 → 04 → 05). Each notebook depends on outputs from the previous one.

---

## 🚀 Getting Started

### Launch Jupyter

```bash
# Activate your virtual environment first
.venv\Scripts\activate       # Windows
source .venv/bin/activate    # macOS / Linux

# Install dependencies (if not already done)
pip install -r ../Frontend/requirements.txt
pip install jupyter notebook

# Launch Jupyter from the notebooks directory
cd notebooks
jupyter notebook
```

### Run All Notebooks End-to-End

```bash
# Alternatively, run headlessly from the terminal
jupyter nbconvert --to notebook --execute 01_data_preparation.ipynb --output 01_data_preparation.ipynb
jupyter nbconvert --to notebook --execute 02_feature_selection.ipynb --output 02_feature_selection.ipynb
jupyter nbconvert --to notebook --execute 03_data_visualization.ipynb --output 03_data_visualization.ipynb
jupyter nbconvert --to notebook --execute 04_model_training.ipynb --output 04_model_training.ipynb
jupyter nbconvert --to notebook --execute 05_prediction.ipynb --output 05_prediction.ipynb
```

---

## 📋 Notebook Reference

---

### 📘 `01_data_preparation.ipynb` — Data Ingestion & Cleaning

**Purpose**: Transform raw multi-sheet Excel data into a clean, analysis-ready DataFrame.

**Inputs**:
- `../data/petrol_pump_2011_2025.xlsx` (primary, 14+ years)
- `../data/petrol_pump_data_2024_2026.xlsx` (supplementary)

**Key Operations**:

| Step | Description |
|---|---|
| Multi-sheet merge | Reads all sheets, concatenates with `pd.concat`, deduplicates on identical rows |
| Date parsing | Converts Date column with `dayfirst=True` to handle DD/MM/YYYY format |
| Column normalisation | Strips whitespace from headers; renames date aliases |
| Numeric coercion | Converts all stock/sales columns to float via `pd.to_numeric(errors='coerce')` |
| Missing value strategy | Fills stock/sales nulls with 0; drops rows with unparseable dates |
| `Closing_Stock` derivation | If missing: `Opening_Stock − Total_Sold` clipped at 0 |
| `Total_Sold` derivation | If missing: sum of `MS_Sold + HSD1_Sold + HSD2_Sold + HSD3_Sold` |
| `Target` encoding | Maps `Refill_Required` Yes/No → 1/0 integer |
| Chronological sort | Sorts by Date and resets index |

**Outputs**:
- `../data/clean_data.csv` — The cleaned dataset used by all subsequent notebooks and the dashboard

**File Size**: ~97 KB for ~800+ daily records

---

### 📗 `02_feature_selection.ipynb` — Feature Engineering & Selection

**Purpose**: Construct the 19 domain-aware predictive features and identify the most informative subset via correlation and importance analysis.

**Inputs**:
- `../data/clean_data.csv`

**Feature Engineering Steps**:

| Feature | Type | Derivation |
|---|---|---|
| `Month`, `Year`, `DayOfWeek` | Temporal | Extracted from `Date` |
| `Is_Weekend` | Binary flag | `DayOfWeek >= 5` |
| `Is_Festival_Month` | Binary flag | `Month ∈ {10, 11}` — Diwali/Navratri |
| `Is_Monsoon_Month` | Binary flag | `Month ∈ {6, 7, 8, 9}` |
| `Rolling_7d_Sales` | Rolling stat | 7-day rolling mean of `Total_Sold` |
| `Prev_Closing` | Lag | `Closing_Stock.shift(1)` |
| `Stock_Ratio` | Ratio | `Closing_Stock / Opening_Stock` clipped to [0, 1] |
| `Days_Since_Refill` | Counter | Resets to 0 on each `Target=1` day |
| `Lag1_Total_Sold` | Lag | `Total_Sold.shift(1)` |
| `Lag2_Total_Sold` | Lag | `Total_Sold.shift(2)` |
| `Lag1_Closing` | Lag | `Closing_Stock.shift(1)` |
| `DOW_Avg_Sales` | EWM per group | EWM(span=8) of `Total_Sold` grouped by `DayOfWeek` |
| `Sales_Trend` | Ratio | `Rolling_7d_Sales / global_mean` |

**Feature Selection Method**:
1. **Pearson Correlation** with `Target` — identifies linearly correlated signals
2. **Random Forest Permutation Importance** — non-linear importance ranking
3. Features with importance > 1% and non-zero target correlation are shortlisted

**Key Findings**:
- `Opening_Stock` alone explains **51.1%** of model predictive power
- `Prev_Closing` contributes **29.0%** — together these two cover 80% of the signal
- Payment channels (`Cash`, `Online`, `Card`) are surprisingly informative (proxy for vehicle volume)
- `Days_Since_Refill` is a strong temporal prior — the longer since the last refill, the more likely the next one

**Outputs**:
- `../data/selected_features.csv` — Top 11 features with importance scores
- `../data/model_features.json` — Ordered 19-feature list for model inference
- `../data/correlation_plot.png` — Feature–target correlation bar chart
- `../data/heatmap.png` — Feature cross-correlation heatmap

---

### 📙 `03_data_visualization.ipynb` — Exploratory Data Analysis & Business Visualisations

**Purpose**: Generate a comprehensive suite of business analytics charts that reveal operational patterns across seasons, weekdays, years, and refill behaviours.

**Inputs**:
- `../data/clean_data.csv`

**Charts Generated**:

| Chart | Output File | Business Question Answered |
|---|---|---|
| Class distribution | `viz_01_class_distribution.png` | How often is a refill required? (~17% of days) |
| Sales by day of week | `viz_02_sales_by_day.png` | Which weekdays see highest fuel demand? |
| Monthly seasonal pattern | `viz_03_seasonal_pattern.png` | How does demand vary across months? |
| Year-over-year growth | `viz_04_yearly_growth.png` | Is the business growing year on year? |
| Opening stock trend | `viz_05_opening_stock.png` | How consistent is stock management? |
| Refill event heatmap | `viz_06_refill_heatmap.png` | When do refills cluster? (Month × Weekday) |
| Sales distribution | `viz_07_sales_distribution.png` | What is the typical daily volume range? |

**Key Business Insights Surfaced**:
- 🔺 **October & November** are peak demand months (festival season — ~11–13% above average)
- 🔻 **June–August** see depressed demand (monsoon season — ~10–11% below average)
- 📅 **Tuesday and Thursday** tend to have the highest daily sales
- 🔄 Refills cluster on **Monday and Wednesday** — consistent with weekend depletion patterns
- 📈 Annual sales show a **consistent upward growth trajectory** from 2011 to 2025
- 📊 Daily total sales follow a **near-normal distribution** centred around 4,400–4,600 litres

**Outputs**: 7 PNG visualisation files saved to `../data/`

---

### 📕 `04_model_training.ipynb` — Random Forest Model Training & Evaluation

**Purpose**: Train, tune, evaluate, and serialise the binary Random Forest Classifier that powers FuelIQ's refill prediction engine.

**Inputs**:
- `../data/clean_data.csv`
- `../data/model_features.json` (feature order)

**Training Pipeline**:

```
clean_data.csv
      │
      ├── Feature matrix X: 19 columns from model_features.json
      └── Target vector y: binary Target column (1=Refill, 0=No Refill)
              │
              ▼
    Stratified train-test split (80% / 20%)
    (stratify=y ensures class balance in both splits)
              │
              ▼
    RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        min_samples_leaf=3,
        class_weight='balanced',
        random_state=42
    )
              │
              ▼
    model.fit(X_train, y_train)
              │
              ▼
    Evaluate on X_test:
        - Accuracy  : 1.000
        - F1-Score  : 1.000
        - ROC-AUC   : 1.000
        - Confusion Matrix
        - ROC Curve
```

**Model Hyperparameter Rationale**:

| Parameter | Value | Why |
|---|---|---|
| `n_estimators` | 200 | Large ensemble reduces variance; stable predictions |
| `max_depth` | 12 | Deep enough to capture stock depletion patterns without overfitting |
| `min_samples_leaf` | 3 | Prevents leaf nodes with too few samples; improves generalisation |
| `class_weight` | `'balanced'` | Compensates for class imbalance (~17% refill days vs 83% non-refill) |
| `random_state` | 42 | Reproducible results |

**Why Near-Perfect Accuracy?**
The dataset has a near-deterministic relationship: when `Opening_Stock` drops below ~2,000 litres, a refill **always** occurs. This structural rule is perfectly learnable by a tree-based model. Real-world performance on future unseen data should be validated separately.

**Outputs**:
- `../data/final_model.pkl` — Serialised trained classifier
- `../data/model_metrics.json` — `{"accuracy": 1.0, "f1_score": 1.0, "roc_auc": 1.0}`
- `../data/feature_importance_plot.png` — Feature importance bar chart
- `../data/viz_confusion_matrix.png` — Confusion matrix heatmap
- `../data/viz_roc_curve.png` — ROC curve plot

---

### 📒 `05_prediction.ipynb` — Walk-Forward Simulation & Refill Prediction

**Purpose**: Validate the walk-forward simulation logic that the Streamlit dashboard uses to predict the next refill date. This notebook acts as the **ground truth reference** for `data_loader.predict_refill()`.

**Inputs**:
- `../data/clean_data.csv`
- `../data/final_model.pkl`
- `../data/model_features.json`
- `../data/monthly_multipliers.json`

**Walk-Forward Simulation Algorithm**:

```
Seed from last row of historical data:
  - current_stock = last Closing_Stock (or 12,000 if last day was a refill)
  - start_date = last Date + 1 day
  - lag1_sold, lag2_sold, lag1_closing = last known values
  - days_since_refill = days since last Target=1 event

For each future day i (i = 0 to 29):
  1. Estimate demand:
     - blended_est = 60% × (4-week rolling DOW avg) + 40% × (EWM DOW avg)
     - seasonal_adj = blended_est × monthly_multiplier[month]
     - stock_pressure = min(1.0, current_stock / 6,000)  ← constrains demand near depletion
     - est_sales = min(seasonal_adj × stock_pressure, current_stock)

  2. Build 19-feature inference row with all engineered values

  3. Call model.predict_proba(row) → get refill probability

  4. Compute closing = max(0, current_stock − est_sales)

  5. If closing < 2,000 litres:
     → Record refill_date, days_remaining, confidence
     → STOP simulation

  6. Advance state: update lag1, lag2, rolling_7d, current_stock

Return: refill_date, days_remaining, confidence, avg_sold, closing_stock
```

**15-Day Simulation Table** (for PDF report):

| Column | Description |
|---|---|
| `Date` | Simulated date |
| `Day` | Day of week name |
| `Opening_Stock` | Stock at start of simulated day |
| `Est_Sold` | Estimated fuel sold |
| `Closing_Stock` | Projected closing stock |
| `Refill_Probability` | "High (Refill Triggered)" or "Low" |
| `Refill_Triggered` | Boolean flag |

**Outputs**:
- `../data/viz_next_refill_prediction.png` — Visual plot of stock drawdown and refill trigger point

---

## 🔄 Full Pipeline Summary

```
notebooks/
│
├── 01_data_preparation.ipynb
│      Reads raw Excel → cleans → saves clean_data.csv
│
├── 02_feature_selection.ipynb
│      Reads clean_data.csv → engineers 19 features → saves:
│      selected_features.csv, model_features.json,
│      correlation_plot.png, heatmap.png
│
├── 03_data_visualization.ipynb
│      Reads clean_data.csv → generates 7 EDA charts → saves viz_0*.png
│
├── 04_model_training.ipynb
│      Reads clean_data.csv + model_features.json → trains RF →
│      saves final_model.pkl, model_metrics.json,
│      feature_importance_plot.png, viz_confusion_matrix.png, viz_roc_curve.png
│
└── 05_prediction.ipynb
       Reads clean_data.csv + model + features + multipliers →
       runs walk-forward simulation → saves viz_next_refill_prediction.png
```

All outputs feed directly into `Frontend/utils/data_loader.py` and `Frontend/utils/chart_helpers.py` for the live dashboard.

---

## 🏆 Experiment Results Summary

| Metric | Score | Notes |
|---|---|---|
| **Accuracy** | 100.0% | On 20% stratified holdout set |
| **F1-Score** | 1.000 | Perfect precision & recall balance |
| **ROC-AUC** | 1.000 | Perfect class separation |
| **Top Feature** | `Opening_Stock` (51.1%) | Dominant predictor |
| **2nd Feature** | `Prev_Closing` (29.0%) | Together: 80% of signal |
| **Training Size** | ~800+ daily records | 2011–2025 petrol pump operations |
| **Prediction Window** | Up to 30 days | Walk-forward simulation |
| **Seasonal Factors** | 12 monthly multipliers | Oct/Nov peak (+12%), Jun–Aug trough (−11%) |

---

