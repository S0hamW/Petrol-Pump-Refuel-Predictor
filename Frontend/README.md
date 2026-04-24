# 🖥️ Frontend/ — FuelIQ Streamlit Business Analytics Dashboard

This directory contains the complete **Streamlit web application** that serves as the primary user interface for the FuelIQ Business Analytics platform. It provides an interactive, data-driven dashboard for petrol pump operators to upload their operational data, view AI-generated refill predictions, explore historical analytics, and download management-ready reports.

---

## 📂 Directory Structure

```
Frontend/
├── app.py                    ← Main entry point — router, sidebar, theme bootstrap
├── requirements.txt          ← Python dependency manifest
│
├── pages/                    ← Modular page components (one file per dashboard section)
│   ├── __init__.py
│   ├── home.py               ← Dashboard: AI prediction, KPI cards, charts, PDF export
│   ├── data_overview.py      ← Dataset explorer: schema, stats, CSV download
│   ├── feature_engineering.py← Feature definitions, importance rankings, correlations
│   ├── visualizations.py     ← EDA charts: seasonal, weekly, yearly, refill heatmap
│   └── model_insights.py     ← Model metrics, ROC curve, confusion matrix, hyperparams
│
└── utils/                    ← Shared backend logic and helpers
    ├── __init__.py
    ├── data_loader.py        ← Data ingestion, normalisation, prediction, simulation
    ├── chart_helpers.py      ← Plotly chart factory (25+ chart functions)
    ├── theme.py              ← Dual dark/light design system + CSS injection
    └── pdf_report.py         ← PDF report generator (FPDF2)
```

---

## 🚀 How to Run

### Prerequisites

- Python 3.10 or higher
- A virtual environment (recommended)

### Setup

```bash
# From the project root (soham/)
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (macOS / Linux)
source .venv/bin/activate

# Install all dependencies
pip install -r Frontend/requirements.txt
```

### Launch

```bash
cd Frontend
streamlit run app.py
```

The dashboard will open at **`http://localhost:8501`** in your default browser.

---

## 📦 Dependencies

| Package | Min Version | Purpose |
|---|---|---|
| `streamlit` | 1.32.0 | Web application framework & UI components |
| `pandas` | 2.0.0 | Data manipulation and DataFrame operations |
| `numpy` | 1.24.0 | Numerical computation and array operations |
| `plotly` | 5.18.0 | Interactive charting (line, bar, scatter, heatmap) |
| `scikit-learn` | 1.3.0 | Loading and running the Random Forest model |
| `openpyxl` | 3.1.0 | Reading multi-sheet Excel (.xlsx) files |
| `fpdf2` | 2.7.0 | Generating downloadable PDF summary reports |

Install all with:
```bash
pip install -r requirements.txt
```

---

## 🗂️ Application Entry Point — `app.py`

**`app.py`** is the main router. It is responsible for:

1. **Page Configuration** — Sets the Streamlit page title (`FuelIQ Dashboard`), icon (⛽), wide layout, and expanded sidebar using `st.set_page_config()` (must be the absolute first Streamlit call).
2. **Theme Bootstrap** — Calls `apply_theme()` from `utils/theme.py` to inject CSS into the page based on the current dark/light mode stored in `st.session_state`.
3. **Sidebar Navigation** — Renders the branded sidebar with two navigation groups:
   - **MAIN**: Dashboard, Data Overview
   - **ANALYSIS**: Feature Engineering, Visualizations, Model Insights
4. **Data Status Banner** — Displays a ✅ `DATA READY` or ⚠️ `NO DATA LOADED` badge in the sidebar based on whether `st.session_state.df` is set.
5. **Page Router** — Routes to the correct page module's `render()` function based on `st.session_state.current_page`.

### Navigation Flow

```
app.py
  │
  ├── Sidebar Button: "Dashboard"          → pages/home.py:render()
  ├── Sidebar Button: "Data Overview"      → pages/data_overview.py:render()
  ├── Sidebar Button: "Feature Engineering"→ pages/feature_engineering.py:render()
  ├── Sidebar Button: "Visualizations"     → pages/visualizations.py:render()
  └── Sidebar Button: "Model Insights"     → pages/model_insights.py:render()
```

### Session State Keys

