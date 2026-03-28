# ⛽ Petrol Pump Refuelling Prediction System

> An end-to-end ML system that predicts when a petrol pump needs refuelling,
> built on 5000+ days of synthetic operational data generated using LangChain.

---

## 🧩 Problem Statement

A petrol pump needs refuelling roughly twice a week but cannot predict which days in advance.
This ML system reads the current stock level and predicts exactly when the next refill will be needed.

```
Closing Stock < 2000 L  →  Refill Required = YES
Closing Stock ≥ 2000 L  →  Refill Required = NO
```

---

## 🗂️ Project Structure

```
petrol-pump-ml/
│
├── notebooks/
│   ├── 01_data_preparation.ipynb       ← Load, clean, fix types, engineer features
│   ├── 02_feature_selection.ipynb      ← Find which columns actually matter for ML
│   ├── 03_data_visualization.ipynb     ← 7 charts — patterns, seasonality, trends
│   ├── 04_outlier_detection.ipynb      ← Detect and cap abnormal values
│   ├── 05_class_imbalance.ipynb        ← Fix Yes/No imbalance using SMOTE
│   ├── 06_model_training.ipynb         ← Train, compare, tune and save model
│   └── 07_prediction.ipynb             ← Predict next refill day from current stock
│
├── data/
│   ├── petrol_pump_2011_2025.xlsx      ← Raw dataset (5189 rows, Jan 2011–Mar 2025)
│   ├── clean_data.csv                  ← Output: notebook 01
│   ├── selected_features.csv           ← Output: notebook 02
│   ├── clean_data_no_outliers.csv      ← Output: notebook 04
│   ├── balanced_data.csv               ← Output: notebook 05
│   ├── final_model.pkl                 ← Output: notebook 06 (trained model)
│   ├── model_features.json             ← Output: notebook 06 (feature list)
│   ├── model_metrics.json              ← Output: notebook 06 (accuracy scores)
│   ├── correlation_plot.png            ← Output: notebook 02
│   ├── feature_importance_plot.png     ← Output: notebook 02
│   ├── heatmap.png                     ← Output: notebook 02
│   ├── viz_01_class_distribution.png   ← Output: notebook 03
│   ├── viz_02_sales_by_day.png         ← Output: notebook 03
│   ├── viz_03_seasonal_pattern.png     ← Output: notebook 03
│   ├── viz_04_yearly_growth.png        ← Output: notebook 03
│   ├── viz_05_opening_stock.png        ← Output: notebook 03
│   ├── viz_06_refill_heatmap.png       ← Output: notebook 03
│   ├── viz_07_sales_distribution.png   ← Output: notebook 03
│   ├── viz_outlier_boxplots.png        ← Output: notebook 04
│   ├── viz_outliers_timeseries.png     ← Output: notebook 04
│   ├── viz_imbalance_before.png        ← Output: notebook 05
│   ├── viz_imbalance_comparison.png    ← Output: notebook 05
│   ├── viz_model_comparison.png        ← Output: notebook 06
│   ├── viz_roc_curves.png              ← Output: notebook 06
│   ├── viz_confusion_matrix.png        ← Output: notebook 06
│   └── viz_next_refill_prediction.png  ← Output: notebook 07
│
└── README.md
```

---

## ⚙️ Setup

```bash
# 1. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate           # Windows
source venv/bin/activate        # Mac/Linux

# 2. Install all required packages
pip install pandas openpyxl matplotlib seaborn scikit-learn imbalanced-learn xgboost jupyter notebook

# 3. Start Jupyter
cd petrol-pump-ml
jupyter notebook
```

---

## ▶️ Run Order — IMPORTANT

Run notebooks **in this exact order**. Each one saves a file that the next one reads.

| # | Notebook | Reads | Saves |
|---|---|---|---|
| 1 | 01_data_preparation | petrol_pump_2011_2025.xlsx | clean_data.csv |
| 2 | 02_feature_selection | clean_data.csv | selected_features.csv + 3 PNGs |
| 3 | 03_data_visualization | clean_data.csv | 7 PNGs |
| 4 | 04_outlier_detection | clean_data.csv | clean_data_no_outliers.csv + 2 PNGs |
| 5 | 05_class_imbalance | clean_data_no_outliers.csv | balanced_data.csv + 2 PNGs |
| 6 | 06_model_training | balanced_data.csv | final_model.pkl + 3 PNGs |
| 7 | 07_prediction | clean_data_no_outliers.csv + final_model.pkl | viz_next_refill_prediction.png |

---

## 📓 Notebooks — Detailed Breakdown

### 01 — Data Preparation
Loads the raw Excel file and engineers all features needed for ML.

- Loads Excel, inspects shape, columns, data types
- Checks and handles missing values
- Parses `Date` column and extracts: `Year`, `Month`, `DayOfWeek`, `Quarter`, `WeekOfYear`, `DayOfYear`
- Adds binary flags: `Is_Weekend`, `Is_Festival_Month`, `Is_Monsoon_Month`, `Is_Summer_Month`
- Adds lag features: `Prev_Closing`, `Prev_Total_Sold`
- Adds rolling averages: `Rolling_7d_Sales`, `Rolling_3d_Sales`
- Encodes target: `Refill_Required` → `Target` (0/1)
- Validates business rules (no negative stock, opening ≤ 12000L)

