# FuelIQ - Petrol Pump Refuel Predictor

Welcome to the **FuelIQ** repository! This project predicts fuel requirements for petrol pumps using machine learning and provides an interactive dashboard for simulations and what-if analysis.

## Repository Structure

- `/Frontend`: Contains the Streamlit web application.
- `/data`: Datasets, features, and model metrics used in the ML pipelines.
- `/notebooks`: Exploratory data analysis (EDA) and experimental ML notebooks.

## Quick Start

1. **Setup Environment:**
   Make sure you have your Python environment activated with all required dependencies installed (`pip install -r requirements.txt`).

2. **Run the Dashboard:**
   To start the web application interface, navigate into the `Frontend` folder and run Streamlit:
   ```bash
   cd Frontend
   streamlit run Home.py
   ```

## Workflow
1. Use the exploratory notebooks in `/notebooks` for model changes.
2. Put generated data or datasets in the `/data` folder.
3. Access the predictions through the Streamlit dashboard in `/Frontend`.
