# NRC Inspection Findings and Violations Analysis

## Project Overview
This project conducts an end-to-end Exploratory Data Analysis (EDA) on the NRC Inspection Findings and Violations dataset. The primary research goals are to identify seasonal trends in violations and to determine if a facility's history of minor infractions can predict the likelihood of future high-severity violations.

## Live Dashboard
Explore the interactive data dashboard here: **[Insert your Streamlit Cloud App URL here once deployed]**

## Repository Structure
* `cleaned_violations_data.csv`: The cleaned dataset used for the dashboard.
* `app.py`: Source code for the interactive Streamlit dashboard.
* `requirements.txt`: Dependencies required to run the dashboard.
* `notebooks/`: Jupyter notebooks containing the data cleaning, EDA, feature engineering, and predictive modeling.
* `presentation/`: Slides or link to the prerecorded presentation.
* `README.md`: Project documentation.

## Methodology
1. **Data Cleaning:** Filtered out anomalous dates (e.g., 1970 epoch parsing errors) and handled missing values. Created a binary `High_Severity` target variable mapping 'Green' findings to 0 and more severe findings to 1.
2. **Exploratory Data Analysis:** Visualized violation frequencies across months to assess seasonality and aggregated data to identify sites with the most severe violations.
3. **Feature Engineering:** Calculated `Minor_Infraction_History`, representing the cumulative count of prior minor ('Green') infractions for each site up to the date of a new violation.
4. **Predictive Modeling:** Trained a Logistic Regression model (with balanced class weights to handle imbalanced data) to predict high-severity violations based on infraction history and month.

## Key Findings
* **Seasonality:** Violation volumes fluctuate by month, with notable peaks in January, May, August, and November.
* **Site Severity:** A small subset of sites (e.g., Davis-Besse, Oconee, Kewaunee) account for a disproportionate number of historical high-severity violations.
* **Predictability:** A high accumulation of prior minor infractions is **not** a strong predictor of future high-severity violations. Major violations appear to be driven by acute failures or distinct operational circumstances rather than a gradual buildup of minor issues.

## How to Run Locally
1. Clone this repository: `git clone https://github.com/crawfoml/DataAnalyticsProj`
2. Install the required dependencies: `pip install -r requirements.txt`
3. Launch the Streamlit dashboard: [`streamlit run app.py`](https://dataanalyticsproj-yqsjjbacanxc9y2ezflz6a.streamlit.app/)

## Contributors
* Mitchell Crawford / Parker Roan
