# Data Directory

This folder holds all project data, including raw datasets, cleaning outputs, generated features, and cached metrics. 

## Contents
- **Raw Data (`*.xlsx` / `*.csv`)**: Baseline tracking spreadsheets (Ignored by git unless specified).
- **Extracted Features (`selected_features.csv`, `model_features.json`)**: Feature lists used by our pipeline to run inferences.
- **Metrics (`model_metrics.json`)**: Pre-calculated metrics consumed by the dashboard for visualization.

## Note on Version Control
*Most large data files (.csv, .xlsx, .pkl) are ignored via `.gitignore` to keep the repository lightweight.* Do not commit large datasets to version control. Let the local data pipelines generate them on-device instead whenever possible.
