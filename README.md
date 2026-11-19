# NRC Inspection Findings and Violations Analysis

## Project Overview

This project conducts an end-to-end Exploratory Data Analysis (EDA) on the NRC Inspection Findings and Violations dataset. The primary research goals are to identify seasonal trends in violations and to determine if a facility's history of minor infractions can predict the likelihood of future high-severity violations.

## Repository Structure

- `data/`: Contains the raw and cleaned datasets (e.g., `cleaned_violations_data.csv`).
- `notebooks/`: Jupyter notebooks containing the data cleaning, EDA, feature engineering, and predictive modeling.
- `dashboard/`: Source code for the interactive Streamlit dashboard.
- `presentation/`: Slides or link to the prerecorded presentation.
- `README.md`: Project documentation.

## Methodology

- **Data Cleaning:** Filtered out anomalous dates (e.g., 1970 epoch parsing errors) and handled missing values. Created a binary `High_Severity` target variable mapping 'Green' findings to 0 and more severe findings to 1.
- **Exploratory Data Analysis:** Visualized violation frequencies across months to assess seasonality and aggregated data to identify sites with the most severe violations.
- **Feature Engineering:** Calculated `Minor_Infraction_History`, representing the cumulative count of prior minor ('Green') infractions for each site up to the date of a new violation.
- **Predictive Modeling:** Trained a Logistic Regression model (with balanced class weights to handle imbalanced data) to predict high-severity violations based on infraction history and month.

## Key Findings

- **Seasonality:** Violation volumes fluctuate by month, with notable peaks in January, May, August, and November.
- **Site Severity:** A small subset of sites (e.g., Davis-Besse, Oconee, Kewaunee) account for a disproportionate number of historical high-severity violations.
- **Predictability:** A high accumulation of prior minor infractions is not a strong predictor of future high-severity violations. Major violations appear to be driven by acute failures or distinct operational circumstances rather than a gradual buildup of minor issues.

## How to Run

1. Clone this repository: `git clone [repository-url]`
2. Install the required dependencies: `pip install pandas matplotlib seaborn scikit-learn streamlit`
3. Run the Jupyter notebook to view the core analysis.
4. Launch the Streamlit dashboard: `streamlit run dashboard/app.py`

## Contributors

Mitchell Crawford and Parker Roan
