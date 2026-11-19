import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="NRC Violations Dashboard", page_icon="☢️", layout="wide")

# --- DATA LOADING ---
@st.cache_data
def load_data():
    # Get the directory where this script is saved to ensure we look in the right place
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, 'cleaned_violations_data.csv')

    # Load the exported CSV
    df = pd.read_csv(csv_path)
    # Ensure dates are datetime objects
    df['Issue Date'] = pd.to_datetime(df['Issue Date'])
    return df

try:
    data = load_data()
except FileNotFoundError:
    st.error("⚠️ 'cleaned_violations_data.csv' not found. Please ensure it is in the same folder as this app.")
    st.stop()

# --- SIDEBAR & FILTERS ---
st.sidebar.title("☢️ Navigation & Filters")
st.sidebar.info("Explore the NRC Inspection Findings dataset to understand safety violations, seasonality, and predictability.")

# Year filter
min_year = int(data['Year'].min())
max_year = int(data['Year'].max())
selected_years = st.sidebar.slider("Select Year Range", min_year, max_year, (min_year, max_year))

# Apply filter
filtered_data = data[(data['Year'] >= selected_years[0]) & (data['Year'] <= selected_years[1])]

# --- MAIN HEADER ---
st.title("NRC Inspection Findings & Violations")
st.markdown("An interactive dashboard exploring temporal trends and predicting high-severity safety violations at nuclear facilities.")

# --- KPI METRICS ---
col1, col2, col3, col4 = st.columns(4)
total_violations = len(filtered_data)
high_severity_count = filtered_data['High_Severity'].sum()
unique_sites = filtered_data['Site Name'].nunique()
severe_rate = (high_severity_count / total_violations) * 100 if total_violations > 0 else 0

col1.metric("Total Violations", f"{total_violations:,}")
col2.metric("High Severity Violations", f"{high_severity_count:,}")
col3.metric("Severe Incident Rate", f"{severe_rate:.2f}%")
col4.metric("Facilities Tracked", f"{unique_sites:,}")

st.markdown("---")

# --- TABS FOR ORGANIZATION ---
tab1, tab2, tab3 = st.tabs(["📊 Temporal Trends (Seasonality)", "🏢 Site Severity Analysis", "🔮 Predictive Insights"])

with tab1:
    st.header("Seasonality: When do violations occur?")

    # Group by month
    monthly_counts = filtered_data.groupby('Month').size().reset_index(name='Count')
    month_names = {1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'May',6:'Jun',
                   7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec'}
    monthly_counts['Month Name'] = monthly_counts['Month'].map(month_names)

    # Plotly Interactive Bar Chart
    fig_month = px.bar(monthly_counts, x='Month Name', y='Count',
                       color='Count', color_continuous_scale='Viridis',
                       labels={'Month Name': 'Month', 'Count': 'Number of Violations'})
    st.plotly_chart(fig_month, use_container_width=True)

    st.info("💡 **Key Finding:** Noticeable peaks occur in **January, May, August, and November**. This corresponds to the spring and fall refueling outage windows that take place during the mild months to maximize power available during cold winters and hot summers.")

with tab2:
    st.header("Which sites have the most severe violations?")

    # Group by site
    site_severity = filtered_data.groupby('Site Name')['High_Severity'].sum().reset_index()
    site_severity = site_severity.sort_values(by='High_Severity', ascending=False).head(15)

    # Plotly Interactive Horizontal Bar Chart
    fig_site = px.bar(site_severity, x='High_Severity', y='Site Name', orientation='h',
                      color='High_Severity', color_continuous_scale='Reds',
                      labels={'High_Severity': 'High-Severity Violation Count', 'Site Name': 'Facility'})
    fig_site.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_site, use_container_width=True)

    st.warning("⚠️ **Observation:** A small subset of sites (e.g., Davis-Besse, Oconee) account for a disproportionate number of historical high-severity violations.")

with tab3:
    st.header("Does a history of minor infractions predict major ones?")

    # Make a copy for visualization mapping
    viz_data = filtered_data.copy()
    viz_data['Severity Level'] = viz_data['High_Severity'].map({0: 'Standard (Green)', 1: 'High Severity'})

    # Plotly Interactive Box Plot
    fig_box = px.box(viz_data, x='Severity Level', y='Minor_Infraction_History',
                     color='Severity Level', color_discrete_map={'Standard (Green)': '#66c2a5', 'High Severity': '#fc8d62'},
                     labels={'Minor_Infraction_History': 'Cumulative Prior Minor Infractions'})

    st.plotly_chart(fig_box, use_container_width=True)

    st.success("🎯 **Conclusion:** Our predictive modeling revealed that a **high accumulation of prior minor infractions is NOT a strong predictor of future high-severity violations**. In fact, standard violations had slightly higher historical averages of minor infractions compared to high-severity incidents. Major violations appear to be driven by acute failures rather than a gradual buildup.")

# --- FOOTER ---
st.markdown("---")
st.markdown("<div style='text-align: center; color: grey;'>Created by Mitchell Crawford & Parker Roan | Auburn University Final Project</div>", unsafe_allow_html=True)
