# NRC inspection findings and violations analysis

## Project overview
This project is an end-to-end exploratory data analysis (EDA) of the NRC Inspection Findings and Violations dataset. It asks one question: **can a nuclear site's violation history help predict its future incident rate and the severity of its findings?**

**Short answer.** Yes for how many findings a site gets, and only weakly for how serious they are.

## Live dashboard
Explore the interactive dashboard here: **[Insert your Streamlit Cloud App URL here once deployed]**

The dashboard has four tabs. **The question** gives the answer and the national trend. **Site history** shows any site's findings per year next to the model's one-year-ahead prediction. **Severity risk** estimates the chance that a new finding is high-severity, starting from the chosen site's own recent history. **Explore findings** has the filterable charts and data table. The dashboard fits no models. It reads the coefficients the notebook saves, so its numbers match the analysis.

## Repository structure
* `DataAnalyticsFinalProj.ipynb` is the full analysis. Its sections follow the project document outline (introduction, dataset and quality, cleaning, visualizations and findings, conclusions, references). It also writes `cleaned_violations_data.csv` and `model_coefficients.json`.
* `cleaned_violations_data.csv` is the cleaned finding-level dataset that the dashboard reads.
* `model_coefficients.json` holds the fitted model coefficients that the dashboard reads.
* `app.py` is the Streamlit dashboard, and `nrc_model.py` holds the prediction functions it shares with the notebook. The notebook checks them against statsmodels.
* `raw-findings-violations-dataset.xlsx` is the raw NRC export, and `findings-violations-data-dictionary.xlsx` is the NRC's field list.
* `requirements.txt` lists the packages the dashboard needs. `requirements-analysis.txt` adds the packages the notebook needs.

## Methodology
1. **Cleaning.** 819 rows stored `Issue Date` as an Excel serial number, which a plain date parse reads as 1970. We convert them to their real dates (July 1999 to May 2001) instead of dropping them, so the dataset keeps all 18,240 findings. We also fill missing site codes and create a binary `High_Severity` target (Green = 0; White, Yellow, Red, or Greater Than Green = 1).
2. **History features.** For each finding, we count the same site's minor, high-severity, human-performance, and problem-identification findings in the previous 730 days. For each site-year, we use the finding counts from the previous one and two years.
3. **Multicollinearity.** The 730-day total equals minor plus high-severity exactly, so we drop it. Raw `Year` and `Year²` have a VIF above 600,000, so we center year before squaring it.
4. **Incident rate.** Linear and polynomial regression predicts each site's findings per year from its recent counts, NRC region, and year. Standard errors are clustered by site.
5. **Severity.** Nested logistic regression models predict `High_Severity` from cornerstone, year, identification source, region, and recent history.
6. **Validation.** Every model trains on years through 2017 and is tested on 2018 to 2024.

## Key findings
* **History predicts incident rate.** Each additional finding last year predicts 0.38 more this year, and adding the previous two years' counts raises adjusted R² from 0.24 to 0.43. On 2018 to 2024, the average error drops from 6.8 to 3.8 findings per site-year. No model predicts the national drop in findings after 2017.
* **History only weakly predicts severity.** All-time minor history does no better than chance (ROC AUC 0.55). Recent serious findings are the strongest signal, since each one raises the odds of another by 21%. The full model reaches only ROC AUC 0.64 on 2018 to 2024.
* **Safety area matters.** Emergency Preparedness findings (25.0% high-severity) and Security findings (10.2%) are far more likely to be serious than the rest.
* **Identification source is a confounder.** Self-revealed findings look less serious on their own (odds ratio 0.59). The gap disappears once the model controls for cornerstone (0.90), because NRC inspectors find more Security and Emergency Preparedness issues.
* **Regions differ.** Region 2 has 1.80 times the odds of a high-severity finding compared with Region 1, yet it receives the fewest findings. Region 4 receives the most. The data cannot tell whether that reflects stricter enforcement or different plant risk.
* **Seasonality and sites.** Findings peak in February, May, August, and November. Davis-Besse, Oconee, and Kewaunee have the most high-severity findings.

## How to run locally
1. Clone this repository: `git clone https://github.com/crawfoml/DataAnalyticsProj`
2. Create and activate a virtual environment: `python3 -m venv .venv && source .venv/bin/activate`
3. Install the dashboard's packages with `pip install -r requirements.txt`, or use `pip install -r requirements-analysis.txt` to also run the notebook.
4. Launch the Streamlit dashboard: [`streamlit run app.py`](https://dataanalyticsproj-yqsjjbacanxc9y2ezflz6a.streamlit.app/)
5. Open the notebook with `jupyter lab DataAnalyticsFinalProj.ipynb`. It reads the raw xlsx from the repository root. In Google Colab, upload the xlsx first.

## Contributors
* Mitchell Crawford / Parker Roan
