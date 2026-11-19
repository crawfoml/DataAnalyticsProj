import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Set page layout to wide and add custom page title
st.set_page_config(
    page_title="NRC Inspection Findings Dashboard",
    page_icon="☢️",
    layout="wide"
)

# Title and Header
st.title("☢️ NRC Inspection Findings & Violations Explorer")
st.markdown("""
This interactive dashboard allows you to explore nuclear safety inspections, analyze regional trends,
and inspect the history of standard vs. high-severity violations.
""")

# Load the cleaned dataset
@st.cache_data
def load_data():
    # Use a relative path for GitHub / Streamlit Cloud deployment
    file_path = 'cleaned_violations_data.csv'

    import os
    if not os.path.exists(file_path):
        file_path = '/content/cleaned_violations_data.csv' # Fallback for Colab

    df = pd.read_csv(file_path)
    df['Issue Date'] = pd.to_datetime(df['Issue Date'])
    df['Year'] = df['Issue Date'].dt.year
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Could not load data. Error: {e}")
    st.stop()

# ==========================================
# SIDEBAR FILTERS
# ==========================================
st.sidebar.header("⚙️ Filter Controls")

# Region filter
all_regions = sorted(df['Region'].unique())
selected_regions = st.sidebar.multiselect("Select Region(s)", options=all_regions, default=all_regions)

# Cornerstone filter
all_cornerstones = sorted(df['Cornerstone'].unique())
selected_cornerstones = st.sidebar.multiselect("Select Cornerstone(s)", options=all_cornerstones, default=all_cornerstones)

# Year slider
min_year, max_year = int(df['Year'].min()), int(df['Year'].max())
selected_years = st.sidebar.slider("Select Year Range", min_value=min_year, max_value=max_year, value=(min_year, max_year))

# Filter the dataframe based on selections
filtered_df = df[
    (df['Region'].isin(selected_regions)) &
    (df['Cornerstone'].isin(selected_cornerstones)) &
    (df['Year'] >= selected_years[0]) &
    (df['Year'] <= selected_years[1])
]

# ==========================================
# KEY METRICS PANEL
# ==========================================
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Violations Filtered", f"{len(filtered_df):,}")
with col2:
    high_sev_count = filtered_df['High_Severity'].sum()
    st.metric("High-Severity Violations", f"{high_sev_count:,}", delta=f"{(high_sev_count/len(filtered_df)*100):.1f}% of total", delta_color="inverse")
with col3:
    top_site = filtered_df['Site Name'].mode().values[0] if not filtered_df.empty else "N/A"
    st.metric("Most Frequently Cited Site", top_site)
with col4:
    top_cornerstone = filtered_df['Cornerstone'].mode().values[0] if not filtered_df.empty else "N/A"
    st.metric("Primary Area of Concern", top_cornerstone)

st.markdown("---")

# ==========================================
# CHARTS SECTION
# ==========================================
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.subheader("📈 Annual Violation Trends")
    # Group by Year and Severity
    trend_df = filtered_df.groupby(['Year', 'High_Severity']).size().reset_index(name='Count')
    trend_df['Severity'] = trend_df['High_Severity'].map({0: 'Standard (Green)', 1: 'High Severity'})
    fig_trend = px.line(
        trend_df, x='Year', y='Count', color='Severity',
        title="Violations Over Time by Severity",
        color_discrete_map={'Standard (Green)': '#2ecc71', 'High Severity': '#e74c3c'},
        markers=True
    )
    st.plotly_chart(fig_trend, use_container_width=True)

with row1_col2:
    st.subheader("📊 Violations by Cornerstone Area")
    corner_df = filtered_df.groupby('Cornerstone').size().reset_index(name='Count').sort_values(by='Count', ascending=True)
    fig_corner = px.bar(
        corner_df, x='Count', y='Cornerstone', orientation='h',
        title="Violations Distribution by Cornerstone",
        color='Count', color_continuous_scale='Blues'
    )
    st.plotly_chart(fig_corner, use_container_width=True)

st.markdown("---")

row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.subheader("🎯 Site-by-Site Comparison (Top 15 Sites)")
    site_counts = filtered_df.groupby(['Site Name', 'High_Severity']).size().reset_index(name='Count')
    site_totals = filtered_df.groupby('Site Name').size().reset_index(name='Total')
    top_15_sites = site_totals.sort_values(by='Total', ascending=False).head(15)['Site Name']

    site_counts_filtered = site_counts[site_counts['Site Name'].isin(top_15_sites)]
    site_counts_filtered['Severity'] = site_counts_filtered['High_Severity'].map({0: 'Standard (Green)', 1: 'High Severity'})

    fig_site = px.bar(
        site_counts_filtered, x='Site Name', y='Count', color='Severity',
        title="Top Sites Count Breakdown (Stacked)",
        color_discrete_map={'Standard (Green)': '#2ecc71', 'High Severity': '#e74c3c'}
    )
    fig_site.update_layout(xaxis={'categoryorder':'total descending'})
    st.plotly_chart(fig_site, use_container_width=True)

with row2_col2:
    st.subheader("🗓️ Seasonal Heatmap")
    # Count by Month and Region
    season_df = filtered_df.groupby(['Month', 'Region']).size().reset_index(name='Count')
    season_pivot = season_df.pivot(index='Region', columns='Month', values='Count').fillna(0)
    # Map numeric months to names
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    season_pivot.columns = [month_names[m-1] for m in season_pivot.columns]

    fig_heat = px.imshow(
        season_pivot,
        labels=dict(x="Month", y="Region", color="Incidents"),
        x=season_pivot.columns,
        y=[f"Region {r}" for r in season_pivot.index],
        color_continuous_scale='Viridis',
        title="Incident Frequency Heatmap (Month vs Region)"
    )
    st.plotly_chart(fig_heat, use_container_width=True)

# ==========================================
# SEARCHABLE DATA VIEW
# ==========================================
st.markdown("---")
st.subheader("🔍 Filtered Findings Dataset Details")
show_cols = ['Issue Date', 'Site Name', 'Cornerstone', 'Significance', 'High_Severity', 'Minor_Infraction_History']
st.dataframe(filtered_df[show_cols], use_container_width=True)
