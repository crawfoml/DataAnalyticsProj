"""Prediction helpers shared by the Streamlit dashboard and the notebook.

The notebook fits the models and saves their coefficients to model_coefficients.json. These functions turn
those coefficients into predictions, and the notebook checks them against statsmodels so the dashboard
cannot drift from the analysis.
"""
import math

import pandas as pd


def predict_rate(coefs, region, year, findings_lag1, findings_lag2, high_lag1):
    """Expected findings for a site in `year`, from model R2 (linear regression)."""
    meta, rate = coefs["meta"], coefs["rate"]
    return (rate["intercept"]
            + rate["region"].get(str(region), 0.0)
            + rate["year_c"] * (year - meta["year_center"])
            + rate["findings_lag1"] * findings_lag1
            + rate["findings_lag2"] * findings_lag2
            + rate["high_lag1"] * high_lag1)


def predict_severity(coefs, cornerstone, self_revealed, region, year, minor_24m, hp_24m, pi_24m, high_24m):
    """Probability that a finding is high-severity, from model M2 (logistic regression)."""
    meta, sev = coefs["meta"], coefs["severity"]
    z = (sev["intercept"]
         + sev["cornerstone"].get(cornerstone, 0.0)
         + (sev["idby_self_revealed"] if self_revealed else 0.0)
         + sev["region"].get(str(region), 0.0)
         + sev["year_c"] * (year - meta["year_center"])
         + sev["minor_24m"] * minor_24m
         + sev["minor_24m_sq"] * minor_24m ** 2
         + sev["hp_24m"] * hp_24m
         + sev["pi_24m"] * pi_24m
         + sev["high_24m"] * high_24m)
    return 1.0 / (1.0 + math.exp(-z))


def trailing_history(df, site, as_of, window_days):
    """A site's findings in the `window_days` up to `as_of`, in the form model M2 expects."""
    recent = df[(df["Site Name"] == site)
                & (df["Issue Date"] >= as_of - pd.Timedelta(days=window_days))
                & (df["Issue Date"] <= as_of)]
    return {
        "minor_24m": int((recent["Significance"] == "Green").sum()),
        "high_24m": int(recent["High_Severity"].sum()),
        "hp_24m": int((recent["CrossCutting Area"] == "H").sum()),
        "pi_24m": int((recent["CrossCutting Area"] == "P").sum()),
    }


def site_year_table(df, site, last_full_year):
    """Findings and high-severity findings per year for one site, with zero-finding years included."""
    rows = df[df["Site Name"] == site]
    years = range(int(rows["Year"].min()), last_full_year + 1)
    counts = rows.groupby("Year").agg(findings=("High_Severity", "size"), high=("High_Severity", "sum"))
    return counts.reindex(years, fill_value=0).rename_axis("Year").reset_index()
