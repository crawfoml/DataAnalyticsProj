import inspect
import json

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from nrc_model import predict_rate, predict_severity, site_year_table, trailing_history

st.set_page_config(page_title="NRC findings: does history predict the future?", page_icon="☢️", layout="wide")

GREEN, RED, BLUE = "#2ecc71", "#e74c3c", "#4C72B0"

# Streamlit renamed use_container_width to width in newer versions, so pick whichever this version supports
_PLOTLY_HAS_WIDTH = "width" in inspect.signature(st.plotly_chart).parameters


def show(fig):
    if _PLOTLY_HAS_WIDTH:
        st.plotly_chart(fig, width="stretch")
    else:
        st.plotly_chart(fig, use_container_width=True)


def show_table(frame):
    try:
        st.dataframe(frame, width="stretch")
    except Exception:
        st.dataframe(frame, use_container_width=True)


@st.cache_data
def load_data():
    df = pd.read_csv("cleaned_violations_data.csv")
    df["Issue Date"] = pd.to_datetime(df["Issue Date"])
    df["Year"] = df["Issue Date"].dt.year
    return df


@st.cache_data
def load_model():
    with open("model_coefficients.json") as fh:
        return json.load(fh)


try:
    df = load_data()
    coefs = load_model()
except Exception as e:
    st.error(f"Could not load the data or the saved models. Error: {e}")
    st.stop()

meta = coefs["meta"]
last_full_year = meta["last_full_year"]
next_year = last_full_year + 1
as_of = pd.Timestamp(meta["latest_date"])

# ==========================================
# HEADER AND SITE PICKER
# ==========================================
st.title("NRC inspection findings: does a site's history predict its future?")
st.markdown(
    "Can a nuclear site's violation history help predict its future **incident rate** (how many findings it gets) "
    "and the **severity** of its findings? The tabs below answer each half and let you try it on any site."
)

sites = sorted(df["Site Name"].unique())
site = st.sidebar.selectbox("Site", sites, index=sites.index("Davis-Besse") if "Davis-Besse" in sites else 0)
st.sidebar.caption("The site picker drives the Site history and Severity risk tabs.")

tab_q, tab_site, tab_risk, tab_explore = st.tabs(["The question", "Site history", "Severity risk", "Explore findings"])

# ==========================================
# TAB 1. THE QUESTION
# ==========================================
with tab_q:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Findings", f"{len(df):,}")
    c2.metric("Sites", df["Site Name"].nunique())
    c3.metric("High-severity share", f"{df['High_Severity'].mean():.1%}")
    c4.metric("Period", f"{df['Issue Date'].min():%b %Y} to {df['Issue Date'].max():%b %Y}")

    left, right = st.columns(2)
    with left:
        st.subheader("How many findings? Yes, history predicts it.")
        st.write(
            f"Each finding a site had last year predicts {coefs['rate']['findings_lag1']:.2f} more this year, and each "
            f"finding two years ago predicts {coefs['rate']['findings_lag2']:.2f} more. On years the model never saw "
            f"(2018 onward), it is off by {meta['rate_out_of_time_mae']:.1f} findings per site per year on average."
        )
    with right:
        st.subheader("How serious? Only weakly.")
        st.write(
            f"A site's recent serious findings raise the odds of another, but the full model ranks findings only a "
            f"little better than chance (out-of-time ROC AUC {meta['severity_out_of_time_auc']:.2f}, where 0.50 is a coin flip). "
            "Serious findings seem to come from specific failures, not from a pile of minor ones."
        )

    yearly = (df[(df["Year"] >= 2001) & (df["Year"] <= last_full_year)]
              .groupby("Year").agg(findings=("High_Severity", "size"), share=("High_Severity", "mean")).reset_index())
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_bar(x=yearly["Year"], y=yearly["findings"], name="Findings", marker_color=BLUE, secondary_y=False)
    fig.add_scatter(x=yearly["Year"], y=yearly["share"] * 100, name="% high-severity", mode="lines+markers",
                    line_color=RED, secondary_y=True)
    fig.update_yaxes(title_text="Findings per year", secondary_y=False)
    fig.update_yaxes(title_text="% of findings high-severity", secondary_y=True)
    fig.update_layout(title="Findings per year and the high-severity share", xaxis_title="Year issued",
                      legend=dict(orientation="h", y=-0.2))
    show(fig)
    st.caption(
        "The dashboard fits no models. It reads the coefficients saved by data_analytics_final_proj.ipynb "
        "(model_coefficients.json), so every prediction here matches the notebook."
    )