| Key | Type | Description |
|---|---|---|
| `dark_mode` | `bool` | True = dark theme (default), False = light |
| `current_page` | `str` | Name of the active dashboard page |
| `df` | `pd.DataFrame` | The loaded petrol pump dataset (None until loaded) |
| `data_source` | `str` | `"demo"` or `"upload"` |
| `uploaded_filename` | `str` | Name of the user-uploaded file |
| `_last_file_key` | `str` | Cache key to prevent re-parsing the same file |

---

## 📄 Pages

### 1. 🏠 `pages/home.py` — Dashboard

The primary landing page and the most feature-rich page in the application.

**Sections:**
- **Data Source Card**: File uploader (CSV / XLSX) + "⚡ Use Demo Data" button. Displays a 4-column summary grid (Source, Records, Date Range, Refill Events) immediately after loading.
- **KPI Stat Row**: 4 stat cards — Total Records, Avg Daily Sales (litres), Current Stock (with colour-coded level), Refill Event Count.
- **AI Prediction Card**: The centrepiece of the dashboard. Calls `predict_refill()` and displays:
  - Predicted Refill Date
  - Days Remaining
  - Closing Stock of last record
  - Model Confidence progress bar
- **Why This Prediction**: Plain-language explanation card with 3 bullet points — stock level context, 7-day rolling sales vs average, model accuracy note.
- **PDF Report Download**: One-click download of a structured management report generated by `utils/pdf_report.py`.
- **Quick Charts**: Two side-by-side Plotly charts:
  - **Stock Forecast – Next 8 Days** (`drawdown_chart`)
  - **7-Day Rolling Sales – Last 60 Days** (`rolling_sales_chart`)

**Key dependencies**: `data_loader.predict_refill()`, `data_loader.simulate_forward()`, `chart_helpers.drawdown_chart()`, `pdf_report.generate_pdf_report()`

---

### 2. 📋 `pages/data_overview.py` — Data Overview

Full dataset exploration and validation page.

**Sections:**
- **5-Column Summary Banner**: Total Rows, Columns, Start Date, End Date, Missing Values (coloured red/green).
- **Dataset Schema Table**: Interactive `st.dataframe` showing all columns with data type, non-null count, missing count, missing %, and a sample value.
- **Full Dataset Preview**: Scrollable 450px-tall dataframe showing all rows.
- **Descriptive Statistics**: `df.describe()` output for all numeric columns.
- **Export Tools**:
  - ⬇️ Download Cleaned CSV — exports the processed DataFrame
  - 🔎 Verify Last Entry — expandable panel showing the most recent row's key fields

---

### 3. 🔧 `pages/feature_engineering.py` — Feature Engineering

Explains the 19 features used by the ML model with full business context.

**Sections:**
- **Feature Catalogue**: Each of the 19 model features rendered as a styled card showing:
  - Feature name
  - Formula / derivation logic
  - Business rationale ("Why this matters")
- **Feature Importance Chart**: Horizontal bar chart from `selected_features.csv` ranking all 11 shortlisted features by their Random Forest importance score.
- **Correlation with Target**: Bar chart showing each feature's Pearson correlation with `Refill_Required` (positive = higher stock correlates with refill).

---

### 4. 📈 `pages/visualizations.py` — Visualizations

Comprehensive EDA chart gallery for business pattern discovery.

**Charts included:**
| Chart | Type | Business Insight |
|---|---|---|
| Sales by Day of Week | Bar | Which weekdays drive highest fuel demand |
| Monthly Seasonal Pattern | Line | Identify festival/monsoon demand swings |
| Year-over-Year Sales Growth | Bar | Annual business growth trajectory |
| Opening Stock Trend | Line | Historical stock management patterns |
| Refill Event Heatmap | Heatmap | When refills cluster across month × weekday |
| Sales Distribution | Histogram | Normal distribution of daily volumes |
| Class Distribution | Bar | Ratio of refill vs non-refill days |

---

### 5. 🧠 `pages/model_insights.py` — Model Insights

Full ML model explainability and performance audit page.

**Sections:**
- **Model Summary Card**: Algorithm name, training size, model artifact name.
- **Validation Metrics (4 cards)**:
  - Accuracy: 100.0%
  - F1-Score: 100.0%
  - ROC-AUC: 1.000
  - Refill Event Count