**Output:** `clean_data.csv` — 5189 rows, 25+ columns

---

### 02 — Feature Selection
Identifies which columns actually help predict refill and drops the rest.

- Pearson correlation of every feature against `Target`
- Random Forest feature importance scores
- Multicollinearity check — drops features correlated > 0.90 with each other
- Drops leaky features: `Closing_Stock`, `Stock_Ratio`, `Dip` — these directly reveal the answer and cannot be used at prediction time
- Keeps features above 1% importance threshold

**Output:** `selected_features.csv`, `correlation_plot.png`, `feature_importance_plot.png`, `heatmap.png`

---

### 03 — Data Visualization
7 charts to understand patterns in the data before training.

| Chart | What it shows |
|---|---|
| `viz_01_class_distribution.png` | 36% Refill vs 64% No Refill — class imbalance |
| `viz_02_sales_by_day.png` | Weekend sales 20–30% higher than weekdays |
| `viz_03_seasonal_pattern.png` | Monsoon ↓8%, Diwali ↑15%, Summer ↑8% |
| `viz_04_yearly_growth.png` | +2% year-on-year sales growth 2011→2025 |
| `viz_05_opening_stock.png` | Stock distribution on refill vs no-refill days |
| `viz_06_refill_heatmap.png` | Refill frequency by day of week × month |
| `viz_07_sales_distribution.png` | Sales histogram + Cash/Online/Card split |

---

### 04 — Outlier Detection & Handling
Detects and controls abnormal values using three methods.

| Method | How it works |
|---|---|
| IQR | Flags values outside Q1 − 1.5×IQR and Q3 + 1.5×IQR |
| Z-Score | Flags values more than 3 standard deviations from mean |
| Isolation Forest | ML-based — learns normal patterns, flags anomalies |

**Decision — Winsorizing:** Values below 1st percentile are raised to 1st percentile; above 99th percentile are lowered. No rows deleted — data preserved, extremes controlled.

**Output:** `clean_data_no_outliers.csv`, `viz_outlier_boxplots.png`, `viz_outliers_timeseries.png`

---

### 05 — Class Imbalance Handling
Fixes the 64%/36% split so the model learns both classes equally.

| Approach | What it does |
|---|---|
| Baseline | No balancing — model biased toward No Refill |
| Class Weights | Penalises wrong Refill predictions more |
| **SMOTE** ✅ | Creates synthetic Refill rows by interpolating existing ones |
| Undersampling | Deletes No Refill rows — loses real data |

Winner determined by highest F1 Score — typically SMOTE.

**Output:** `balanced_data.csv`, `viz_imbalance_before.png`, `viz_imbalance_comparison.png`

---

### 06 — Model Training & Evaluation
Trains 4 models on balanced data, compares on original data, tunes and saves the best.

| Model | Approach |
|---|---|
| Logistic Regression | Simple linear baseline |
| Decision Tree | Interpretable if-then rules |
| **Random Forest** ✅ | 100 independent trees, majority vote |
| XGBoost | Sequential boosting — each tree corrects previous errors |

**Metrics:** Accuracy, F1 Score (primary), ROC-AUC

**Tuning:** GridSearchCV with 5-fold cross-validation on `n_estimators`, `max_depth`, `min_samples_split`, `class_weight`

**Output:** `final_model.pkl`, `model_features.json`, `model_metrics.json`, `viz_model_comparison.png`, `viz_roc_curves.png`, `viz_confusion_matrix.png`

---

### 07 — Prediction
Reads the last entry from cleaned data, simulates stock drawdown day by day,
and predicts exactly when the next refill will be needed.

**How it works:**
- Reads `clean_data_no_outliers.csv` — takes last row as starting point
- Determines opening stock: if last day had refill → 12000L, else last closing stock
- Calculates real average daily consumption per day of week from historical data
- Simulates stock decreasing day by day using those averages
- Stops when closing stock drops below 2000L — that is the next refill day
- ML model confirms the prediction with a probability score

**Example output:**
```
=======================================================
  NEXT REFILL PREDICTION
  Current stock : 4844 L
  From date     : 17-03-2025
=======================================================

  Next refill needed on:
  Date          : 17-03-2025  (Monday)
  Days from now : 1 day(s)
  Opening stock : 4844 L
  Expected sold : 4537 L
  Closing stock : 307 L  (below 2000L threshold)
  ML confidence : 100%
=======================================================
```

**Output:** `viz_next_refill_prediction.png`

---

## 📊 Dataset

| Property | Value |
|---|---|
| Source | Synthetic — generated using LangChain + GPT-4o-mini |
| Rows | 5,189 days |
| Date range | Jan 2011 → Mar 2025 |
| Refill days | ~36% Yes, ~64% No |
| Columns | Date, Day, Opening Stock, MS/HSD1/HSD2/HSD3 Sold, Total Sold, Closing Stock, Cash, Online, Card, Dip, Refill Required |

---

## 🛠️ Tech Stack

`Python` `Scikit-learn` `XGBoost` `Pandas` `NumPy` `Matplotlib` `Seaborn` `imbalanced-learn` `LangChain` `OpenAI API` `Jupyter Notebooks` `OpenPyXL`