# ==========================================
# TAB 2. SITE HISTORY (INCIDENT RATE)
# ==========================================
with tab_site:
    st.subheader(f"{site}: findings per year and the model's one-year-ahead prediction")
    full_table = site_year_table(df, site, last_full_year)
    region = int(df.loc[df["Site Name"] == site, "Region"].iloc[0])
    last_finding_year = int(df.loc[df["Site Name"] == site, "Year"].max())
    active = last_finding_year >= last_full_year

    # A site with no recent findings has shut down, so the chart stops at its last year with findings
    table = (full_table if active else full_table[full_table["Year"] <= last_finding_year]).reset_index(drop=True)
    table["standard"] = table["findings"] - table["high"]

    preds = {}
    for i in range(2, len(table)):
        year = int(table.loc[i, "Year"])
        preds[year] = predict_rate(coefs, region, year, table.loc[i - 1, "findings"],
                                   table.loc[i - 2, "findings"], table.loc[i - 1, "high"])
    if active and len(table) >= 2:
        forecast = predict_rate(coefs, region, next_year, table.iloc[-1]["findings"],
                                table.iloc[-2]["findings"], table.iloc[-1]["high"])
    else:
        forecast = None

    fig = go.Figure()
    fig.add_bar(x=table["Year"], y=table["standard"], name="Standard (Green)", marker_color=GREEN)
    fig.add_bar(x=table["Year"], y=table["high"], name="High severity", marker_color=RED)
    if preds:
        fig.add_scatter(x=list(preds), y=list(preds.values()), mode="lines+markers", name="Predicted from the two prior years",
                        line=dict(color="black", dash="dot"))
    if forecast is not None:
        fig.add_scatter(x=[next_year], y=[forecast], mode="markers", name=f"Expected in {next_year}",
                        marker=dict(color="black", size=14, symbol="diamond"))
    fig.update_layout(barmode="stack", xaxis_title="Year issued", yaxis_title="Findings",
                      legend=dict(orientation="h", y=-0.25), margin=dict(t=20))
    show(fig)

    m1, m2, m3 = st.columns(3)
    m1.metric(f"Findings in {last_full_year}", int(full_table.iloc[-1]["findings"]))
    if forecast is not None:
        m2.metric(f"Expected in {next_year} (full year)", f"{forecast:.0f}")
        m2.caption(f"Typical error about {meta['rate_out_of_time_mae']:.0f} findings")
    else:
        m2.metric(f"Expected in {next_year}", "n/a")
    ytd = int(((df["Site Name"] == site) & (df["Year"] == next_year)).sum())
    m3.metric(f"{next_year} so far (to {as_of:%b %d})", ytd)

    if not active:
        st.warning(f"{site} has no findings after {last_finding_year}, so it may have shut down. "
                   "The forecast does not apply.")
    st.caption(
        "The prediction uses the site's findings in the two prior years, its NRC region, and a time trend. It tracks which "
        "sites get more findings, but it cannot foresee national shifts, such as the drop after 2017."
    )

# ==========================================
# TAB 3. SEVERITY RISK
# ==========================================
with tab_risk:
    st.subheader("How likely is a new finding to be high-severity?")
    st.write(
        f"Start from {site}'s own history as of {as_of:%b %d, %Y} (the sliders are pre-filled), then change anything "
        "to see how the odds move."
    )
    hist = trailing_history(df, site, as_of, meta["window_days"])
    region = int(df.loc[df["Site Name"] == site, "Region"].iloc[0])

    inputs, results = st.columns([1, 1.3])
    with inputs:
        corner = st.selectbox("Cornerstone (safety area)", sorted(df["Cornerstone"].unique()),
                              index=sorted(df["Cornerstone"].unique()).index(meta["reference"]["cornerstone"]))
        source = st.radio("Who identified it?", ["NRC - Identified", "Self - Revealed"], horizontal=True)
        minor = st.slider("Minor findings at the site, prior 24 months", 0, max(150, hist["minor_24m"]),
                          hist["minor_24m"], key=f"minor_{site}")
        high = st.slider("High-severity findings at the site, prior 24 months", 0, max(15, hist["high_24m"]),
                         hist["high_24m"], key=f"high_{site}")
        hp = st.slider("Human-performance findings, prior 24 months", 0, max(40, hist["hp_24m"]),
                       hist["hp_24m"], key=f"hp_{site}")
        pi = st.slider("Problem-identification findings, prior 24 months", 0, max(15, hist["pi_24m"]),
                       hist["pi_24m"], key=f"pi_{site}")
        st.caption(f"{site} is in NRC Region {region}.")

    def risk(corner_name):
        return predict_severity(coefs, corner_name, source == "Self - Revealed", region, next_year, minor, hp, pi, high)

    p = risk(corner)
    base = meta["severity_base_rate"]
    with results:
        st.metric("Chance this finding is high-severity", f"{p:.1%}",
                  delta=f"{p / base - 1:+.0%} vs the {base:.1%} average", delta_color="inverse")
        by_corner = pd.DataFrame({"Cornerstone": sorted(df["Cornerstone"].unique())})
        by_corner["Chance"] = by_corner["Cornerstone"].map(risk) * 100
        by_corner = by_corner.sort_values("Chance")
        fig = px.bar(by_corner, x="Chance", y="Cornerstone", orientation="h",
                     title="Same history and source, by cornerstone",
                     labels={"Chance": "Chance of high severity (%)"})
        fig.update_traces(marker_color=[RED if c == corner else BLUE for c in by_corner["Cornerstone"]])
        show(fig)
    st.caption(
        f"This model ranks findings only modestly (out-of-time ROC AUC {meta['severity_out_of_time_auc']:.2f}). Use it to see which "
        "factors matter, not to predict an individual finding. It shows association, not cause."
    )