- **Model Evaluation Charts**:
  - ROC Curve — visualises false positive vs true positive trade-off
  - Confusion Matrix — actual vs predicted class breakdown on the test set
- **About the Model**: Structured table of hyperparameters, training strategy, target variable, and file references.

---

## 🛠️ Utilities

### `utils/data_loader.py`

The backbone of all data operations. Key functions:

| Function | Cache | Description |
|---|---|---|
| `load_demo_data()` | `@st.cache_data` | Loads the bundled dataset from `/data`; picks source with most rows |
| `load_uploaded_data(bytes, name)` | `@st.cache_data` | Parses user-uploaded CSV/XLSX; combines all sheets |
| `load_model()` | `@st.cache_resource` | Loads `final_model.pkl` once per session |
| `load_metrics()` | `@st.cache_data` | Reads `model_metrics.json` |
| `load_features()` | `@st.cache_data` | Reads `model_features.json` |
| `load_selected_features()` | `@st.cache_data` | Reads `selected_features.csv` with correlation enrichment |
| `predict_refill(df, model, features, adj)` | — | Walk-forward 30-day simulation; returns prediction dict |
| `simulate_forward(df, adj, n_days)` | — | 15-day walk-forward table for PDF and sim pages |
| `_normalise(df)` | — | Adds all 19 engineered features to any raw DataFrame |
| `_read_excel_all_sheets(path)` | — | Reads + concatenates all Excel sheets; deduplicates |
| `_generate_synthetic_data()` | — | Fallback: generates 365 rows of synthetic pump data |

**Walk-Forward Prediction Logic (`predict_refill`):**
1. Starts from the **last row** of the loaded dataset as the seed state.
2. For each simulated future day (up to 30):
   - Estimates demand using a **blended DOW average** (60% recent rolling 4-week, 40% exponential weighted mean)
   - Applies the **monthly seasonal multiplier** from `monthly_multipliers.json`
   - Applies a **stock-pressure cap** — demand is naturally constrained when stock is low
   - Builds a full 19-feature inference row
   - Calls `model.predict_proba()` to get the refill probability
   - Triggers a refill when stock drops below **2,000 litres**
3. Returns: `refill_date`, `days_remaining`, `confidence`, `avg_sold`, `closing_stock`

---

### `utils/chart_helpers.py`

A Plotly chart factory with 25+ chart-generating functions, all theme-aware (dark/light). Key charts:

| Function | Chart Type | Used In |
|---|---|---|
| `drawdown_chart(df, dark, pred)` | Line + area | Home — Stock Forecast |
| `rolling_sales_chart(df, dark)` | Line | Home — 7-Day Rolling Sales |
| `roc_curve_chart(dark)` | Line | Model Insights — ROC Curve |
| `confusion_matrix_chart(dark)` | Annotated Heatmap | Model Insights — Confusion Matrix |
| `feature_importance_chart(feat_df, dark)` | Horizontal Bar | Feature Engineering |
| `sales_by_day_chart(df, dark)` | Bar | Visualizations |
| `seasonal_chart(df, dark)` | Line | Visualizations |
| `yearly_growth_chart(df, dark)` | Bar | Visualizations |
| `refill_heatmap(df, dark)` | Heatmap | Visualizations |
| `sales_distribution_chart(df, dark)` | Histogram | Visualizations |

All charts use the theme's `plot_paper`, `plot_bg`, `grid_color`, and `template` tokens for consistent rendering.

---

### `utils/theme.py`

The FuelIQ design system — a complete dual-mode (dark/light) CSS framework injected via `st.markdown(..., unsafe_allow_html=True)`.

**Theme Tokens:**

| Token | Dark Value | Light Value | Used For |
|---|---|---|---|
| `bg` | `#0E1117` | `#f4f6fb` | Page background |
| `sidebar_bg` | `#0a0d13` | `#ffffff` | Sidebar background |
| `card_bg` | `#161b27` | `#ffffff` | Card backgrounds |
| `accent` | `#f59e0b` | `#d97706` | Amber — primary highlight |
| `accent2` | `#22c55e` | `#16a34a` | Green — positive signals |
| `accent3` | `#6366f1` | `#4f46e5` | Indigo — secondary accent |
| `danger` | `#ef4444` | `#dc2626` | Low stock / critical alerts |
| `warning` | `#f97316` | `#ea580c` | Mid-level warnings |
| `success` | `#22c55e` | `#16a34a` | Positive indicators |
| `text_primary` | `#e8eaf0` | `#0f172a` | Body text |
| `text_secondary` | `#6b7a99` | `#64748b` | Labels, subtitles |

