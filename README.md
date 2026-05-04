# ⛽ PetroPredict — Petrol Pump Business Analytics & Refuel Predictor

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32%2B-FF4B4B?logo=streamlit)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.3%2B-F7931E?logo=scikit-learn)
![Plotly](https://img.shields.io/badge/Plotly-5.18%2B-3F4F75?logo=plotly)
![License](https://img.shields.io/badge/License-MIT-green)

**A full-stack business analytics platform for petrol pump operations — powered by Machine Learning.**

</div>

---

## 📌 Project Overview

**FuelIQ** is a production-grade **business analytics and decision-support tool** designed for petrol pump owners and managers. It combines over **14 years of historical operational data** (2011–2025) with a trained **Random Forest Classifier** to accurately predict the next fuel refill date, track daily stock drawdown, and surface actionable business insights through an interactive Streamlit dashboard.

The system addresses a real-world operational challenge: **petrol pump operators often run low on stock unexpectedly**, resulting in lost sales and customer dissatisfaction. PetroPredict solves this by:

- 📊 **Analysing** historical daily sales, stock levels, and payment trends
- 🤖 **Predicting** the next refill date with up to **100% model accuracy**
- 📈 **Visualising** seasonal patterns, weekly rhythms, and year-over-year growth
- 🔧 **Engineering** 19 domain-aware features for robust model generalisation
- 📄 **Generating** downloadable PDF summary reports for management review

---

## 🏗️ Repository Structure

```
soham/
├── README.md                   ← You are here (Main project README)
├── .gitignore                  ← Comprehensive ignore rules for Python, Jupyter & data files
│
├── Frontend/                   ← Streamlit web application (Business Analytics Dashboard)
│   ├── app.py                  ← Main router: page navigation + sidebar + theme engine
│   ├── requirements.txt        ← Python dependency manifest
│   ├── pages/                  ← Modular page components
│   │   ├── home.py             ← Dashboard: KPI cards, AI prediction, quick charts, PDF export
│   │   ├── data_overview.py    ← Schema explorer, descriptive stats, CSV export
│   │   ├── feature_engineering.py  ← Feature definitions, importance rankings, correlation view
│   │   ├── visualizations.py   ← Interactive charts (seasonal, weekly, yearly, refill heatmap)
│   │   └── model_insights.py   ← Model metrics, ROC curve, confusion matrix, explainability
│   └── utils/                  ← Shared backend utilities
│       ├── data_loader.py      ← Data ingestion, normalisation, walk-forward prediction engine
│       ├── chart_helpers.py    ← Plotly chart factory functions (stock, sales, ROC, CM, etc.)
│       ├── theme.py            ← Dual-mode (Dark/Light) design system in pure CSS
│       └── pdf_report.py       ← PDF report generator (FPDF2)
│
├── data/                       ← Datasets, model artifacts, and configuration JSONs
│   ├── petrol_pump_2011_2025.xlsx          ← 14-year historical raw dataset (primary)
│   ├── petrol_pump_data_2024_2026.xlsx     ← Recent 2-year operational data
│   ├── clean_data.csv                      ← Pre-processed, feature-engineered dataset
│   ├── selected_features.csv               ← Feature importance rankings (11 features)
│   ├── model_features.json                 ← Ordered list of 19 model input features
│   ├── model_metrics.json                  ← Model evaluation results (accuracy, F1, ROC-AUC)
│   ├── monthly_multipliers.json            ← Seasonal demand multipliers by month
│   ├── final_model.pkl                     ← Trained Random Forest Classifier (serialised)
│   └── viz_*.png / *.png                   ← Pre-generated chart images from notebook runs
│
└── notebooks/                  ← Jupyter notebooks: EDA, modelling, and experiment lifecycle
    ├── 01_data_preparation.ipynb       ← Data ingestion, cleaning, deduplication
    ├── 02_feature_selection.ipynb      ← Correlation analysis, feature shortlisting
    ├── 03_data_visualization.ipynb     ← EDA charts (seasonal, weekly, distribution plots)
    ├── 04_model_training.ipynb         ← Random Forest training, hyperparameter tuning
    └── 05_prediction.ipynb             ← Walk-forward simulation and refill prediction
```

---

## 🚀 Quick Start

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r Frontend/requirements.txt
```
```bash
cd Frontend
streamlit run app.py
```

Open your browser at **`http://localhost:8501`**.

---

## 🧭 Application Workflow

```
Raw Excel Data (2011–2025)
        │
        ▼
[01_data_preparation.ipynb]  →  Cleaned & deduplicated DataFrame
        │
        ▼
[02_feature_selection.ipynb] →  19 engineered features selected
        │
        ▼
[03_data_visualization.ipynb] → EDA charts saved to /data
        │
        ▼
[04_model_training.ipynb]    →  final_model.pkl + model_metrics.json
        │
        ▼
[05_prediction.ipynb]        →  Walk-forward simulation validated
        │
        ▼
[Frontend/app.py]            →  Live Streamlit dashboard
```

---

## 📊 Dashboard Pages

| Page | Icon | Description |
|---|---|---|
| **Dashboard** | ⛽ | AI prediction card, KPI metrics, stock forecast & rolling sales charts, PDF download |
| **Data Overview** | 📋 | Full dataset preview, schema validation, descriptive statistics, CSV export |
| **Feature Engineering** | 🔧 | 19-feature definitions, importance bar chart, correlation with target |
| **Visualizations** | 📈 | Seasonal patterns, sales by day-of-week, yearly growth, refill heatmap |
| **Model Insights** | 🧠 | Accuracy/F1/ROC-AUC metrics, ROC curve, confusion matrix, hyperparameter reference |

---

## 🤖 Machine Learning Model

| Property | Value |
|---|---|
| **Algorithm** | Random Forest Classifier (scikit-learn) |
| **Training Set** | 14+ years of daily petrol pump records |
| **Features** | 19 engineered signals (stock levels, lag features, DOW patterns, seasonal multipliers) |
| **Target** | Binary — `Refill_Required`: Yes (1) / No (0) |
| **Accuracy** | **100%** on held-out test set |
| **F1-Score** | **1.000** |
| **ROC-AUC** | **1.000** |
| **Validation** | Stratified 80/20 train-test split |
| **Hyperparameters** | `n_estimators=200`, `max_depth=12`, `min_samples_leaf=3` |

### Top Predictive Features (by Importance)

| Rank | Feature | Importance |
|---|---|---|
| 1 | `Opening_Stock` | 51.1% |
| 2 | `Prev_Closing` | 29.0% |
| 3 | `Total_Sold` | 2.8% |
| 4 | `Cash` | 2.4% |
| 5 | `HSD1_Sold` | 2.2% |


---

## 📦 Dependencies

| Package | Version | Purpose |
|---|---|---|
| `streamlit` | ≥ 1.32 | Web application framework |
| `pandas` | ≥ 2.0 | Data manipulation |
| `numpy` | ≥ 1.24 | Numerical computation |
| `plotly` | ≥ 5.18 | Interactive visualisations |
| `scikit-learn` | ≥ 1.3 | Random Forest model |
| `openpyxl` | ≥ 3.1 | Excel file I/O |
| `fpdf2` | ≥ 2.7 | PDF report generation |

---

## 📄 PDF Report Export

PetroPredict generates a downloadable **management-ready PDF report** containing:
- Next refill date prediction with confidence score
- Current stock level and days remaining
- 15-day walk-forward stock simulation table
- Model accuracy summary

---


## 📜 License

This project is licensed under the **MIT License**.  
Built as a business analytics capstone project demonstrating end-to-end ML deployment.

---

