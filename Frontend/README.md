# Frontend Application

This directory contains the FuelIQ Streamlit UI. It is designed to act as the primary interaction layer over our prediction models.

## Structure
- `Home.py`: The main entry point to the dashboard.
- `pages/`: Sub-pages for specific views (e.g., Predictions, Insights, "What-If" Analysis).
- `utils/`: Reusable Python modules and helper scripts that connect our ML logic to the Streamlit UI.

## How to Run
From the root of this folder, execute:
```bash
streamlit run Home.py
```

## Features
- **File Uploads**: Effortlessly upload data locally through the UI to generate predictions.
- **Dynamic State**: The app manages "No Data Loaded" states flawlessly—pages remain inactive until valid data is loaded.
- **Interactive Visualizations**: Leverages powerful Plotly charts for predictions and insights.