# ==========================================
# TAB 4. EXPLORE FINDINGS
# ==========================================
with tab_explore:
    f1, f2, f3 = st.columns(3)
    all_regions = sorted(df["Region"].unique())
    selected_regions = f1.multiselect("Region(s)", all_regions, default=all_regions)
    all_cornerstones = sorted(df["Cornerstone"].unique())
    selected_cornerstones = f2.multiselect("Cornerstone(s)", all_cornerstones, default=all_cornerstones)
    min_year, max_year = int(df["Year"].min()), int(df["Year"].max())
    selected_years = f3.slider("Year range", min_year, max_year, (min_year, max_year))

    filtered_df = df[df["Region"].isin(selected_regions) & df["Cornerstone"].isin(selected_cornerstones)
                     & df["Year"].between(*selected_years)]

    if filtered_df.empty:
        st.info("No findings match these filters.")
    else:
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Findings", f"{len(filtered_df):,}")
        high_count = int(filtered_df["High_Severity"].sum())
        k2.metric(f"High-severity findings ({high_count / len(filtered_df):.1%})", f"{high_count:,}")
        k3.metric("Most-cited site", filtered_df["Site Name"].mode().iloc[0])
        k4.metric("Most-cited cornerstone", filtered_df["Cornerstone"].mode().iloc[0])

        label = {0: "Standard (Green)", 1: "High Severity"}
        colors = {"Standard (Green)": GREEN, "High Severity": RED}
        a, b = st.columns(2)
        with a:
            trend = filtered_df.groupby(["Year", "High_Severity"]).size().reset_index(name="Count")
            trend["Severity"] = trend["High_Severity"].map(label)
            show(px.line(trend, x="Year", y="Count", color="Severity", markers=True,
                                    title="Findings over time by severity", color_discrete_map=colors))
        with b:
            corner_df = filtered_df.groupby("Cornerstone").size().reset_index(name="Count").sort_values("Count")
            show(px.bar(corner_df, x="Count", y="Cornerstone", orientation="h",
                                   title="Findings by cornerstone", color="Count", color_continuous_scale="Blues"))

        c, d = st.columns(2)
        with c:
            top_sites = filtered_df["Site Name"].value_counts().head(15).index
            site_counts = (filtered_df[filtered_df["Site Name"].isin(top_sites)]
                           .groupby(["Site Name", "High_Severity"]).size().reset_index(name="Count"))
            site_counts["Severity"] = site_counts["High_Severity"].map(label)
            fig = px.bar(site_counts, x="Site Name", y="Count", color="Severity", color_discrete_map=colors,
                         title="Top 15 sites by findings (stacked)")
            fig.update_layout(xaxis={"categoryorder": "total descending"})
            show(fig)
        with d:
            season = filtered_df.groupby(["Month", "Region"]).size().reset_index(name="Count")
            pivot = season.pivot(index="Region", columns="Month", values="Count").fillna(0)
            names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            pivot.columns = [names[m - 1] for m in pivot.columns]
            show(px.imshow(pivot, labels=dict(x="Month", y="Region", color="Findings"),
                                      x=list(pivot.columns), y=[f"Region {r}" for r in pivot.index],
                                      color_continuous_scale="Viridis", title="Findings by month and region"))

        st.subheader("Findings in the current filter")
        table_view = filtered_df[["Issue Date", "Site Name", "Cornerstone", "Significance", "High_Severity",
                                  "Minor_Infraction_History"]].copy()
        table_view["Issue Date"] = table_view["Issue Date"].dt.date
        show_table(table_view)