**CSS Components defined:**
- `.stat-card`, `.stat-row` — KPI metric cards with hover lift effect
- `.pred-card`, `.pred-grid` — AI prediction card layout
- `.conf-bar-track`, `.conf-bar-fill` — Confidence progress bar
- `.fiq-card`, `.fiq-card-header` — Generic info cards
- `.feat-row`, `.feat-name`, `.feat-formula` — Feature catalogue rows
- `.metric-card`, `.metric-value` — Model metrics cards
- `.no-data-wrap`, `.no-data-badge` — Empty state UI
- `.brand-wrap`, `.nav-label` — Sidebar branding
- Native Streamlit component overrides (buttons, file uploader, sliders, expanders, tabs, dataframes)

**Exported Functions:**
- `get_theme(dark: bool) -> dict` — Returns the active theme token dict
- `apply_theme(dark: bool)` — Injects the full CSS stylesheet
- `theme_toggle()` — Renders the dark/light toggle button
- `no_data_state(page_name, icon)` — Renders the standard empty-state placeholder

---

### `utils/pdf_report.py`

Generates a formatted **management PDF report** using the FPDF2 library. The report includes:

- FuelIQ branding header
- Next predicted refill date and confidence score
- Current stock status with visual indicators
- Days remaining until refill
- 15-day walk-forward stock simulation table (Date, Opening Stock, Estimated Sold, Closing Stock, Refill Triggered)
- Model accuracy summary footer

**Output**: `fueliq_prediction_report.pdf` — downloadable directly from the Dashboard page.

---

## 🎨 Design Principles

1. **No Data = Graceful Degradation** — Every page calls `no_data_state()` if `st.session_state.df` is `None`, guiding users back to the Dashboard to upload data.
2. **Session State as Single Source of Truth** — The DataFrame (`df`), theme preference, and navigation state all live in `st.session_state`, ensuring consistent state across page switches without re-loading data.
3. **Caching Strategy** — `@st.cache_data` for data and metrics, `@st.cache_resource` for the model (loaded once per process lifetime). File-upload cache is cleared on each new upload via `load_uploaded_data.clear()`.
4. **Theme Consistency** — All HTML/CSS injected via `unsafe_allow_html=True` uses dynamic f-string interpolation of theme token values, ensuring charts and custom HTML components always match the current dark/light mode.
5. **Multi-Sheet Excel Safety** — The app never silently loads partial data. A warning is displayed if fewer than 500 rows are loaded, prompting the user to check their file.

---

## ✅ Supported Data Formats

| Format | Extension | Notes |
|---|---|---|
| CSV | `.csv` | Standard UTF-8 CSV; Date column auto-detected |
| Excel 2007+ | `.xlsx` | Multi-sheet — all sheets are merged |
| Excel Legacy | `.xls` | Supported via openpyxl |
| Excel Macro | `.xlsm` | Supported |

**Required Columns** (at minimum):

| Column | Aliases Accepted |
|---|---|
| `Date` | `date`, `DATE`, `Dates` |
| `Opening_Stock` | — |
| `Total_Sold` | `TotalSold`, `TotalSales`, `Sales` |
| `Refill_Required` | `Refill` (mapped to `Target`) |

All other columns are derived automatically by `_normalise()` if missing.

---

## 🐛 Troubleshooting

| Issue | Likely Cause | Fix |
|---|---|---|
| Only N rows loaded | Excel file has data on multiple sheets without a `Date` column | Ensure all sheets have a `Date` column |
| Model not loading | `final_model.pkl` missing from `/data` | Run `04_model_training.ipynb` to regenerate |
| "Prediction error" toast | A feature column missing after normalisation | Check your data has `Opening_Stock`, `Total_Sold`, and `Refill_Required` |
| Charts look washed out | Theme not applied (e.g., partial load) | Refresh the browser tab |
| File re-uploads ignored | Stale cache key | Click "Use Demo Data" once, then re-upload |
